from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import logging
import os
import re
import time
from io import BytesIO
from datetime import datetime, timedelta, timezone
from html import escape as html_escape
from html import unescape as html_unescape
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode, urljoin
from xml.etree import ElementTree as ET

import httpx
from PIL import Image, ImageDraw, ImageFont

from quantamind import config
from quantamind.server import knowledge_base, memory, state_store

_log = logging.getLogger("quantamind.arxiv_intel")

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_SEARCH_URL = "https://arxiv.org/search/"
ARXIV_RSS_FEEDS = [
    "https://rss.arxiv.org/rss/quant-ph",
    "https://rss.arxiv.org/rss/cond-mat.supr-con",
    "https://rss.arxiv.org/rss/eess.SP",
    "https://rss.arxiv.org/rss/cs.AI",
    "https://rss.arxiv.org/rss/cs.LG",
]
SCIRATE_BASE_URL = "https://scirate.com"
# 与 ARXIV_RSS_FEEDS 对应的 arXiv 分区路径（SciRate 列表页）
SCIRATE_ARXIV_CATEGORIES = [
    "quant-ph",
    "cond-mat.supr-con",
    "eess.SP",
    "cs.AI",
    "cs.LG",
]
ARXIV_SEARCH_TERMS = [
    "superconducting qubit",
    "transmon",
    "surface code",
    "quantum control",
    "quantum chip",
    "large language model",
    "AI agent",
    "multi-agent",
    "agentic workflow",
]
CROSSREF_API_URL = "https://api.crossref.org/works"
OPENALEX_API_URL = "https://api.openalex.org/works"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
DC_NS_URI = "http://purl.org/dc/elements/1.1/"

_INTEL_BACKEND_RANK = {
    "live-api": 40,
    "live-search-html": 30,
    "live-openalex": 25,
    "live-crossref": 25,
    "live-scirate": 18,
    "live-rss": 10,
    "cache": 5,
    "": 0,
}

# 情报「技术路线图」节点与画布（SVG / PNG 保持一致）
_ROUTE_GRAPH_CANVAS_W = 1280
_ROUTE_GRAPH_NODE_W = 220
_ROUTE_GRAPH_NODE_H = 400
_ROUTE_GRAPH_NODE_GAP = 22
_ROUTE_GRAPH_NODES_X0 = 40
_ROUTE_GRAPH_NODES_Y = 158
_ROUTE_GRAPH_METHOD_GAP = 18


def _route_graph_content_bottom_y(route_graph: Dict[str, Any]) -> int:
    """白底卡片内，技术路线内容（节点行 + 可选方法图条）占用的最底 y。"""
    y = _ROUTE_GRAPH_NODES_Y + _ROUTE_GRAPH_NODE_H
    mf = route_graph.get("method_figure") or {}
    if (mf.get("caption") or "").strip() or (mf.get("image_url") or "").strip():
        return y + _ROUTE_GRAPH_METHOD_GAP + 52
    return y


def _route_graph_inner_and_canvas(route_graph: Dict[str, Any]) -> tuple[int, int]:
    """(inner_h, canvas_h)，收紧无方法图时的下方留白。"""
    bottom = _route_graph_content_bottom_y(route_graph)
    inner_h = bottom - 20 + 36
    inner_h = max(inner_h, 440)
    return inner_h, 20 + inner_h + 20

SEARCH_BASE_QUERY = (
    '((cat:quant-ph OR cat:cond-mat.supr-con OR cat:eess.SP OR cat:cs.AI OR cat:cs.LG) AND '
    '(all:quantum OR all:qubit OR all:superconducting OR all:transmon OR all:"surface code" '
    'OR all:"error correction" OR all:"quantum control" OR all:"quantum chip" '
    'OR all:"quantum processor" OR all:"machine learning" OR all:"large language model" '
    'OR all:"AI agent" OR all:"multi-agent" OR all:agentic OR all:"tool use")))'
)

TOPIC_QUERIES: List[Dict[str, str]] = [
    {
        "id": "chip_design",
        "label": "量子芯片设计",
        "query": '(all:"quantum chip design" OR all:transmon OR all:"superconducting qubit design" '
                 'OR all:"quantum processor layout" OR all:coupler OR all:resonator OR all:"quantum processor architecture")',
    },
    {
        "id": "chip_fabrication",
        "label": "量子芯片生产",
        "query": '(all:"quantum chip fabrication" OR all:"superconducting qubit fabrication" '
                 'OR all:"Josephson junction fabrication" OR all:wafer OR all:etch OR all:deposition OR all:lithography)',
    },
    {
        "id": "measurement_control",
        "label": "量子测控",
        "query": '(all:"quantum control" OR all:"qubit readout" OR all:"quantum measurement" '
                 'OR all:"pulse calibration" OR all:ramsey OR all:rabi OR all:"readout fidelity")',
    },
    {
        "id": "quantum_computing",
        "label": "量子计算",
        "query": '(all:"quantum computing" OR all:"quantum circuit" OR all:"quantum compiler" '
                 'OR all:"quantum processor" OR all:"quantum architecture")',
    },
    {
        "id": "quantum_error_correction",
        "label": "量子纠错",
        "query": '(all:"quantum error correction" OR all:"surface code" OR all:"fault-tolerant quantum computing" '
                 'OR all:"logical qubit" OR all:"decoder")',
    },
    {
        "id": "ai_for_quantum",
        "label": "AI赋能量子",
        "query": '(all:"machine learning for quantum" OR all:"AI for quantum" OR all:"foundation model quantum" '
                 'OR all:"neural" OR all:"learning-based" OR all:"surrogate model")',
    },
    {
        "id": "ai_agents",
        "label": "AI/智能体",
        "query": '(all:"large language model" OR all:llm OR all:"AI agent" OR all:"multi-agent" '
                 'OR all:agentic OR all:"tool use" OR all:"reasoning model" OR all:"workflow agent")',
    },
    {
        "id": "quantum_application",
        "label": "量子应用",
        "query": '(all:"quantum application" OR all:"quantum chemistry" OR all:"quantum optimization" '
                 'OR all:"quantum sensing" OR all:"quantum simulation")',
    },
]

TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "chip_design": ["transmon", "layout", "coupler", "resonator", "chip design", "superconducting qubit", "processor architecture", "frequency allocation"],
    "chip_fabrication": ["fabrication", "junction", "josephson", "wafer", "deposition", "etch", "lithography", "yield"],
    "measurement_control": ["readout", "pulse", "quantum measurement", "calibration", "ramsey", "rabi", "fidelity", "microwave"],
    "quantum_computing": ["quantum computing", "quantum circuit", "quantum compiler", "quantum processor", "quantum architecture", "benchmark"],
    "quantum_error_correction": ["error correction", "surface code", "fault-tolerant", "logical qubit", "decoder", "stabilizer"],
    "ai_for_quantum": ["machine learning for quantum", "ai for quantum", "quantum machine learning", "foundation model quantum", "learning-based", "surrogate model"],
    "ai_agents": ["large language model", "llm", "agent", "ai agent", "multi-agent", "agentic", "tool use", "reasoning model", "workflow"],
    "quantum_application": ["quantum chemistry", "quantum optimization", "quantum sensing", "quantum simulation", "variational quantum", "hamiltonian"],
}
NEGATIVE_NOISE_TERMS = [
    "antenna",
    "wireless communication",
    "wireless communications",
    "fluid antenna",
    "throughput maximization",
    "campus accessibility",
    "customer interaction",
    "pandemic",
    "covid",
    "zika",
    "monkeypox",
    "economic indicators",
]

TOPIC_LABELS = {item["id"]: item["label"] for item in TOPIC_QUERIES}
FORMAL_TRACK_RULES: Dict[str, Dict[str, Any]] = {
    "ai_agents": {
        "label": "AI/智能体",
        "title_cn": "QuantaMind AI/智能体日报",
        "title_en": "QuantaMind AI Agents Daily Brief",
        "topic_ids": {"ai_agents", "ai_for_quantum"},
        "required_terms": ["agent", "multi-agent", "agentic", "tool use", "memory", "workflow", "llm", "large language model"],
        "boost_terms": ["planner", "reasoning", "code generation", "benchmark", "evaluation", "orchestration"],
    },
    "chip_design": {
        "label": "芯片设计",
        "title_cn": "QuantaMind 芯片设计日报",
        "title_en": "QuantaMind Chip Design Daily Brief",
        "topic_ids": {"chip_design", "chip_fabrication", "quantum_computing"},
        "required_terms": ["superconducting", "transmon", "coupler", "resonator", "layout", "chip", "processor architecture"],
        "boost_terms": ["josephson", "fabrication", "wafer", "lithography", "cavity-based", "multiqudit"],
    },
    "quantum_error_correction": {
        "label": "量子纠错",
        "title_cn": "QuantaMind 量子纠错日报",
        "title_en": "QuantaMind Quantum Error Correction Daily Brief",
        "topic_ids": {"quantum_error_correction", "quantum_computing"},
        "required_terms": ["surface code", "fault-tolerant", "logical qubit", "decoder", "stabilizer", "error correction"],
        "boost_terms": ["threshold", "syndrome", "logical", "qec", "distance"],
    },
    "quantum_computing": {
        "label": "量子计算",
        "title_cn": "QuantaMind 量子计算日报",
        "title_en": "QuantaMind Quantum Computing Daily Brief",
        "topic_ids": {"quantum_computing", "quantum_error_correction", "chip_design"},
        "required_terms": ["quantum computing", "quantum processor", "quantum architecture", "compiler", "circuit", "processor"],
        "boost_terms": ["benchmark", "mapping", "architecture", "multiqudit", "cavity-based", "fault-tolerant"],
    },
    "measurement_control": {
        "label": "测控与读出",
        "title_cn": "QuantaMind 测控与读出日报",
        "title_en": "QuantaMind Measurement And Readout Daily Brief",
        "topic_ids": {"measurement_control", "chip_design"},
        "required_terms": ["readout", "calibration", "control", "ramsey", "rabi", "fidelity", "measurement"],
        "boost_terms": ["pulse", "microwave", "tls", "coherence", "active neighbor", "interface driving"],
    },
    "quantum_application": {
        "label": "量子应用与算法",
        "title_cn": "QuantaMind 量子应用与算法日报",
        "title_en": "QuantaMind Quantum Applications And Algorithms Daily Brief",
        "topic_ids": {"quantum_application", "quantum_computing", "ai_for_quantum"},
        "required_terms": ["quantum chemistry", "optimization", "simulation", "sensing", "algorithm", "application"],
        "boost_terms": ["materials", "finance", "variational", "hamiltonian", "solver", "benchmark"],
    },
}
TEAM_RELEVANCE = {
    "chip_design": {"targets": ["chip_designer", "theorist"], "suggestion": "可转化为版图/频率规划/耦合器设计的下一版输入。"},
    "chip_fabrication": {"targets": ["process_engineer", "knowledge_engineer"], "suggestion": "建议沉淀工艺窗口、失效模式和制造约束。"},
    "measurement_control": {"targets": ["device_ops", "measure_scientist"], "suggestion": "适合作为读出、校准、闭环控制优化的实验输入。"},
    "quantum_computing": {"targets": ["algorithm_engineer", "theorist"], "suggestion": "可评估对芯片拓扑、编译和算法映射的影响。"},
    "quantum_error_correction": {"targets": ["measure_scientist", "algorithm_engineer"], "suggestion": "建议结合当前比特参数评估容错门限和逻辑比特路线。"},
    "ai_for_quantum": {"targets": ["data_analyst", "knowledge_engineer"], "suggestion": "建议纳入数据建模、代理建模和自动调参能力路线。"},
    "ai_agents": {"targets": ["knowledge_engineer", "project_manager"], "suggestion": "建议跟踪智能体编排、工具调用、记忆与评测路线，评估对团队自动化研发的适配性。"},
    "quantum_application": {"targets": ["project_manager", "algorithm_engineer"], "suggestion": "适合作为应用牵引和场景对标的专题输入。"},
}
ROUTE_THEMES = {
    "chip_design": "超导量子比特/芯片架构设计",
    "chip_fabrication": "约瑟夫森结与工艺制造",
    "measurement_control": "读出、校准与闭环控制",
    "quantum_computing": "量子处理器架构与编译",
    "quantum_error_correction": "容错架构与量子纠错",
    "ai_for_quantum": "AI 辅助建模与自动优化",
    "ai_agents": "大模型、工具调用与智能体系统",
    "quantum_application": "量子应用与行业场景",
}
TECH_SYSTEM_PATHS = {
    "chip_design": ["器件与工艺层", "QPU/芯片设计", "比特/耦合器/谐振器"],
    "chip_fabrication": ["器件与工艺层", "工艺制造", "薄膜/刻蚀/约瑟夫森结"],
    "measurement_control": ["控制与读出层", "控制电子学与脉冲", "读出链路/校准/闭环"],
    "quantum_computing": ["软件与编译层", "量子程序与编译", "映射/路由/调度"],
    "quantum_error_correction": ["容错与体系层", "量子纠错", "编码/解码/容错门"],
    "ai_for_quantum": ["智能与自动化层", "AI for Quantum", "代理模型/自动优化"],
    "ai_agents": ["智能体技术栈", "智能体编排", "规划/工具调用/记忆"],
    "quantum_application": ["应用层", "行业应用", "化学/优化/仿真"],
}
TECH_SYSTEM_TAXONOMY = {
    "quantum_stack_v2": [
        {"id": "device", "label": "器件与工艺层", "modules": ["物理比特平台", "QPU/芯片设计", "封装互连", "工艺制造"]},
        {"id": "control", "label": "控制与读出层", "modules": ["控制电子学与脉冲", "读出链路", "标定与闭环控制", "低温系统集成"]},
        {"id": "software", "label": "软件与编译层", "modules": ["量子程序与SDK", "量子程序与编译", "映射/路由/调度", "ISA/微架构"]},
        {"id": "fault_tolerance", "label": "容错与体系层", "modules": ["量子纠错", "解码器", "容错逻辑门", "系统架构协同"]},
        {"id": "intelligence", "label": "智能与自动化层", "modules": ["AI for Quantum", "实验自动化", "误差缓解/参数优化", "智能体协同"]},
        {"id": "application", "label": "应用层", "modules": ["量子化学/材料", "优化/组合问题", "量子模拟", "量子机器学习/行业场景"]},
    ],
    "ai_agents_stack_v2": [
        {"id": "foundation", "label": "模型层", "modules": ["LLM/多模态模型", "推理/规划模型", "领域知识底座"]},
        {"id": "agent_core", "label": "智能体核心层", "modules": ["规划", "记忆", "工具调用", "多智能体协同"]},
        {"id": "delivery", "label": "执行与治理层", "modules": ["工作流编排", "任务执行", "评测基准", "安全治理"]},
    ],
}
TECH_SYSTEM_DETAIL_KEYWORDS = {
    "chip_design": {
        "比特设计": ["transmon", "fluxonium", "qubit", "qubit design"],
        "耦合器设计": ["coupler", "coupling"],
        "谐振器/读出腔": ["resonator", "readout resonator", "cavity"],
        "芯片版图与布局": ["layout", "placement", "topology", "chip design"],
    },
    "chip_fabrication": {
        "约瑟夫森结": ["josephson", "junction"],
        "薄膜沉积": ["deposition", "thin film"],
        "刻蚀与光刻": ["etch", "lithography", "patterning"],
        "良率与一致性": ["yield", "uniformity", "variation", "wafer"],
    },
    "measurement_control": {
        "脉冲优化": ["pulse", "waveform", "drag"],
        "读出放大链路": ["readout", "amplifier", "resonator"],
        "自动标定": ["calibration", "tune-up", "ramsey", "rabi"],
        "闭环反馈": ["feedback", "adaptive", "closed-loop"],
    },
    "quantum_computing": {
        "线路综合": ["synthesis", "circuit synthesis"],
        "映射与路由": ["mapping", "routing", "placement"],
        "调度优化": ["scheduling", "latency", "depth"],
        "处理器架构": ["architecture", "microarchitecture", "processor", "isa", "instruction set", "compiler"],
    },
    "quantum_error_correction": {
        "表面码": ["surface code", "surface-code"],
        "解码器": ["decoder", "syndrome"],
        "逻辑比特": ["logical qubit"],
        "容错门与门限": ["fault-tolerant", "threshold", "lattice surgery", "magic state"],
    },
    "ai_for_quantum": {
        "代理模型": ["surrogate", "neural network model", "ml model"],
        "误差建模": ["noise model", "error model"],
        "自动优化": ["optimization", "reinforcement learning", "bayesian"],
        "实验自动化": ["autonomous experiment", "auto-calibration", "closed-loop"],
    },
    "quantum_application": {
        "量子化学": ["chemistry", "molecule", "electronic structure"],
        "优化问题": ["optimization", "qubo"],
        "量子模拟": ["simulation", "hamiltonian"],
        "量子机器学习": ["quantum machine learning", "qml"],
    },
    "ai_agents": {
        "规划": ["planning", "plan"],
        "工具调用": ["tool use", "function calling", "tool calling"],
        "记忆": ["memory", "retrieval"],
        "多智能体协同": ["multi-agent", "agentic", "workflow", "orchestration"],
    },
}
TAXONOMY_LIBRARY_DIR = config.PROJECT_ROOT / "quantamind" / "knowledge" / "taxonomy"
TAXONOMY_RUNTIME_DIR = config.DEFAULT_ROOT / "intel" / "taxonomy_engineer"
TAXONOMY_RUNTIME_FILE = TAXONOMY_RUNTIME_DIR / "runtime_overlays.json"
TAXONOMY_PENDING_FILE = TAXONOMY_RUNTIME_DIR / "taxonomy_pending_updates.json"
METHOD_FIGURE_PRIMARY_HINTS = [
    "architecture", "workflow", "framework", "overview",
]
METHOD_FIGURE_SECONDARY_HINTS = [
    "pipeline", "system", "schematic", "method", "approach", "design", "layout",
    "stack", "decoder", "readout", "control", "compiler", "calibration",
]
METHOD_FIGURE_NEGATIVE_HINTS = [
    "result", "results", "benchmark", "ablation", "timing", "latency", "accuracy",
    "error bars", "histogram", "dataset", "training curve",
]
_STOPWORDS = {
    "quantum", "qubit", "using", "based", "with", "from", "for", "and", "the", "new", "towards",
    "superconducting", "paper", "study", "approach", "system", "method", "analysis", "results",
    "我们", "研究", "方法", "系统", "结果", "一个", "以及", "相关", "论文",
}
_TAXONOMY_UPDATE_STOPWORDS = _STOPWORDS | {
    "figure", "fig", "section", "introduction", "conclusion", "workflow", "framework", "architecture",
    "overview", "device", "devices", "control", "readout", "code", "codes", "quantum-computing",
}

_papers_cache: Dict[str, Dict[str, Any]] = {}
_reports_cache: Dict[str, Dict[str, Any]] = {}
_translation_cache: Dict[str, Dict[str, str]] = {}
_method_figure_cache: Dict[str, Dict[str, Any]] = {}
_taxonomy_library_cache: Dict[str, Dict[str, Any]] = {}
_taxonomy_runtime_cache: Dict[str, Any] = {}
_taxonomy_pending_cache: Dict[str, Any] = {}
_last_fetch_monotonic: float = 0.0
_feishu_token_cache: Dict[str, Any] = {"token": "", "expires_at": 0.0}

FETCH_MIN_INTERVAL_SECONDS = 2.0
FETCH_MAX_RETRIES = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
FEISHU_IMAGE_UPLOAD_MAX_RETRIES = 3
FEISHU_IMAGE_UPLOAD_RETRY_DELAY_SECONDS = 1.5
INTEL_FETCH_HTTP_TIMEOUT_SECONDS = 12.0
INTEL_FETCH_SOFT_LIMIT_SECONDS = 45.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _local_now() -> datetime:
    return datetime.now().astimezone()


def _fetch_time_left(deadline_monotonic: Optional[float]) -> Optional[float]:
    if deadline_monotonic is None:
        return None
    return deadline_monotonic - time.monotonic()


def _fetch_deadline_exceeded(deadline_monotonic: Optional[float]) -> bool:
    remaining = _fetch_time_left(deadline_monotonic)
    return remaining is not None and remaining <= 0


def _bounded_fetch_timeout(deadline_monotonic: Optional[float], default_seconds: float) -> float:
    remaining = _fetch_time_left(deadline_monotonic)
    if remaining is None:
        return default_seconds
    # 给 httpx 留出一点最小超时窗口，避免传入 0 或负值
    return max(1.0, min(default_seconds, remaining))


def _lightweight_feishu_translation(record: Dict[str, Any]) -> Dict[str, str]:
    title = (record.get("title") or "").strip()
    title_zh = title if _contains_chinese(title) else "（标题翻译已跳过，请查看英文标题）"
    summary_zh = (
        record.get("summary_cn")
        or record.get("core_conclusion")
        or record.get("technical_route")
        or "（摘要翻译已跳过，请查看英文摘要）"
    )
    return {
        "title_zh": _shorten_text(title_zh, 160),
        "summary_zh": _shorten_text(summary_zh, 260),
    }


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _safe_parse_dt(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return _parse_dt(value)
    except Exception:
        return None


def _parse_rfc2822_dt(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _sentence_split(text: str) -> List[str]:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    return [s.strip() for s in re.split(r"(?<=[\.\!\?;])\s+", normalized) if s.strip()]


def _pick_sentences(text: str, patterns: List[str], fallback_first: bool = False, reverse: bool = False) -> str:
    sentences = _sentence_split(text)
    if reverse:
        sentences = list(reversed(sentences))
    selected: List[str] = []
    for sentence in sentences:
        low = sentence.lower()
        if any(p in low for p in patterns):
            selected.append(sentence)
        if len(selected) >= 2:
            break
    if not selected and fallback_first and sentences:
        selected = sentences[:2]
    return " ".join(selected)


def _extract_technical_route(summary: str) -> str:
    return _pick_sentences(
        summary,
        ["we propose", "we present", "we develop", "we introduce", "using", "based on", "architecture", "fabrication", "control"],
        fallback_first=True,
    )


def _extract_conclusion(summary: str) -> str:
    return _pick_sentences(
        summary,
        ["we show", "we demonstrate", "results show", "we find", "our results", "achieve", "improve", "outperform", "conclude"],
        fallback_first=True,
        reverse=True,
    )


def _infer_topics(title: str, summary: str) -> List[str]:
    text = f"{title}\n{summary}".lower()
    matched: List[str] = []
    for topic_id, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matched.append(topic_id)
    return matched


def _ensure_topics(record: Dict[str, Any]) -> List[str]:
    topics = record.get("matched_topics") or _infer_topics(record.get("title", ""), record.get("summary", ""))
    if not topics:
        categories = " ".join(record.get("categories", [])).lower()
        if "quant-ph" in categories:
            topics = ["quantum_computing"]
        elif "cond-mat.supr-con" in categories:
            topics = ["chip_design"]
        elif "cs.ai" in categories or "cs.lg" in categories:
            topics = ["ai_agents"]
    return sorted(set(topics))


def _importance(record: Dict[str, Any]) -> str:
    text = f"{record.get('title', '')}\n{record.get('summary', '')}".lower()
    high_hits = sum(1 for token in ["superconducting", "transmon", "surface code", "readout", "fabrication", "josephson"] if token in text)
    if high_hits >= 3:
        return "high"
    if high_hits >= 1:
        return "medium"
    return "info"


def _team_relevance(record: Dict[str, Any]) -> Dict[str, Any]:
    targets: List[str] = []
    suggestions: List[str] = []
    for topic in _ensure_topics(record):
        rule = TEAM_RELEVANCE.get(topic)
        if not rule:
            continue
        targets.extend(rule["targets"])
        suggestions.append(rule["suggestion"])
    targets = list(dict.fromkeys(targets))
    suggestion = suggestions[0] if suggestions else "建议由知识工程师复核并决定是否沉淀为专题知识卡片。"
    return {"targets": targets, "suggestion": suggestion}


def _extract_problem_statement(title: str, summary: str) -> str:
    return _pick_sentences(
        summary,
        ["challenge", "problem", "bottleneck", "limitation", "noise", "hallucination", "reliability", "scalability"],
        fallback_first=False,
    ) or title


def _extract_method_summary(summary: str) -> str:
    return _pick_sentences(
        summary,
        ["we propose", "we present", "we introduce", "framework", "architecture", "workflow", "method", "agent", "model"],
        fallback_first=True,
    )


def _extract_evaluation_summary(summary: str) -> str:
    return _pick_sentences(
        summary,
        ["experiment", "benchmark", "evaluation", "results", "accuracy", "fidelity", "performance", "latency"],
        fallback_first=False,
    )


def _extract_focus_components(record: Dict[str, Any], limit: int = 4) -> List[str]:
    text = f"{record.get('title', '')} {record.get('summary', '')}".lower()
    topic_keywords = []
    for topic in _ensure_topics(record):
        topic_keywords.extend(TOPIC_KEYWORDS.get(topic, []))
    seen: List[str] = []
    for keyword in topic_keywords:
        normalized = keyword.strip()
        if normalized and normalized.lower() in text and normalized not in seen:
            seen.append(normalized)
        if len(seen) >= limit:
            break
    return seen


def _tech_stack_text(record: Dict[str, Any]) -> str:
    return f"{record.get('title', '')} {record.get('summary', '')}".lower()


def _detect_stack_detail(primary_topic: str, record: Dict[str, Any]) -> str:
    text = _tech_stack_text(record)
    rules = TECH_SYSTEM_DETAIL_KEYWORDS.get(primary_topic) or {}
    best_label = ""
    best_score = 0
    for label, keywords in rules.items():
        score = sum(1 for keyword in keywords if keyword.lower() in text)
        if score > best_score:
            best_label = label
            best_score = score
    return best_label


def _extract_stack_evidence_terms(record: Dict[str, Any], detail: str = "", limit: int = 5) -> List[str]:
    evidence = list(_extract_focus_components(record, limit=limit))
    if detail and detail not in evidence:
        evidence.insert(0, detail)
    return evidence[:limit]


def _load_base_taxonomy_engineer_libraries(force: bool = False) -> Dict[str, Dict[str, Any]]:
    global _taxonomy_library_cache
    if _taxonomy_library_cache and not force:
        return copy.deepcopy(_taxonomy_library_cache)
    libraries: Dict[str, Dict[str, Any]] = {}
    for path in sorted(TAXONOMY_LIBRARY_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            _log.warning("加载技术体系库失败 %s: %s", path, e)
            continue
        topic_id = (payload.get("topic_id") or path.stem).strip()
        if not topic_id:
            continue
        libraries[topic_id] = payload
    _taxonomy_library_cache = libraries
    return copy.deepcopy(_taxonomy_library_cache)


def _load_taxonomy_runtime_state(force: bool = False) -> Dict[str, Any]:
    global _taxonomy_runtime_cache
    if _taxonomy_runtime_cache and not force:
        return copy.deepcopy(_taxonomy_runtime_cache)
    if not TAXONOMY_RUNTIME_FILE.exists():
        _taxonomy_runtime_cache = {}
        return {}
    try:
        _taxonomy_runtime_cache = json.loads(TAXONOMY_RUNTIME_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        _log.warning("加载技术体系工程师运行缓存失败 %s: %s", TAXONOMY_RUNTIME_FILE, e)
        _taxonomy_runtime_cache = {}
    return copy.deepcopy(_taxonomy_runtime_cache)


def _save_taxonomy_runtime_state(state: Dict[str, Any]) -> None:
    global _taxonomy_runtime_cache
    TAXONOMY_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    TAXONOMY_RUNTIME_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    _taxonomy_runtime_cache = copy.deepcopy(state)


def _load_taxonomy_pending_state(force: bool = False) -> Dict[str, Any]:
    global _taxonomy_pending_cache
    if _taxonomy_pending_cache and not force:
        return copy.deepcopy(_taxonomy_pending_cache)
    if not TAXONOMY_PENDING_FILE.exists():
        _taxonomy_pending_cache = {"updated_at": "", "updates": []}
        return copy.deepcopy(_taxonomy_pending_cache)
    try:
        loaded = json.loads(TAXONOMY_PENDING_FILE.read_text(encoding="utf-8"))
        updates = loaded.get("updates") if isinstance(loaded, dict) else []
        _taxonomy_pending_cache = {
            "updated_at": (loaded or {}).get("updated_at", "") if isinstance(loaded, dict) else "",
            "updates": updates if isinstance(updates, list) else [],
        }
    except Exception as e:
        _log.warning("加载技术体系待审池失败 %s: %s", TAXONOMY_PENDING_FILE, e)
        _taxonomy_pending_cache = {"updated_at": "", "updates": []}
    return copy.deepcopy(_taxonomy_pending_cache)


def _save_taxonomy_pending_state(state: Dict[str, Any]) -> None:
    global _taxonomy_pending_cache
    TAXONOMY_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    TAXONOMY_PENDING_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    _taxonomy_pending_cache = copy.deepcopy(state)


def _merge_taxonomy_point_overlay(point: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(point)
    supplement_terms = list(dict.fromkeys((overlay.get("supplement_terms") or [])))
    evidence_refs = overlay.get("evidence_refs") or []
    if supplement_terms:
        merged["supplement_terms"] = supplement_terms
        merged["keywords"] = list(dict.fromkeys((merged.get("keywords") or []) + supplement_terms))
    if evidence_refs:
        merged["evidence_refs"] = evidence_refs
    return merged


def _merge_taxonomy_engineer_library(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    point_updates = overlay.get("point_updates") or {}
    if overlay.get("updated_at"):
        merged["runtime_updated_at"] = overlay.get("updated_at")
    for lane in merged.get("lanes") or []:
        for module in lane.get("modules") or []:
            module_points = []
            for point in module.get("points") or []:
                module_points.append(_merge_taxonomy_point_overlay(point, point_updates.get(point.get("id", ""), {})))
            module["points"] = module_points
    return merged


def _load_taxonomy_engineer_libraries(force: bool = False) -> Dict[str, Dict[str, Any]]:
    bases = _load_base_taxonomy_engineer_libraries(force=force)
    overlays = _load_taxonomy_runtime_state(force=force)
    libraries: Dict[str, Dict[str, Any]] = {}
    for topic_id, base in bases.items():
        libraries[topic_id] = _merge_taxonomy_engineer_library(base, (overlays.get("libraries") or {}).get(topic_id, {}))
    return libraries


def _score_keyword_hits(text: str, keywords: List[str]) -> tuple[int, List[str]]:
    hits: List[str] = []
    score = 0
    for keyword in keywords:
        normalized = keyword.lower().strip()
        if normalized and normalized in text:
            hits.append(keyword)
            score += 3 if (" " in normalized or "-" in normalized or "/" in normalized) else 2
    return score, hits


def _score_taxonomy_engineer_library(text: str, library: Dict[str, Any]) -> int:
    score = 0
    for lane in library.get("lanes") or []:
        lane_score, _ = _score_keyword_hits(text, lane.get("keywords") or [])
        score += lane_score
        for module in lane.get("modules") or []:
            module_score, _ = _score_keyword_hits(text, module.get("keywords") or [])
            score += module_score
            for point in module.get("points") or []:
                point_score, _ = _score_keyword_hits(text, point.get("keywords") or [])
                score += point_score * 2
    return score


def _select_taxonomy_engineer_library(record: Dict[str, Any]) -> Dict[str, Any]:
    topics = record.get("matched_topics") or _ensure_topics(record)
    text = _tech_stack_text(record)
    libraries = _load_taxonomy_engineer_libraries()
    candidates = []
    for topic in topics:
        library = libraries.get(topic)
        if library:
            candidates.append((_score_taxonomy_engineer_library(text, library), library))
    if not candidates:
        return {}
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _map_record_to_taxonomy_engineer_library(record: Dict[str, Any], library: Dict[str, Any]) -> Dict[str, Any]:
    text = _tech_stack_text(record)
    best: Dict[str, Any] = {}
    best_score = -1
    for lane in library.get("lanes") or []:
        lane_score, lane_hits = _score_keyword_hits(text, lane.get("keywords") or [])
        for module in lane.get("modules") or []:
            module_score, module_hits = _score_keyword_hits(text, module.get("keywords") or [])
            for point in module.get("points") or []:
                point_score, point_hits = _score_keyword_hits(text, point.get("keywords") or [])
                total = lane_score + module_score + point_score * 2
                if total > best_score:
                    best_score = total
                    best = {
                        "lane_id": lane.get("id", ""),
                        "lane_label": lane.get("label", ""),
                        "module_id": module.get("id", ""),
                        "module_label": module.get("label", ""),
                        "point_id": point.get("id", ""),
                        "point_label": point.get("label", ""),
                        "score": total,
                        "evidence_terms": list(dict.fromkeys((point_hits + module_hits + lane_hits)))[:6],
                    }
    if best_score <= 0:
        lane = (library.get("lanes") or [{}])[0]
        module = (lane.get("modules") or [{}])[0]
        point = (module.get("points") or [{}])[0]
        best = {
            "lane_id": lane.get("id", ""),
            "lane_label": lane.get("label", ""),
            "module_id": module.get("id", ""),
            "module_label": module.get("label", ""),
            "point_id": point.get("id", ""),
            "point_label": point.get("label", "待人工定位"),
            "score": 0,
            "evidence_terms": [],
        }
    return best


def _build_taxonomy_engineer_lanes(library: Dict[str, Any], selected: Dict[str, Any]) -> List[Dict[str, Any]]:
    lanes: List[Dict[str, Any]] = []
    for lane in library.get("lanes") or []:
        lane_copy = {"id": lane.get("id", ""), "label": lane.get("label", ""), "selected": lane.get("id") == selected.get("lane_id"), "modules": []}
        for module in lane.get("modules") or []:
            module_copy = {
                "id": module.get("id", ""),
                "label": module.get("label", ""),
                "selected": module.get("id") == selected.get("module_id"),
                "points": [],
            }
            for point in module.get("points") or []:
                module_copy["points"].append({
                    "id": point.get("id", ""),
                    "label": point.get("label", ""),
                    "selected": point.get("id") == selected.get("point_id"),
                })
            lane_copy["modules"].append(module_copy)
        lanes.append(lane_copy)
    return lanes


def _primary_topic(record: Dict[str, Any]) -> str:
    topics = record.get("matched_topics") or _ensure_topics(record)
    return topics[0] if topics else "quantum_computing"


def _build_generic_tech_system_map(record: Dict[str, Any]) -> Dict[str, Any]:
    primary_topic = _primary_topic(record)
    matched_topics = record.get("matched_topics") or _ensure_topics(record)
    path = list(TECH_SYSTEM_PATHS.get(primary_topic, ["通用技术体系", TOPIC_LABELS.get(primary_topic, primary_topic)]))
    detail = _detect_stack_detail(primary_topic, record)
    if detail and detail not in path:
        path.append(detail)
    taxonomy_id = "ai_agents_stack_v2" if primary_topic == "ai_agents" else "quantum_stack_v2"
    return {
        "version": "v2",
        "taxonomy_id": taxonomy_id,
        "domain": "ai_agents" if primary_topic == "ai_agents" else "quantum",
        "system_label": "AI 智能体技术体系" if primary_topic == "ai_agents" else "量子技术体系",
        "highlighted_topic": {"id": primary_topic, "label": TOPIC_LABELS.get(primary_topic, primary_topic)},
        "highlighted_layer": path[0] if path else "",
        "highlighted_module": path[1] if len(path) > 1 else "",
        "highlighted_detail": path[2] if len(path) > 2 else "",
        "highlighted_path": path,
        "matched_topics": [{"id": topic, "label": TOPIC_LABELS.get(topic, topic)} for topic in matched_topics],
        "focus_components": _extract_focus_components(record),
        "evidence_terms": _extract_stack_evidence_terms(record, detail),
        "taxonomy_nodes": TECH_SYSTEM_TAXONOMY.get(taxonomy_id, []),
        "render_hints": {"chart_type": "stack_lane_highlight", "layout": "horizontal_lanes"},
    }


def _build_tech_system_map(record: Dict[str, Any]) -> Dict[str, Any]:
    library = _select_taxonomy_engineer_library(record)
    if library:
        selected = _map_record_to_taxonomy_engineer_library(record, library)
        lanes = _build_taxonomy_engineer_lanes(library, selected)
        evidence_terms = selected.get("evidence_terms") or _extract_stack_evidence_terms(record, selected.get("point_label", ""))
        return {
            "version": "taxonomy_engineer_v1",
            "source_mode": "taxonomy_library",
            "library_id": library.get("library_id", ""),
            "library_label": library.get("library_label", "技术体系工程师"),
            "library_summary": library.get("library_summary", ""),
            "domain": "quantum",
            "system_label": library.get("system_label", "量子技术体系"),
            "highlighted_topic": {"id": _primary_topic(record), "label": TOPIC_LABELS.get(_primary_topic(record), _primary_topic(record))},
            "highlighted_layer": selected.get("lane_label", ""),
            "highlighted_module": selected.get("module_label", ""),
            "highlighted_detail": selected.get("point_label", ""),
            "highlighted_path": [selected.get("lane_label", ""), selected.get("module_label", ""), selected.get("point_label", "")],
            "matched_topics": [{"id": topic, "label": TOPIC_LABELS.get(topic, topic)} for topic in (record.get("matched_topics") or _ensure_topics(record))],
            "focus_components": _extract_focus_components(record),
            "evidence_terms": evidence_terms[:6],
            "taxonomy_lanes": lanes,
            "selected_node": selected,
            "render_hints": {"chart_type": "taxonomy_library_highlight", "layout": "three_lane_library"},
        }
    return _build_generic_tech_system_map(record)


def _clean_taxonomy_source_text(text: str) -> str:
    normalized = _clean_html_text(text)
    return _shorten_text(normalized, 40000)


def _fetch_taxonomy_source_document(client: httpx.Client, source: Dict[str, Any]) -> Dict[str, Any]:
    url = (source.get("url") or "").strip()
    if not url:
        return {}
    _respect_fetch_interval()
    resp = client.get(url, headers={"User-Agent": "QuantaMind/0.1 taxonomy-engineer"})
    resp.raise_for_status()
    title = (source.get("title") or source.get("id") or url).strip()
    text = _clean_taxonomy_source_text(resp.text)
    return {
        "source_id": source.get("id") or hashlib.sha1(url.encode("utf-8")).hexdigest()[:12],
        "title": title,
        "url": url,
        "kind": source.get("kind", "reference"),
        "text": f"{title}. {text}",
    }


def _extract_taxonomy_candidate_terms(text: str, keywords: List[str], limit: int = 4) -> List[str]:
    keyword_set = {item.lower().strip() for item in keywords if item.strip()}
    counts: Dict[str, int] = {}
    related_sentences = [sentence for sentence in _sentence_split(text) if any(keyword in sentence.lower() for keyword in keyword_set)]
    for sentence in related_sentences:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\-\+]{2,}", sentence.lower())
        filtered = [token for token in tokens if token not in _TAXONOMY_UPDATE_STOPWORDS and token not in keyword_set]
        for token in filtered:
            counts[token] = counts.get(token, 0) + 1
        for idx in range(len(filtered) - 1):
            pair = f"{filtered[idx]} {filtered[idx + 1]}"
            if pair.replace(" ", "") and not any(part in _TAXONOMY_UPDATE_STOPWORDS for part in pair.split()):
                counts[pair] = counts.get(pair, 0) + 2
    singles = sorted(((term, score) for term, score in counts.items() if " " not in term), key=lambda item: (-item[1], item[0]))
    phrases = sorted(((term, score) for term, score in counts.items() if " " in term), key=lambda item: (-item[1], item[0]))
    ranked = singles + phrases
    return [term for term, _ in ranked[:limit]]


def _iter_taxonomy_points(library: Dict[str, Any]) -> List[Dict[str, Any]]:
    points: List[Dict[str, Any]] = []
    for lane in library.get("lanes") or []:
        for module in lane.get("modules") or []:
            for point in module.get("points") or []:
                points.append({
                    "lane_id": lane.get("id", ""),
                    "lane_label": lane.get("label", ""),
                    "module_id": module.get("id", ""),
                    "module_label": module.get("label", ""),
                    "point": point,
                })
    return points


def _taxonomy_pending_update_id(topic_id: str, point_id: str) -> str:
    raw = f"{topic_id}|{point_id}"
    return "taxupd_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _merge_evidence_refs(existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in list(existing) + list(incoming):
        key = item.get("source_id") or item.get("url") or json.dumps(item, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def _build_taxonomy_pending_entry(topic_id: str, library: Dict[str, Any], point_meta: Dict[str, Any], point_overlay: Dict[str, Any]) -> Dict[str, Any]:
    now_iso = _now_iso()
    return {
        "update_id": _taxonomy_pending_update_id(topic_id, point_meta["point"].get("id", "")),
        "topic_id": topic_id,
        "library_id": library.get("library_id", topic_id),
        "library_label": library.get("library_label", "技术体系工程师"),
        "system_label": library.get("system_label", ""),
        "lane_id": point_meta.get("lane_id", ""),
        "lane_label": point_meta.get("lane_label", ""),
        "module_id": point_meta.get("module_id", ""),
        "module_label": point_meta.get("module_label", ""),
        "point_id": point_meta["point"].get("id", ""),
        "point_label": point_meta["point"].get("label", ""),
        "supplement_terms": list(point_overlay.get("supplement_terms") or []),
        "evidence_refs": list(point_overlay.get("evidence_refs") or []),
        "status": "pending",
        "created_at": now_iso,
        "updated_at": now_iso,
        "occurrence_count": 1,
    }


def _find_pending_update(state: Dict[str, Any], update_id: str) -> Optional[Dict[str, Any]]:
    for item in state.get("updates") or []:
        if item.get("update_id") == update_id:
            return item
    return None


def _existing_runtime_point_overlay(runtime_state: Dict[str, Any], topic_id: str, point_id: str) -> Dict[str, Any]:
    return ((((runtime_state.get("libraries") or {}).get(topic_id) or {}).get("point_updates") or {}).get(point_id) or {})


def _apply_candidate_to_pending(state: Dict[str, Any], candidate: Dict[str, Any], runtime_overlay: Dict[str, Any]) -> bool:
    runtime_terms = {term.lower() for term in (runtime_overlay.get("supplement_terms") or [])}
    runtime_sources = {item.get("source_id") for item in (runtime_overlay.get("evidence_refs") or [])}
    new_terms = [term for term in (candidate.get("supplement_terms") or []) if term.lower() not in runtime_terms]
    new_evidence = [item for item in (candidate.get("evidence_refs") or []) if item.get("source_id") not in runtime_sources]
    if not new_terms and not new_evidence:
        return False
    existing = _find_pending_update(state, candidate["update_id"])
    now_iso = _now_iso()
    if existing:
        existing["supplement_terms"] = list(dict.fromkeys((existing.get("supplement_terms") or []) + new_terms))
        existing["evidence_refs"] = _merge_evidence_refs(existing.get("evidence_refs") or [], new_evidence)
        existing["updated_at"] = now_iso
        existing["occurrence_count"] = int(existing.get("occurrence_count", 1) or 1) + 1
    else:
        candidate = dict(candidate)
        candidate["supplement_terms"] = new_terms
        candidate["evidence_refs"] = new_evidence
        candidate["created_at"] = now_iso
        candidate["updated_at"] = now_iso
        state.setdefault("updates", []).append(candidate)
    state["updated_at"] = now_iso
    return True


def list_taxonomy_pending_updates(topic_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = list((_load_taxonomy_pending_state().get("updates") or []))
    if topic_id:
        items = [item for item in items if item.get("topic_id") == topic_id]
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return items


def approve_taxonomy_pending_update(update_id: str, reviewer: Optional[str] = None, note: Optional[str] = None) -> Dict[str, Any]:
    pending = _load_taxonomy_pending_state(force=True)
    target = _find_pending_update(pending, update_id)
    if not target:
        return {"error": f"pending update {update_id} not found"}
    runtime_state = _load_taxonomy_runtime_state(force=True)
    runtime_state.setdefault("libraries", {})
    topic_state = runtime_state["libraries"].setdefault(target["topic_id"], {
        "library_id": target.get("library_id", target["topic_id"]),
        "topic_id": target["topic_id"],
        "updated_at": _now_iso(),
        "sources_checked": 0,
        "point_updates": {},
    })
    point_state = topic_state.setdefault("point_updates", {}).setdefault(target["point_id"], {"supplement_terms": [], "evidence_refs": []})
    point_state["supplement_terms"] = list(dict.fromkeys((point_state.get("supplement_terms") or []) + (target.get("supplement_terms") or [])))
    point_state["evidence_refs"] = _merge_evidence_refs(point_state.get("evidence_refs") or [], target.get("evidence_refs") or [])
    topic_state["updated_at"] = _now_iso()
    runtime_state["updated_at"] = topic_state["updated_at"]
    _save_taxonomy_runtime_state(runtime_state)
    pending["updates"] = [item for item in (pending.get("updates") or []) if item.get("update_id") != update_id]
    pending["updated_at"] = _now_iso()
    _save_taxonomy_pending_state(pending)
    _taxonomy_library_cache.clear()
    return {
        "status": "approved",
        "update_id": update_id,
        "topic_id": target["topic_id"],
        "point_id": target["point_id"],
        "reviewer": reviewer,
        "note": note,
        "remaining_pending": len(pending.get("updates") or []),
    }


def reject_taxonomy_pending_update(update_id: str, reviewer: Optional[str] = None, note: Optional[str] = None) -> Dict[str, Any]:
    pending = _load_taxonomy_pending_state(force=True)
    target = _find_pending_update(pending, update_id)
    if not target:
        return {"error": f"pending update {update_id} not found"}
    pending["updates"] = [item for item in (pending.get("updates") or []) if item.get("update_id") != update_id]
    pending["updated_at"] = _now_iso()
    _save_taxonomy_pending_state(pending)
    return {
        "status": "rejected",
        "update_id": update_id,
        "topic_id": target["topic_id"],
        "point_id": target["point_id"],
        "reviewer": reviewer,
        "note": note,
        "remaining_pending": len(pending.get("updates") or []),
    }


def _append_taxonomy_overlay(point_updates: Dict[str, Any], point_id: str, source_doc: Dict[str, Any], matched_terms: List[str], supplement_terms: List[str]) -> None:
    entry = point_updates.setdefault(point_id, {"supplement_terms": [], "evidence_refs": []})
    entry["supplement_terms"] = list(dict.fromkeys((entry.get("supplement_terms") or []) + supplement_terms))
    existing_ids = {item.get("source_id") for item in entry.get("evidence_refs") or []}
    if source_doc.get("source_id") not in existing_ids:
        entry.setdefault("evidence_refs", []).append({
            "source_id": source_doc.get("source_id"),
            "title": source_doc.get("title"),
            "url": source_doc.get("url"),
            "kind": source_doc.get("kind"),
            "matched_terms": matched_terms[:6],
            "captured_at": _now_iso(),
        })


def _build_taxonomy_overlay_for_library(client: httpx.Client, topic_id: str, library: Dict[str, Any]) -> Dict[str, Any]:
    overlay = {
        "library_id": library.get("library_id", topic_id),
        "topic_id": topic_id,
        "updated_at": _now_iso(),
        "sources_checked": 0,
        "point_updates": {},
    }
    points = _iter_taxonomy_points(library)
    for source in library.get("review_sources") or []:
        try:
            source_doc = _fetch_taxonomy_source_document(client, source)
        except Exception as e:
            _log.warning("技术体系工程师抓取来源失败 [%s/%s]: %s", topic_id, source.get("url"), e)
            continue
        if not source_doc:
            continue
        overlay["sources_checked"] += 1
        source_text = source_doc.get("text", "").lower()
        for item in points:
            point = item["point"]
            keywords = point.get("keywords") or []
            score, hits = _score_keyword_hits(source_text, keywords)
            if score <= 0:
                continue
            supplement_terms = _extract_taxonomy_candidate_terms(source_doc.get("text", ""), keywords)
            _append_taxonomy_overlay(overlay["point_updates"], point.get("id", ""), source_doc, hits, supplement_terms)
    return overlay


def run_taxonomy_engineer_update(force: bool = False) -> Dict[str, Any]:
    libraries = _load_base_taxonomy_engineer_libraries(force=True)
    if not libraries:
        return {"status": "skipped", "reason": "no_taxonomy_libraries"}
    pending_state = _load_taxonomy_pending_state(force=True)
    runtime_state = _load_taxonomy_runtime_state(force=True)
    if not pending_state:
        pending_state = {"updated_at": "", "updates": []}
    updated_points = 0
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        for topic_id, library in libraries.items():
            overlay = _build_taxonomy_overlay_for_library(client, topic_id, library)
            point_index = {item["point"].get("id", ""): item for item in _iter_taxonomy_points(library)}
            for point_id, point_overlay in (overlay.get("point_updates") or {}).items():
                point_meta = point_index.get(point_id)
                if not point_meta:
                    continue
                candidate = _build_taxonomy_pending_entry(topic_id, library, point_meta, point_overlay)
                if _apply_candidate_to_pending(
                    pending_state,
                    candidate,
                    _existing_runtime_point_overlay(runtime_state, topic_id, point_id),
                ):
                    updated_points += 1
    if updated_points == 0:
        return {"status": "unchanged", "libraries": len(libraries), "updated_points": 0, "pending_updates": len(pending_state.get("updates") or [])}
    _save_taxonomy_pending_state(pending_state)
    return {
        "status": "pending_updated",
        "libraries": len(libraries),
        "updated_points": updated_points,
        "updated_at": pending_state.get("updated_at", _now_iso()),
        "pending_updates": len(pending_state.get("updates") or []),
    }


def _build_tech_route_graph(record: Dict[str, Any]) -> Dict[str, Any]:
    problem = _extract_problem_statement(record.get("title", ""), record.get("summary", ""))
    method = _extract_method_summary(record.get("summary", ""))
    route = record.get("technical_route") or method
    evaluation = _extract_evaluation_summary(record.get("summary", ""))
    conclusion = record.get("core_conclusion") or _extract_conclusion(record.get("summary", ""))
    components = _extract_focus_components(record)
    nodes = [
        {"id": "problem", "label": "研究问题", "kind": "problem", "text": problem},
        {"id": "method", "label": "核心方法", "kind": "method", "text": method or route},
        {"id": "implementation", "label": "技术实现", "kind": "implementation", "text": route},
        {"id": "evaluation", "label": "实验验证", "kind": "evaluation", "text": evaluation or "摘要中未明确给出独立实验段落。"},
        {"id": "conclusion", "label": "结论输出", "kind": "conclusion", "text": conclusion or "摘要中未明确给出独立结论段落。"},
    ]
    return {
        "version": "v2",
        "graph_type": "pipeline",
        "title": record.get("title", ""),
        "focus_topic": {"id": _primary_topic(record), "label": TOPIC_LABELS.get(_primary_topic(record), _primary_topic(record))},
        "components": components,
        "nodes": nodes,
        "method_figure": record.get("method_figure") or {},
        "edges": [
            {"source": "problem", "target": "method", "label": "方法设计"},
            {"source": "method", "target": "implementation", "label": "实现展开"},
            {"source": "implementation", "target": "evaluation", "label": "实验验证"},
            {"source": "evaluation", "target": "conclusion", "label": "结果沉淀"},
        ],
        "render_hints": {"chart_type": "route_flow", "layout": "left_to_right"},
    }


def _extract_arxiv_id(record: Dict[str, Any]) -> str:
    for candidate in [record.get("arxiv_url", ""), record.get("pdf_url", ""), record.get("paper_id", "")]:
        match = re.search(r"(?:arxiv\.org/(?:abs|pdf)/|^)([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", candidate or "")
        if match:
            return match.group(1).replace(".pdf", "")
    return ""


def _ar5iv_html_url(record: Dict[str, Any]) -> str:
    arxiv_id = _extract_arxiv_id(record)
    return f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}" if arxiv_id else ""


def _clean_html_text(value: str) -> str:
    return re.sub(r"\s+", " ", html_unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def _score_method_figure(caption: str, record: Dict[str, Any]) -> int:
    text = caption.lower()
    primary_hits = sum(1 for hint in METHOD_FIGURE_PRIMARY_HINTS if hint in text)
    secondary_hits = sum(1 for hint in METHOD_FIGURE_SECONDARY_HINTS if hint in text)
    negative_hits = sum(1 for hint in METHOD_FIGURE_NEGATIVE_HINTS if hint in text)
    score = primary_hits * 6
    score += secondary_hits * 2
    score -= negative_hits * 4
    score += sum(1 for term in _extract_focus_components(record, limit=6) if term.lower() in text)
    score += sum(1 for keyword in TOPIC_KEYWORDS.get(_primary_topic(record), [])[:12] if keyword.lower() in text)
    if primary_hits == 0 and negative_hits > 0:
        score -= 6
    if primary_hits == 0 and secondary_hits == 0:
        score -= 3
    return score


def _parse_ar5iv_method_figure(html: str, base_url: str, record: Dict[str, Any]) -> Dict[str, Any]:
    pattern = re.compile(
        r'<figure[^>]*class="[^"]*ltx_figure[^"]*"[^>]*>(?P<body>[\s\S]*?)</figure>',
        re.IGNORECASE,
    )
    best: Dict[str, Any] = {}
    best_score = 0
    for idx, match in enumerate(pattern.finditer(html), start=1):
        body = match.group("body")
        img_match = re.search(r'<img[^>]+src="([^"]+)"', body, re.IGNORECASE)
        caption_match = re.search(r"<figcaption[^>]*>([\s\S]*?)</figcaption>", body, re.IGNORECASE)
        if not img_match or not caption_match:
            continue
        caption = _clean_html_text(caption_match.group(1))
        if not caption:
            continue
        score = _score_method_figure(caption, record)
        if score <= 0:
            continue
        if score > best_score:
            best_score = score
            best = {
                "source": "ar5iv",
                "figure_index": idx,
                "caption": caption,
                "image_url": urljoin(base_url, img_match.group(1)),
                "score": score,
            }
    return best


def _extract_method_figure(record: Dict[str, Any]) -> Dict[str, Any]:
    cache_key = record.get("paper_id") or record.get("arxiv_url") or record.get("title") or ""
    if cache_key and cache_key in _method_figure_cache:
        return dict(_method_figure_cache[cache_key])
    ar5iv_url = _ar5iv_html_url(record)
    if not ar5iv_url:
        return {}
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            resp = client.get(ar5iv_url)
            resp.raise_for_status()
        result = _parse_ar5iv_method_figure(resp.text, ar5iv_url, record)
        if cache_key:
            _method_figure_cache[cache_key] = dict(result)
        return result
    except Exception as e:
        _log.info("方法图提取失败，跳过该论文: %s", e)
        return {}


def _attach_method_figure(record: Dict[str, Any]) -> Dict[str, Any]:
    route_graph = dict(record.get("tech_route_graph") or {})
    method_figure = route_graph.get("method_figure") or record.get("method_figure") or _extract_method_figure(record)
    if not method_figure:
        return record
    enriched = dict(record)
    route_graph["method_figure"] = method_figure
    system_map = enriched.get("tech_system_map") or _build_tech_system_map(enriched)
    system_map, route_graph = _attach_visual_assets(system_map, route_graph, enriched)
    enriched["tech_system_map"] = system_map
    enriched["tech_route_graph"] = route_graph
    enriched["method_figure"] = method_figure
    return enriched


def _svg_text_lines(text: str, max_chars: int = 18, max_lines: int = 4) -> List[str]:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    if not normalized:
        return [""]
    lines: List[str] = []
    current = ""
    for ch in normalized:
        if len(current) >= max_chars and ch != " ":
            lines.append(current.strip())
            current = ch
        else:
            current += ch
    if current.strip():
        lines.append(current.strip())
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [_shorten_text(" ".join(lines[max_lines - 1:]), max_chars)]
    return lines


def _svg_text_block(x: int, y: int, lines: List[str], font_size: int = 16, color: str = "#0f172a",
                    anchor: str = "start", weight: str = "400", line_gap: int = 20) -> str:
    tspans = []
    for idx, line in enumerate(lines):
        dy = "0" if idx == 0 else str(line_gap)
        tspans.append(
            f'<tspan x="{x}" dy="{dy}">{html_escape(line)}</tspan>'
        )
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{font_size}" '
        f'font-family="Arial, PingFang SC, Microsoft YaHei, sans-serif" '
        f'font-weight="{weight}" fill="{color}">{"".join(tspans)}</text>'
    )


def _svg_card(x: int, y: int, w: int, h: int, title: str, body: str,
              fill: str = "#ffffff", stroke: str = "#cbd5e1", title_fill: str = "#0f172a") -> str:
    body_max_lines = max(6, min(22, int((h - 48) / 13)))
    # 13px 拉丁字母约 6.5–8px 宽；原 w/13 导致每行过短、框内右侧大块留白
    inner_w = max(36, w - 32)
    body_lines = _svg_text_lines(body, max_chars=max(18, int(inner_w / 7.2)), max_lines=body_max_lines)
    return (
        f'<rect x="{x}" y="{y}" rx="16" ry="16" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
        + _svg_text_block(x + 16, y + 28, [title], font_size=15, color=title_fill, weight="700")
        + _svg_text_block(x + 16, y + 52, body_lines, font_size=13, color="#334155", line_gap=15)
    )


def _svg_data_uri(svg: str) -> str:
    return "data:image/svg+xml;charset=utf-8," + quote(svg)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates = []
    windows_dir = os.environ.get("WINDIR", r"C:\Windows")
    font_candidates.extend(
        [
            f"{windows_dir}\\Fonts\\msyh.ttc",
            f"{windows_dir}\\Fonts\\msyhbd.ttc" if bold else f"{windows_dir}\\Fonts\\msyh.ttc",
            f"{windows_dir}\\Fonts\\simhei.ttf",
            f"{windows_dir}\\Fonts\\arialbd.ttf" if bold else f"{windows_dir}\\Fonts\\arial.ttf",
        ]
    )
    for path in font_candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_wrapped_text(draw: ImageDraw.ImageDraw, text: str, box: tuple[int, int, int, int], font: ImageFont.ImageFont,
                       fill: str = "#0f172a", max_lines: int = 4, line_gap: int = 6,
                       line_char_width_px: float = 12.0) -> None:
    x, y, w, h = box
    words = _svg_text_lines(
        text,
        max_chars=max(10, int(w / max(line_char_width_px, 4.0))),
        max_lines=max_lines,
    )
    current_y = y
    for line in words[:max_lines]:
        draw.text((x, current_y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, current_y), line, font=font)
        current_y += (bbox[3] - bbox[1]) + line_gap
        if current_y > y + h:
            break


def _rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str, radius: int = 18, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _png_bytes_from_taxonomy_library_system_map(system_map: Dict[str, Any], record: Dict[str, Any]) -> bytes:
    width, height = 1360, 900
    image = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(image)
    title_font = _load_font(24, bold=True)
    sub_font = _load_font(16, bold=True)
    text_font = _load_font(14)
    small_font = _load_font(12)
    _rounded_rect(draw, (20, 20, 1340, 880), "#ffffff", "#e2e8f0", radius=24)
    draw.text((48, 42), "技术体系定位图", font=title_font, fill="#0f172a")
    draw.text((48, 78), system_map.get("system_label", "技术体系"), font=text_font, fill="#475569")
    draw.text((1040, 46), system_map.get("library_label", "技术体系工程师"), font=text_font, fill="#1d4ed8")
    _draw_wrapped_text(draw, f"论文：{record.get('title', '')}", (48, 102, 1180, 38), small_font, fill="#64748b", max_lines=2)
    _draw_wrapped_text(draw, system_map.get("library_summary", ""), (48, 134, 1240, 34), small_font, fill="#64748b", max_lines=2)
    lanes = system_map.get("taxonomy_lanes") or []
    col_w = 404
    start_x = 48
    top_y = 188
    module_gap = 18
    lane_gap = 18
    for lane_idx, lane in enumerate(lanes[:3]):
        x = start_x + lane_idx * (col_w + lane_gap)
        lane_fill = "#eff6ff" if lane.get("selected") else "#f8fafc"
        lane_outline = "#2563eb" if lane.get("selected") else "#cbd5e1"
        _rounded_rect(draw, (x, top_y, x + col_w, top_y + 560), lane_fill, lane_outline, radius=18)
        draw.text((x + 18, top_y + 16), lane.get("label", ""), font=sub_font, fill="#1e3a8a" if lane.get("selected") else "#0f172a")
        module_y = top_y + 58
        for module in lane.get("modules") or []:
            module_fill = "#ffffff" if not module.get("selected") else "#dbeafe"
            module_outline = "#bfdbfe" if not module.get("selected") else "#2563eb"
            _rounded_rect(draw, (x + 14, module_y, x + col_w - 14, module_y + 228), module_fill, module_outline, radius=16)
            _draw_wrapped_text(draw, module.get("label", ""), (x + 28, module_y + 14, col_w - 56, 28), sub_font, fill="#1d4ed8" if module.get("selected") else "#0f172a", max_lines=2, line_gap=2)
            point_y = module_y + 56
            for point in module.get("points") or []:
                point_fill = "#fee2e2" if point.get("selected") else "#ffffff"
                point_outline = "#ef4444" if point.get("selected") else "#dbeafe"
                text_color = "#b91c1c" if point.get("selected") else "#334155"
                _rounded_rect(draw, (x + 28, point_y, x + col_w - 28, point_y + 42), point_fill, point_outline, radius=12)
                _draw_wrapped_text(draw, point.get("label", ""), (x + 42, point_y + 10, col_w - 84, 24), text_font, fill=text_color, max_lines=2, line_gap=2)
                point_y += 50
            module_y += 228 + module_gap
    _rounded_rect(draw, (48, 770, 1312, 852), "#f8fafc", "#cbd5e1", radius=16)
    draw.text((66, 790), "论文落点", font=sub_font, fill="#0f172a")
    _draw_wrapped_text(draw, " > ".join(part for part in (system_map.get("highlighted_path") or []) if part) or "未定位", (66, 818, 540, 24), text_font, fill="#dc2626", max_lines=2)
    draw.text((700, 790), "证据关键词", font=sub_font, fill="#0f172a")
    _draw_wrapped_text(draw, " / ".join(system_map.get("evidence_terms") or []) or "未抽取到显著关键词", (700, 818, 560, 24), text_font, fill="#475569", max_lines=2)
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _png_bytes_from_system_map(system_map: Dict[str, Any], record: Dict[str, Any]) -> bytes:
    if system_map.get("source_mode") == "taxonomy_library":
        return _png_bytes_from_taxonomy_library_system_map(system_map, record)
    width, height = 1280, 760
    image = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(image)
    title_font = _load_font(24, bold=True)
    sub_font = _load_font(16, bold=True)
    text_font = _load_font(14)
    small_font = _load_font(13)
    _rounded_rect(draw, (20, 20, 1260, 740), "#ffffff", "#e2e8f0", radius=24)
    draw.text((48, 42), "技术体系定位图", font=title_font, fill="#0f172a")
    draw.text((48, 78), system_map.get("system_label", "技术体系"), font=text_font, fill="#475569")
    _draw_wrapped_text(draw, f"论文：{record.get('title', '')}", (48, 102, 1120, 40), small_font, fill="#64748b", max_lines=2)
    path = system_map.get("highlighted_path") or []
    taxonomy_nodes = system_map.get("taxonomy_nodes") or []
    row_y = 156
    row_h = 82
    label_w = 176
    module_w = 228
    module_gap = 14
    for node in taxonomy_nodes:
        layer = node.get("label", "")
        modules = node.get("modules") or []
        layer_active = layer == system_map.get("highlighted_layer")
        _rounded_rect(draw, (48, row_y, 48 + label_w, row_y + 60), "#dbeafe" if layer_active else "#f8fafc", "#2563eb" if layer_active else "#cbd5e1", radius=18)
        _draw_wrapped_text(draw, layer, (64, row_y + 16, label_w - 28, 30), sub_font, fill="#1e3a8a" if layer_active else "#0f172a", max_lines=2, line_gap=2)
        for idx, module in enumerate(modules[:4]):
            x = 48 + label_w + 20 + idx * (module_w + module_gap)
            module_active = module == system_map.get("highlighted_module")
            fill = "#dbeafe" if module_active else "#ffffff"
            outline = "#2563eb" if module_active else "#dbeafe"
            _rounded_rect(draw, (x, row_y, x + module_w, row_y + 60), fill, outline, radius=16)
            _draw_wrapped_text(draw, module, (x + 14, row_y + 12, module_w - 28, 36), text_font, fill="#1d4ed8" if module_active else "#334155", max_lines=2, line_gap=2)
        row_y += row_h
    _rounded_rect(draw, (48, 646, 1232, 720), "#f8fafc", "#cbd5e1", radius=16)
    draw.text((66, 664), "论文落点", font=sub_font, fill="#0f172a")
    _draw_wrapped_text(draw, " > ".join(path) or "未定位", (66, 690, 520, 24), text_font, fill="#2563eb", max_lines=2)
    evidence = system_map.get("evidence_terms") or system_map.get("focus_components") or []
    draw.text((640, 664), "证据关键词", font=sub_font, fill="#0f172a")
    _draw_wrapped_text(draw, " / ".join(evidence[:5]) or "未抽取到显著关键词", (640, 690, 560, 24), text_font, fill="#475569", max_lines=2)
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _png_bytes_from_route_graph(route_graph: Dict[str, Any], record: Dict[str, Any]) -> bytes:
    inner_h, height = _route_graph_inner_and_canvas(route_graph)
    width = _ROUTE_GRAPH_CANVAS_W
    image = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(image)
    title_font = _load_font(24, bold=True)
    sub_font = _load_font(16, bold=True)
    text_font = _load_font(13)
    _rounded_rect(draw, (20, 20, width - 40, inner_h), "#ffffff", "#e2e8f0", radius=24)
    draw.text((44, 42), "技术路线图", font=title_font, fill="#0f172a")
    _draw_wrapped_text(draw, record.get("title", ""), (44, 78, 1160, 40), text_font, fill="#475569", max_lines=2)
    components = route_graph.get("components") or []
    if components:
        draw.text((44, 118), f"关键组件：{' / '.join(components[:4])}", font=text_font, fill="#64748b")
    palette = {
        "problem": ("#fee2e2", "#ef4444"),
        "method": ("#dbeafe", "#3b82f6"),
        "implementation": ("#e0f2fe", "#0ea5e9"),
        "evaluation": ("#ede9fe", "#8b5cf6"),
        "conclusion": ("#dcfce7", "#22c55e"),
    }
    nodes = route_graph.get("nodes") or []
    node_w = _ROUTE_GRAPH_NODE_W
    node_h = _ROUTE_GRAPH_NODE_H
    gap = _ROUTE_GRAPH_NODE_GAP
    start_x = _ROUTE_GRAPH_NODES_X0
    y = _ROUTE_GRAPH_NODES_Y
    body_max_lines = max(6, min(22, int((node_h - 48) / 13)))
    for idx, node in enumerate(nodes[:5]):
        x = start_x + idx * (node_w + gap)
        fill, outline = palette.get(node.get("kind"), ("#f8fafc", "#94a3b8"))
        _rounded_rect(draw, (x, y, x + node_w, y + node_h), fill, outline, radius=16)
        draw.text((x + 16, y + 14), node.get("label", ""), font=sub_font, fill="#0f172a")
        _draw_wrapped_text(
            draw,
            node.get("text", ""),
            (x + 16, y + 44, node_w - 32, node_h - 52),
            text_font,
            fill="#334155",
            max_lines=body_max_lines,
            line_char_width_px=7.2,
        )
        if idx < len(nodes[:5]) - 1:
            line_y = y + node_h // 2
            draw.line((x + node_w + 6, line_y, x + node_w + gap - 10, line_y), fill="#94a3b8", width=3)
            draw.polygon([(x + node_w + gap - 10, line_y), (x + node_w + gap - 22, line_y - 8), (x + node_w + gap - 22, line_y + 8)], fill="#94a3b8")
    method_figure = route_graph.get("method_figure") or {}
    if method_figure:
        mf_y = y + node_h + _ROUTE_GRAPH_METHOD_GAP
        _rounded_rect(draw, (44, mf_y, 1236, mf_y + 52), "#eff6ff", "#bfdbfe", radius=14)
        draw.text((62, mf_y + 16), "方法图说明", font=sub_font, fill="#1e3a8a")
        _draw_wrapped_text(draw, method_figure.get("caption", ""), (190, mf_y + 14, 1020, 34), text_font, fill="#334155", max_lines=2)
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _render_tech_system_map_svg(system_map: Dict[str, Any], record: Dict[str, Any]) -> str:
    if system_map.get("source_mode") == "taxonomy_library":
        width = 1360
        height = 900
        lanes = system_map.get("taxonomy_lanes") or []
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#f8fafc"/>',
            '<rect x="20" y="20" width="1320" height="860" rx="24" ry="24" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>',
            _svg_text_block(48, 58, ["技术体系定位图"], font_size=24, color="#0f172a", weight="700"),
            _svg_text_block(48, 84, _svg_text_lines(system_map.get("system_label", "技术体系"), 28, 2), font_size=15, color="#475569"),
            _svg_text_block(1040, 58, [system_map.get("library_label", "技术体系工程师")], font_size=14, color="#1d4ed8", weight="700"),
            _svg_text_block(48, 120, [f"论文：{record.get('title', '')}"], font_size=13, color="#64748b"),
            _svg_text_block(48, 144, _svg_text_lines(system_map.get("library_summary", ""), 92, 2), font_size=12, color="#64748b"),
        ]
        col_w = 404
        start_x = 48
        top_y = 188
        for lane_idx, lane in enumerate(lanes[:3]):
            x = start_x + lane_idx * (col_w + 18)
            parts.append(
                f'<rect x="{x}" y="{top_y}" rx="18" ry="18" width="{col_w}" height="560" fill="{"#eff6ff" if lane.get("selected") else "#f8fafc"}" stroke="{"#2563eb" if lane.get("selected") else "#cbd5e1"}" stroke-width="2"/>'
            )
            parts.append(_svg_text_block(x + 18, top_y + 30, _svg_text_lines(lane.get("label", ""), 16, 2), font_size=16, color="#1e3a8a" if lane.get("selected") else "#0f172a", weight="700"))
            module_y = top_y + 58
            for module in lane.get("modules") or []:
                parts.append(
                    f'<rect x="{x + 14}" y="{module_y}" rx="16" ry="16" width="{col_w - 28}" height="228" fill="{"#dbeafe" if module.get("selected") else "#ffffff"}" stroke="{"#2563eb" if module.get("selected") else "#bfdbfe"}" stroke-width="2"/>'
                )
                parts.append(_svg_text_block(x + 28, module_y + 28, _svg_text_lines(module.get("label", ""), 22, 2), font_size=15, color="#1d4ed8" if module.get("selected") else "#0f172a", weight="700"))
                point_y = module_y + 56
                for point in module.get("points") or []:
                    parts.append(
                        f'<rect x="{x + 28}" y="{point_y}" rx="12" ry="12" width="{col_w - 56}" height="42" fill="{"#fee2e2" if point.get("selected") else "#ffffff"}" stroke="{"#ef4444" if point.get("selected") else "#dbeafe"}" stroke-width="2"/>'
                    )
                    parts.append(_svg_text_block(x + 42, point_y + 26, _svg_text_lines(point.get("label", ""), 28, 2), font_size=13, color="#b91c1c" if point.get("selected") else "#334155", weight="700" if point.get("selected") else "400"))
                    point_y += 50
                module_y += 246
        parts.append('<rect x="48" y="770" rx="16" ry="16" width="1264" height="82" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>')
        parts.append(_svg_text_block(66, 794, ["论文落点"], font_size=15, color="#0f172a", weight="700"))
        parts.append(_svg_text_block(66, 820, _svg_text_lines(" > ".join(part for part in (system_map.get("highlighted_path") or []) if part), 42, 2), font_size=14, color="#dc2626", weight="700"))
        parts.append(_svg_text_block(700, 794, ["证据关键词"], font_size=15, color="#0f172a", weight="700"))
        parts.append(_svg_text_block(700, 820, _svg_text_lines(" / ".join(system_map.get("evidence_terms") or []), 48, 2), font_size=14, color="#475569"))
        parts.append("</svg>")
        return "".join(parts)
    width = 1280
    height = 760
    title = system_map.get("system_label", "技术体系定位图")
    path = system_map.get("highlighted_path") or []
    taxonomy_nodes = system_map.get("taxonomy_nodes") or []
    evidence_terms = system_map.get("evidence_terms") or system_map.get("focus_components") or []
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<rect x="20" y="20" width="1240" height="720" rx="24" ry="24" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>',
        _svg_text_block(48, 58, ["技术体系定位图"], font_size=24, color="#0f172a", weight="700"),
        _svg_text_block(48, 84, _svg_text_lines(title, 28, 2), font_size=15, color="#475569"),
        _svg_text_block(48, 120, [f"论文：{record.get('title', '')}"], font_size=13, color="#64748b"),
    ]
    row_y = 156
    label_w = 176
    module_w = 228
    module_gap = 14
    for node in taxonomy_nodes:
        root_label = node.get("label", "")
        root_active = root_label == system_map.get("highlighted_layer")
        parts.append(
            f'<rect x="48" y="{row_y}" rx="18" ry="18" width="{label_w}" height="60" '
            f'fill="{"#dbeafe" if root_active else "#f8fafc"}" stroke="{"#2563eb" if root_active else "#cbd5e1"}" stroke-width="2"/>'
        )
        parts.append(_svg_text_block(48 + label_w // 2, row_y + 34, _svg_text_lines(root_label, 10, 2), font_size=16,
                                     color="#1e3a8a" if root_active else "#0f172a", anchor="middle", weight="700"))
        for idx, child in enumerate((node.get("modules") or [])[:4]):
            x = 48 + label_w + 20 + idx * (module_w + module_gap)
            child_active = child == system_map.get("highlighted_module")
            parts.append(
                f'<rect x="{x}" y="{row_y}" rx="14" ry="14" width="{module_w}" height="60" '
                f'fill="{"#eff6ff" if child_active else "#ffffff"}" stroke="{"#60a5fa" if child_active else "#dbeafe"}" stroke-width="2"/>'
            )
            parts.append(_svg_text_block(x + module_w // 2, row_y + 28, _svg_text_lines(child, 12, 2), font_size=13,
                                         color="#1d4ed8" if child_active else "#334155", anchor="middle",
                                         weight="700" if child_active else "400"))
        row_y += 82
    focus_box_x = 48
    focus_box_y = 646
    parts.append(
        f'<rect x="{focus_box_x}" y="{focus_box_y}" rx="16" ry="16" width="1184" height="74" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>'
    )
    parts.append(_svg_text_block(focus_box_x + 18, focus_box_y + 28, ["论文落点"], font_size=15, color="#0f172a", weight="700"))
    parts.append(_svg_text_block(focus_box_x + 18, focus_box_y + 52, [" > ".join(path) or "未定位"], font_size=14, color="#2563eb", weight="700"))
    if evidence_terms:
        parts.append(_svg_text_block(focus_box_x + 640, focus_box_y + 28, ["证据关键词"], font_size=15, color="#0f172a", weight="700"))
        parts.append(_svg_text_block(focus_box_x + 640, focus_box_y + 52, [" / ".join(evidence_terms[:5])], font_size=14, color="#475569"))
    parts.append("</svg>")
    return "".join(parts)


def _render_tech_route_graph_svg(route_graph: Dict[str, Any], record: Dict[str, Any]) -> str:
    width = _ROUTE_GRAPH_CANVAS_W
    inner_h, height = _route_graph_inner_and_canvas(route_graph)
    nodes = route_graph.get("nodes") or []
    components = route_graph.get("components") or []
    node_w = _ROUTE_GRAPH_NODE_W
    node_h = _ROUTE_GRAPH_NODE_H
    gap = _ROUTE_GRAPH_NODE_GAP
    start_x = _ROUTE_GRAPH_NODES_X0
    y = _ROUTE_GRAPH_NODES_Y
    palette = {
        "problem": ("#fee2e2", "#ef4444"),
        "method": ("#dbeafe", "#3b82f6"),
        "implementation": ("#e0f2fe", "#0ea5e9"),
        "evaluation": ("#ede9fe", "#8b5cf6"),
        "conclusion": ("#dcfce7", "#22c55e"),
    }
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        f'<rect x="20" y="20" width="1240" height="{inner_h}" rx="24" ry="24" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>',
        _svg_text_block(44, 56, ["技术路线图"], font_size=24, color="#0f172a", weight="700"),
        _svg_text_block(44, 82, _svg_text_lines(record.get("title", ""), 64, 2), font_size=14, color="#475569"),
    ]
    if components:
        parts.append(_svg_text_block(44, 114, [f"关键组件：{' / '.join(components[:4])}"], font_size=13, color="#64748b"))
    for idx, node in enumerate(nodes[:5]):
        x = start_x + idx * (node_w + gap)
        fill, stroke = palette.get(node.get("kind"), ("#f8fafc", "#94a3b8"))
        parts.append(_svg_card(x, y, node_w, node_h, node.get("label", ""), node.get("text", ""), fill=fill, stroke=stroke, title_fill="#0f172a"))
        if idx < len(nodes[:5]) - 1:
            arrow_x = x + node_w
            next_x = x + node_w + gap
            parts.append(
                f'<line x1="{arrow_x + 6}" y1="{y + node_h / 2}" x2="{next_x - 10}" y2="{y + node_h / 2}" stroke="#94a3b8" stroke-width="3"/>'
                f'<polygon points="{next_x - 10},{y + node_h / 2} {next_x - 22},{y + node_h / 2 - 8} {next_x - 22},{y + node_h / 2 + 8}" fill="#94a3b8"/>'
            )
    method_figure = route_graph.get("method_figure") or {}
    if method_figure:
        mf_y = y + node_h + _ROUTE_GRAPH_METHOD_GAP
        parts.append(
            f'<rect x="44" y="{mf_y}" rx="14" ry="14" width="1192" height="52" fill="#eff6ff" stroke="#bfdbfe" stroke-width="2"/>'
        )
        parts.append(_svg_text_block(62, mf_y + 22, ["方法图说明"], font_size=15, color="#1e3a8a", weight="700"))
        parts.append(
            _svg_text_block(180, mf_y + 22, _svg_text_lines(method_figure.get("caption", ""), 88, 2), font_size=13, color="#334155")
        )
    parts.append("</svg>")
    return "".join(parts)


def _attach_visual_assets(system_map: Dict[str, Any], route_graph: Dict[str, Any], record: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    system_svg = system_map.get("svg") or _render_tech_system_map_svg(system_map, record)
    route_svg = route_graph.get("svg") or _render_tech_route_graph_svg(route_graph, record)
    system_map = dict(system_map)
    route_graph = dict(route_graph)
    system_map.update({
        "svg": system_svg,
        "mime_type": "image/svg+xml",
        "data_uri": _svg_data_uri(system_svg),
    })
    route_graph.update({
        "svg": route_svg,
        "mime_type": "image/svg+xml",
        "data_uri": _svg_data_uri(route_svg),
    })
    return system_map, route_graph


def _enrich_structured_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(record)
    enriched["matched_topics"] = enriched.get("matched_topics") or _ensure_topics(enriched)
    enriched["technical_route"] = enriched.get("technical_route") or _extract_technical_route(enriched.get("summary", ""))
    enriched["core_conclusion"] = enriched.get("core_conclusion") or _extract_conclusion(enriched.get("summary", ""))
    enriched["team_relevance"] = enriched.get("team_relevance") or _team_relevance(enriched)
    system_map = enriched.get("tech_system_map") or _build_tech_system_map(enriched)
    route_graph = enriched.get("tech_route_graph") or _build_tech_route_graph(enriched)
    system_map, route_graph = _attach_visual_assets(system_map, route_graph, enriched)
    enriched["tech_system_map"] = system_map
    enriched["tech_route_graph"] = route_graph
    return enriched


def _extract_hot_terms(records: List[Dict[str, Any]], limit: int = 8) -> List[str]:
    counts: Dict[str, int] = {}
    for record in records:
        text = f"{record.get('title', '')} {record.get('summary', '')}".lower()
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{2,}|[\u4e00-\u9fff]{2,}", text):
            if token in _STOPWORDS:
                continue
            counts[token] = counts.get(token, 0) + 1
    items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _ in items[:limit]]


def _build_trend_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    topic_counts: Dict[str, int] = {}
    route_counts: Dict[str, int] = {}
    for record in records:
        for topic in _ensure_topics(record):
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            route = ROUTE_THEMES.get(topic)
            if route:
                route_counts[route] = route_counts.get(route, 0) + 1
    sorted_topics = sorted(topic_counts.items(), key=lambda item: (-item[1], item[0]))
    sorted_routes = sorted(route_counts.items(), key=lambda item: (-item[1], item[0]))
    team_actions: List[str] = []
    for topic, _ in sorted_topics[:3]:
        rule = TEAM_RELEVANCE.get(topic)
        if not rule:
            continue
        team_actions.append(f"{TOPIC_LABELS.get(topic, topic)}: {rule['suggestion']}")
    return {
        "topic_counts": topic_counts,
        "route_counts": route_counts,
        "hot_topics": [TOPIC_LABELS.get(topic, topic) for topic, _ in sorted_topics[:5]],
        "route_changes": [route for route, _ in sorted_routes[:5]],
        "hot_terms": _extract_hot_terms(records),
        "team_actions": team_actions,
    }


def _display_source(record: Dict[str, Any]) -> str:
    return record.get("source") or "arXiv"


def _display_backend(record: Dict[str, Any]) -> str:
    mapping = {
        "live-rss": "arXiv RSS",
        "live-search-html": "arXiv Search",
        "live-api": "arXiv API",
        "live-scirate": "SciRate",
        "live-openalex": "OpenAlex",
        "live-crossref": "Crossref",
        "cache": "cache",
    }
    return mapping.get(record.get("retrieval_backend", ""), record.get("retrieval_backend", "") or "unknown")


def _build_source_summary(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    source_counts: Dict[str, int] = {}
    backend_counts: Dict[str, int] = {}
    for record in records:
        source = _display_source(record)
        backend = _display_backend(record)
        source_counts[source] = source_counts.get(source, 0) + 1
        backend_counts[backend] = backend_counts.get(backend, 0) + 1
    return {"source_counts": source_counts, "backend_counts": backend_counts}


def _first_author(record: Dict[str, Any]) -> str:
    authors = record.get("authors") or []
    if authors:
        return str(authors[0]).strip()
    corresponding = (record.get("corresponding_author") or "").strip()
    if corresponding:
        return corresponding
    return "源数据未提供"


def _corresponding_author(record: Dict[str, Any]) -> str:
    corresponding = (record.get("corresponding_author") or "").strip()
    if corresponding:
        return corresponding
    authors = record.get("authors") or []
    if authors:
        return str(authors[0]).strip()
    return "源数据未提供"


def _journal_or_venue(record: Dict[str, Any]) -> str:
    for key in ("journal", "venue", "host_venue", "container_title"):
        value = (record.get(key) or "").strip() if isinstance(record.get(key), str) else ""
        if value:
            return value
    source = _display_source(record)
    if source in {"arXiv", "arXiv RSS", "arXiv Search"}:
        primary = (record.get("primary_category") or "").strip()
        return f"arXiv 预印本{f' ({primary})' if primary else ''}"
    return source or "未知"


def _score_record_for_formal_track(record: Dict[str, Any], track_key: str) -> int:
    rule = FORMAL_TRACK_RULES.get(track_key) or {}
    topics = set(record.get("matched_topics") or _ensure_topics(record))
    text = f"{record.get('title', '')} {record.get('summary', '')}".lower()
    title = (record.get("title") or "").lower()
    score = 0
    matched_topics = topics & set(rule.get("topic_ids") or set())
    score += len(matched_topics) * 4
    for term in rule.get("required_terms") or []:
        if term in title:
            score += 3
        elif term in text:
            score += 1
    for term in rule.get("boost_terms") or []:
        if term in title:
            score += 2
        elif term in text:
            score += 1
    if record.get("source") in {"arXiv", "arXiv RSS", "arXiv Search"}:
        score += 1
    return score


def select_formal_track_records(records: List[Dict[str, Any]], track_key: str, limit: int = 4) -> List[Dict[str, Any]]:
    rule = FORMAL_TRACK_RULES.get(track_key)
    if not rule:
        return []
    scored: List[tuple[int, Dict[str, Any]]] = []
    seen: set[str] = set()
    for record in records:
        enriched = _enrich_structured_fields(record)
        title_key = (enriched.get("title") or "").strip().lower()
        if not title_key or title_key in seen:
            continue
        score = _score_record_for_formal_track(enriched, track_key)
        if score < 4:
            continue
        seen.add(title_key)
        scored.append((score, enriched))
    scored.sort(key=lambda item: (-item[0], item[1].get("published", ""), item[1].get("title", "")))
    return [item[1] for item in scored[:limit]]


def build_formal_track_reports(records: List[Dict[str, Any]], report_date: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    reports: Dict[str, Dict[str, Any]] = {}
    for track_key, rule in FORMAL_TRACK_RULES.items():
        selected = select_formal_track_records(records, track_key, limit=min(config.INTEL_MAX_PAPERS, 4))
        if not selected:
            continue
        reports[track_key] = build_report_payload(
            selected,
            report_date=report_date,
            report_id_prefix=f"intel-{track_key}",
            title_cn=rule["title_cn"],
            title_en=rule["title_en"],
            card_title=rule["title_cn"],
            track_key=track_key,
            track_label=rule["label"],
        )
    return reports


def _paper_id_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def _stable_id(prefix: str, raw: str) -> str:
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]}"


def get_report_window(report_at: Optional[datetime] = None) -> tuple[datetime, datetime]:
    end_local = report_at or _local_now()
    start_local = end_local - timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _intel_backend_rank(backend: str) -> int:
    return _INTEL_BACKEND_RANK.get(backend or "", 0)


def _merge_intel_records(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two normalized intel records for the same paper; favor richer metadata and rebuild enrich fields."""
    l_auth, r_auth = left.get("authors") or [], right.get("authors") or []
    l_cor = (left.get("corresponding_author") or "").strip()
    r_cor = (right.get("corresponding_author") or "").strip()
    l_sum = (left.get("summary") or "").strip()
    r_sum = (right.get("summary") or "").strip()
    l_rank = _intel_backend_rank(left.get("retrieval_backend", ""))
    r_rank = _intel_backend_rank(right.get("retrieval_backend", ""))

    l_score = (l_rank, len(l_auth), len(l_sum))
    r_score = (r_rank, len(r_auth), len(r_sum))
    prefer_right_base = r_score >= l_score

    base = copy.deepcopy(right if prefer_right_base else left)

    if len(r_auth) > len(l_auth):
        base["authors"] = list(r_auth)
    elif len(l_auth) > len(r_auth):
        base["authors"] = list(l_auth)
    else:
        base["authors"] = list(r_auth or l_auth)

    base["corresponding_author"] = r_cor or l_cor

    if len(r_sum) > len(l_sum):
        base["summary"] = right.get("summary", "")
        sum_side = "right"
    elif len(l_sum) > len(r_sum):
        base["summary"] = left.get("summary", "")
        sum_side = "left"
    else:
        sum_side = "right" if prefer_right_base else "left"
        base["summary"] = (right.get("summary", "") if sum_side == "right" else left.get("summary", ""))

    title_left = (left.get("title") or "").strip()
    title_right = (right.get("title") or "").strip()
    if sum_side == "right":
        base["title"] = title_right or title_left or (base.get("title") or "").strip()
    else:
        base["title"] = title_left or title_right or (base.get("title") or "").strip()

    url_left = (left.get("arxiv_url") or "").strip()
    url_right = (right.get("arxiv_url") or "").strip()
    base["arxiv_url"] = (url_right if sum_side == "right" else url_left) or url_left or url_right

    base["paper_id"] = (right.get("paper_id") or "").strip() or (left.get("paper_id") or "").strip() or base.get("paper_id", "")
    base["arxiv_id"] = (
        (right.get("arxiv_id") or "").strip() or (left.get("arxiv_id") or "").strip() or base.get("arxiv_id", "")
    )

    pc_r = (right.get("primary_category") or "").strip()
    pc_l = (left.get("primary_category") or "").strip()
    base["primary_category"] = (pc_r if sum_side == "right" else pc_l) or pc_l or pc_r

    src_r = (right.get("source") or "").strip()
    src_l = (left.get("source") or "").strip()
    base["source"] = src_r or src_l

    base["retrieval_backend"] = (
        (right.get("retrieval_backend") or "") if r_rank >= l_rank else (left.get("retrieval_backend") or "")
    ) or "cache"

    base["matched_topics"] = sorted(set(left.get("matched_topics") or []) | set(right.get("matched_topics") or []))
    base["categories"] = list(dict.fromkeys((left.get("categories") or []) + (right.get("categories") or [])))

    lc = left.get("scite_count")
    rc = right.get("scite_count")
    li = lc if isinstance(lc, int) else -1
    ri = rc if isinstance(rc, int) else -1
    if ri >= li and isinstance(rc, int):
        base["scite_count"] = rc
        base["scirate_url"] = (right.get("scirate_url") or "").strip() or (left.get("scirate_url") or "").strip()
    elif isinstance(lc, int):
        base["scite_count"] = lc
        base["scirate_url"] = (left.get("scirate_url") or "").strip() or (right.get("scirate_url") or "").strip()
    elif isinstance(rc, int):
        base["scite_count"] = rc
        base["scirate_url"] = (right.get("scirate_url") or "").strip()

    for key in ("journal", "venue", "container_title"):
        vr, vl = (right.get(key) or "").strip(), (left.get(key) or "").strip()
        base[key] = (vr if sum_side == "right" else vl) or vl or vr

    base["published"] = (right.get("published") or "").strip() or (left.get("published") or "").strip() or base.get("published", "")
    base["updated"] = (right.get("updated") or "").strip() or (left.get("updated") or "").strip() or base.get("updated", "")

    base["window_start"] = left.get("window_start") or right.get("window_start")
    base["window_end"] = left.get("window_end") or right.get("window_end")
    base["ingested_at"] = _now_iso()

    base.pop("tech_system_map", None)
    base.pop("tech_route_graph", None)

    base["technical_route"] = _extract_technical_route(base.get("summary", ""))
    base["core_conclusion"] = _extract_conclusion(base.get("summary", ""))
    base["summary_cn"] = (
        f"研究主题：{base.get('title', '')}。"
        f" 技术路线：{base.get('technical_route') or '基于摘要自动提取，建议人工复核。'}"
        f" 结论：{base.get('core_conclusion') or '基于摘要自动提取，建议人工复核。'}"
    )
    base["importance"] = _importance(base)
    base["team_relevance"] = _team_relevance(base)
    return _enrich_structured_fields(base)


def _intel_merge_into(bucket: Dict[str, Dict[str, Any]], record: Dict[str, Any]) -> None:
    pid = record.get("paper_id") or record.get("arxiv_id")
    if not pid:
        return
    if pid not in bucket:
        bucket[pid] = record
    else:
        bucket[pid] = _merge_intel_records(bucket[pid], record)


def _dedupe_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for record in records:
        paper_id = record.get("paper_id") or record.get("arxiv_id")
        if not paper_id:
            continue
        existing = merged.get(paper_id)
        if existing:
            merged[paper_id] = _merge_intel_records(existing, record)
            continue
        merged[paper_id] = dict(record)
    return list(merged.values())


def _fallback_recent_papers(start_utc: datetime, end_utc: datetime) -> List[Dict[str, Any]]:
    cached = state_store.list_intel_papers(limit=300) or list(_papers_cache.values())
    results: List[Dict[str, Any]] = []
    for record in _dedupe_records(cached):
        published_dt = _safe_parse_dt(record.get("published", ""))
        if not published_dt:
            continue
        if start_utc <= published_dt <= end_utc:
            fallback_record = dict(record)
            fallback_record["retrieval_backend"] = "cache"
            results.append(_enrich_structured_fields(fallback_record))
    results.sort(key=lambda item: item.get("published", ""), reverse=True)
    return results


def _respect_fetch_interval(deadline_monotonic: Optional[float] = None) -> None:
    global _last_fetch_monotonic
    if _fetch_deadline_exceeded(deadline_monotonic):
        raise TimeoutError("intel fetch deadline exceeded before request")
    now = time.monotonic()
    elapsed = now - _last_fetch_monotonic
    if elapsed < FETCH_MIN_INTERVAL_SECONDS:
        delay = FETCH_MIN_INTERVAL_SECONDS - elapsed
        remaining = _fetch_time_left(deadline_monotonic)
        if remaining is not None:
            delay = min(delay, max(0.0, remaining))
        if delay > 0:
            time.sleep(delay)
    _last_fetch_monotonic = time.monotonic()


def _fetch_arxiv_feed(client: httpx.Client, url: str, deadline_monotonic: Optional[float] = None) -> str:
    last_error: Optional[Exception] = None
    for attempt in range(1, FETCH_MAX_RETRIES + 1):
        try:
            if _fetch_deadline_exceeded(deadline_monotonic):
                raise TimeoutError("intel fetch deadline exceeded")
            _respect_fetch_interval(deadline_monotonic)
            resp = client.get(
                url,
                headers={"User-Agent": "QuantaMind/0.1 arxiv-intel"},
                timeout=_bounded_fetch_timeout(deadline_monotonic, INTEL_FETCH_HTTP_TIMEOUT_SECONDS),
            )
            if resp.status_code in RETRYABLE_STATUS_CODES:
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else min(5.0 * attempt, 20.0)
                last_error = httpx.HTTPStatusError(
                    f"retryable status {resp.status_code}",
                    request=resp.request,
                    response=resp,
                )
                _log.warning("arXiv 请求被限流/暂时失败（第 %d/%d 次）: %s，%.1f 秒后重试", attempt, FETCH_MAX_RETRIES, resp.status_code, delay)
                if attempt < FETCH_MAX_RETRIES and not _fetch_deadline_exceeded(deadline_monotonic):
                    time.sleep(delay)
                    continue
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            last_error = e
            if attempt < FETCH_MAX_RETRIES and not _fetch_deadline_exceeded(deadline_monotonic):
                delay = min(4.0 * attempt, 15.0)
                _log.warning("arXiv 抓取失败（第 %d/%d 次）: %s，%.1f 秒后重试", attempt, FETCH_MAX_RETRIES, e, delay)
                time.sleep(delay)
                continue
    raise last_error or RuntimeError("arXiv fetch failed")


def _fetch_json(client: httpx.Client, url: str, params: Dict[str, Any], source_name: str,
                deadline_monotonic: Optional[float] = None) -> Dict[str, Any]:
    last_error: Optional[Exception] = None
    for attempt in range(1, FETCH_MAX_RETRIES + 1):
        try:
            if _fetch_deadline_exceeded(deadline_monotonic):
                raise TimeoutError(f"{source_name} fetch deadline exceeded")
            _respect_fetch_interval(deadline_monotonic)
            resp = client.get(
                url,
                params=params,
                headers={"User-Agent": "QuantaMind/0.1 arxiv-intel"},
                timeout=_bounded_fetch_timeout(deadline_monotonic, INTEL_FETCH_HTTP_TIMEOUT_SECONDS),
            )
            if resp.status_code in RETRYABLE_STATUS_CODES:
                delay = min(5.0 * attempt, 20.0)
                last_error = httpx.HTTPStatusError(
                    f"retryable status {resp.status_code}",
                    request=resp.request,
                    response=resp,
                )
                _log.warning("%s 请求被限流/暂时失败（第 %d/%d 次）: %s，%.1f 秒后重试", source_name, attempt, FETCH_MAX_RETRIES, resp.status_code, delay)
                if attempt < FETCH_MAX_RETRIES and not _fetch_deadline_exceeded(deadline_monotonic):
                    time.sleep(delay)
                    continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            if attempt < FETCH_MAX_RETRIES and not _fetch_deadline_exceeded(deadline_monotonic):
                delay = min(4.0 * attempt, 15.0)
                _log.warning("%s 抓取失败（第 %d/%d 次）: %s，%.1f 秒后重试", source_name, attempt, FETCH_MAX_RETRIES, e, delay)
                time.sleep(delay)
                continue
    raise last_error or RuntimeError(f"{source_name} fetch failed")


def _parse_feed(xml_text: str) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_text)
    records: List[Dict[str, Any]] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        arxiv_url = entry.findtext("atom:id", default="", namespaces=ATOM_NS).strip()
        title = re.sub(r"\s+", " ", entry.findtext("atom:title", default="", namespaces=ATOM_NS)).strip()
        summary = re.sub(r"\s+", " ", entry.findtext("atom:summary", default="", namespaces=ATOM_NS)).strip()
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS).strip()
        updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NS).strip()
        authors = [node.findtext("atom:name", default="", namespaces=ATOM_NS).strip() for node in entry.findall("atom:author", ATOM_NS)]
        categories = [node.attrib.get("term", "") for node in entry.findall("atom:category", ATOM_NS) if node.attrib.get("term")]
        primary = entry.find("arxiv:primary_category", ATOM_NS)
        paper_id = _paper_id_from_url(arxiv_url)
        records.append(
            {
                "paper_id": paper_id,
                "arxiv_id": paper_id,
                "arxiv_url": arxiv_url,
                "title": title,
                "summary": summary,
                "published": published,
                "updated": updated,
                "authors": authors,
                "corresponding_author": "",
                "categories": categories,
                "primary_category": primary.attrib.get("term", "") if primary is not None else (categories[0] if categories else ""),
            }
        )
    return records


def _parse_rss_authors_from_description(description: str) -> List[str]:
    """Fallback when RSS omits dc:creator; arXiv sometimes embeds 'Authors: ...' in HTML description."""
    plain = _strip_html(description or "")
    block = re.search(
        r"Authors:\s*(.+?)(?=\s*Abstract:\s|$)",
        plain,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not block:
        return []
    segment = re.sub(r"\s+", " ", block.group(1)).strip()
    if not segment:
        return []
    parts = re.split(r",|\band\b|;", segment, flags=re.IGNORECASE)
    return [p.strip(" .") for p in parts if p.strip(" .")]


def _parse_rss_feed(xml_text: str) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_text)
    records: List[Dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        link = (item.findtext("link") or "").strip()
        title = re.sub(r"\s+", " ", (item.findtext("title") or "")).strip()
        raw_description = item.findtext("description") or ""
        summary = re.sub(r"\s+", " ", raw_description).strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        categories = [node.text.strip() for node in item.findall("category") if node.text]
        published_dt = _parse_rfc2822_dt(pub_date)
        paper_id = _paper_id_from_url(link) if link else _stable_id("rss", title or summary)
        authors = [
            (node.text or "").strip()
            for node in item.findall(f"{{{DC_NS_URI}}}creator")
            if (node.text or "").strip()
        ]
        if not authors:
            authors = _parse_rss_authors_from_description(raw_description)
        records.append(
            {
                "paper_id": paper_id,
                "arxiv_id": paper_id,
                "arxiv_url": link,
                "title": title,
                "summary": summary,
                "published": published_dt.isoformat().replace("+00:00", "Z") if published_dt else "",
                "updated": published_dt.isoformat().replace("+00:00", "Z") if published_dt else "",
                "authors": authors,
                "corresponding_author": "",
                "categories": categories,
                "primary_category": categories[0] if categories else "",
                "source": "arXiv RSS",
            }
        )
    return records


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html_unescape(clean)).strip()


def _parse_search_result_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%d %B, %Y").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _extract_first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_arxiv_search_html(html_text: str) -> List[Dict[str, Any]]:
    blocks = re.findall(
        r'<li class="arxiv-result">(.*?)</li>\s*(?=<li class="arxiv-result"|</ol>)',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    records: List[Dict[str, Any]] = []
    for block in blocks:
        url = _extract_first(r'<p class="list-title is-inline-block">.*?<a href="([^"]+)"', block)
        title = _strip_html(_extract_first(r'<p class="title is-5 mathjax">\s*(.*?)\s*</p>', block))
        summary = _strip_html(
            _extract_first(
                r'<span class="abstract-full has-text-grey-dark mathjax"[^>]*>(.*?)</span>',
                block,
            )
        )
        summary = re.sub(r"^\s*Abstract:\s*", "", summary, flags=re.IGNORECASE)
        authors = [
            _strip_html(name)
            for name in re.findall(
                r'<a href="/search/[^"]+">([^<]+)</a>',
                _extract_first(r'<p class="authors">\s*(.*?)\s*</p>', block),
                flags=re.IGNORECASE | re.DOTALL,
            )
            if _strip_html(name)
        ]
        categories = [
            token
            for token in (
                _strip_html(value)
                for value in re.findall(
                    r'<span class="tag[^"]*is-link[^"]*">(.*?)</span>',
                    block,
                    flags=re.IGNORECASE | re.DOTALL,
                )
            )
            if token
        ]
        submitted = _extract_first(r"Submitted\s+(\d{1,2}\s+[A-Za-z]+,\s+\d{4})", block)
        published_dt = _parse_search_result_date(submitted)
        paper_id = _paper_id_from_url(url) if url else _stable_id("search", title or summary)
        records.append(
            {
                "paper_id": paper_id,
                "arxiv_id": paper_id if url and "arxiv.org" in url else "",
                "arxiv_url": url,
                "title": title,
                "summary": summary,
                "published": published_dt.isoformat().replace("+00:00", "Z") if published_dt else "",
                "updated": published_dt.isoformat().replace("+00:00", "Z") if published_dt else "",
                "authors": authors,
                "corresponding_author": "",
                "categories": categories,
                "primary_category": categories[0] if categories else "",
                "source": "arXiv Search",
            }
        )
    return records


def _parse_crossref_items(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = ((data or {}).get("message") or {}).get("items") or []
    records: List[Dict[str, Any]] = []
    for item in items:
        title = " ".join(item.get("title") or []).strip()
        abstract = _strip_html(item.get("abstract") or "")
        doi = (item.get("DOI") or "").strip()
        url = (item.get("URL") or "").strip() or (f"https://doi.org/{doi}" if doi else "")
        created_parts = (((item.get("created") or {}).get("date-parts") or [[None, None, None]])[0])[:3]
        if created_parts and created_parts[0]:
            year = int(created_parts[0])
            month = int(created_parts[1] or 1)
            day = int(created_parts[2] or 1)
            created_dt = datetime(year, month, day, tzinfo=timezone.utc)
            published = created_dt.isoformat().replace("+00:00", "Z")
        else:
            published = ""
        authors = []
        corresponding_author = ""
        for author in item.get("author") or []:
            name = " ".join(part for part in [author.get("given"), author.get("family")] if part)
            if name:
                authors.append(name)
            if not corresponding_author and author.get("sequence") == "first":
                corresponding_author = name
        categories = [str(s) for s in (item.get("subject") or []) if s]
        container_title = " ".join(item.get("container-title") or []).strip()
        records.append(
            {
                "paper_id": _stable_id("cr", doi or title or url),
                "arxiv_id": "",
                "arxiv_url": url,
                "title": title,
                "summary": abstract,
                "published": published,
                "updated": published,
                "authors": authors,
                "corresponding_author": corresponding_author,
                "container_title": container_title,
                "journal": container_title,
                "categories": categories,
                "primary_category": categories[0] if categories else "",
                "source": "Crossref",
            }
        )
    return records


def _openalex_abstract(index: Dict[str, List[int]]) -> str:
    if not isinstance(index, dict):
        return ""
    positions: Dict[int, str] = {}
    for token, slots in index.items():
        for pos in slots or []:
            positions[int(pos)] = token
    if not positions:
        return ""
    return " ".join(positions[idx] for idx in sorted(positions))


def _parse_openalex_items(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = (data or {}).get("results") or []
    records: List[Dict[str, Any]] = []
    for item in items:
        title = (item.get("display_name") or "").strip()
        abstract = _openalex_abstract(item.get("abstract_inverted_index") or {})
        doi = (item.get("doi") or "").strip()
        primary_location = item.get("primary_location") or {}
        url = (
            (primary_location.get("landing_page_url") or "").strip()
            or (item.get("id") or "").strip()
            or doi
        )
        publication_date = (item.get("publication_date") or "").strip()
        published = f"{publication_date}T00:00:00Z" if publication_date else ""
        source_info = (primary_location.get("source") or {}) if isinstance(primary_location, dict) else {}
        venue = (source_info.get("display_name") or "").strip()
        authors = []
        corresponding_author = ""
        for authorship in item.get("authorships") or []:
            author = authorship.get("author") or {}
            name = (author.get("display_name") or "").strip()
            if name:
                authors.append(name)
            if not corresponding_author and authorship.get("is_corresponding"):
                corresponding_author = name
        categories = []
        primary_topic = item.get("primary_topic") or {}
        if primary_topic.get("display_name"):
            categories.append(str(primary_topic["display_name"]))
        for concept in item.get("concepts") or []:
            name = (concept.get("display_name") or "").strip()
            if name and name not in categories:
                categories.append(name)
        records.append(
            {
                "paper_id": _stable_id("oa", str(item.get("id") or doi or title or url)),
                "arxiv_id": "",
                "arxiv_url": url,
                "title": title,
                "summary": abstract,
                "published": published,
                "updated": published,
                "authors": authors,
                "corresponding_author": corresponding_author,
                "venue": venue,
                "journal": venue,
                "categories": categories,
                "primary_category": categories[0] if categories else "",
                "source": "OpenAlex",
            }
        )
    return records


def _has_quantum_context(record: Dict[str, Any]) -> bool:
    text = " ".join(
        [
            record.get("title", ""),
            record.get("summary", ""),
        ]
    ).lower()
    categories = " ".join(record.get("categories", [])).lower()
    if any(token in text for token in NEGATIVE_NOISE_TERMS):
        return False
    anchors = [
        "quantum",
        "qubit",
        "superconduct",
        "transmon",
        "josephson",
        "surface code",
        "fault-tolerant",
        "readout",
        "qec",
        "large language model",
        "llm",
        "agent",
        "ai agent",
        "multi-agent",
        "agentic",
        "tool use",
        "reasoning model",
    ]
    if any(token in text for token in anchors):
        return True
    if any(cat in categories for cat in ("quant-ph", "cond-mat.supr-con", "cs.ai", "cs.lg")):
        return True
    return False


def _normalize_live_record(record: Dict[str, Any], start_utc: datetime, end_utc: datetime, backend: str) -> Optional[Dict[str, Any]]:
    published_dt = _safe_parse_dt(record.get("published", ""))
    if not published_dt or published_dt < start_utc or published_dt > end_utc:
        return None
    normalized = dict(record)
    if not _has_quantum_context(normalized):
        return None
    normalized["matched_topics"] = _ensure_topics(normalized)
    if not normalized["matched_topics"]:
        return None
    normalized["technical_route"] = _extract_technical_route(normalized.get("summary", ""))
    normalized["core_conclusion"] = _extract_conclusion(normalized.get("summary", ""))
    normalized["summary_cn"] = (
        f"研究主题：{normalized.get('title', '')}。"
        f" 技术路线：{normalized.get('technical_route') or '基于摘要自动提取，建议人工复核。'}"
        f" 结论：{normalized.get('core_conclusion') or '基于摘要自动提取，建议人工复核。'}"
    )
    normalized["importance"] = _importance(normalized)
    normalized["team_relevance"] = _team_relevance(normalized)
    normalized["ingested_at"] = _now_iso()
    normalized["window_start"] = start_utc.isoformat().replace("+00:00", "Z")
    normalized["window_end"] = end_utc.isoformat().replace("+00:00", "Z")
    normalized["retrieval_backend"] = backend
    return _enrich_structured_fields(normalized)


def _fetch_rss_recent_papers(client: httpx.Client, start_utc: datetime, end_utc: datetime,
                            deadline_monotonic: Optional[float] = None) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for url in ARXIV_RSS_FEEDS:
        if _fetch_deadline_exceeded(deadline_monotonic):
            _log.warning("RSS 抓取超出时间预算，提前结束")
            break
        try:
            parsed = _parse_rss_feed(_fetch_arxiv_feed(client, url, deadline_monotonic=deadline_monotonic))
        except Exception as e:
            _log.warning("arXiv RSS 抓取失败 [%s]: %s", url, e)
            continue
        for record in parsed:
            normalized = _normalize_live_record(record, start_utc, end_utc, backend="live-rss")
            if not normalized:
                continue
            _intel_merge_into(merged, normalized)
    return sorted(merged.values(), key=lambda item: item.get("published", ""), reverse=True)


def _fetch_search_recent_papers(client: httpx.Client, start_utc: datetime, end_utc: datetime, size: int = 100,
                               deadline_monotonic: Optional[float] = None) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    page_size = 25 if size <= 25 else (50 if size <= 50 else 100)
    for term in ARXIV_SEARCH_TERMS:
        if _fetch_deadline_exceeded(deadline_monotonic):
            _log.warning("Search HTML 抓取超出时间预算，提前结束")
            break
        params = {
            "query": term,
            "searchtype": "all",
            "abstracts": "show",
            "order": "-announced_date_first",
            "size": page_size,
        }
        url = f"{ARXIV_SEARCH_URL}?{urlencode(params)}"
        try:
            parsed = _parse_arxiv_search_html(_fetch_arxiv_feed(client, url, deadline_monotonic=deadline_monotonic))
        except Exception as e:
            _log.warning("arXiv Search 页面抓取失败 [%s]: %s", term, e)
            continue
        for record in parsed:
            normalized = _normalize_live_record(record, start_utc, end_utc, backend="live-search-html")
            if not normalized:
                continue
            _intel_merge_into(merged, normalized)
    return sorted(merged.values(), key=lambda item: item.get("published", ""), reverse=True)


def _fetch_openalex_recent_papers(client: httpx.Client, start_utc: datetime, end_utc: datetime, per_page: int = 25,
                                 deadline_monotonic: Optional[float] = None) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    page_size = max(10, min(per_page, 50))
    for term in ARXIV_SEARCH_TERMS:
        if _fetch_deadline_exceeded(deadline_monotonic):
            _log.warning("OpenAlex 抓取超出时间预算，提前结束")
            break
        params = {
            "search": term,
            "filter": f"from_publication_date:{start_utc.date().isoformat()},to_publication_date:{end_utc.date().isoformat()}",
            "sort": "publication_date:desc",
            "per-page": page_size,
            "mailto": "quantamind@example.local",
        }
        try:
            data = _fetch_json(client, OPENALEX_API_URL, params, "OpenAlex", deadline_monotonic=deadline_monotonic)
        except Exception as e:
            _log.warning("OpenAlex 查询失败 [%s]: %s", term, e)
            continue
        for record in _parse_openalex_items(data):
            normalized = _normalize_live_record(record, start_utc, end_utc, backend="live-openalex")
            if not normalized:
                continue
            _intel_merge_into(merged, normalized)
    return sorted(merged.values(), key=lambda item: item.get("published", ""), reverse=True)


def _fetch_crossref_recent_papers(client: httpx.Client, start_utc: datetime, end_utc: datetime, rows: int = 30,
                                 deadline_monotonic: Optional[float] = None) -> List[Dict[str, Any]]:
    params = {
        "query": "quantum qubit superconducting transmon surface code error correction readout calibration",
        "filter": f"from-created-date:{start_utc.date().isoformat()},until-created-date:{end_utc.date().isoformat()}",
        "sort": "published",
        "order": "desc",
        "rows": rows,
        "mailto": "quantamind@example.local",
    }
    try:
        data = _fetch_json(client, CROSSREF_API_URL, params, "Crossref", deadline_monotonic=deadline_monotonic)
    except Exception as e:
        _log.warning("Crossref 查询失败: %s", e)
        return []
    merged: Dict[str, Dict[str, Any]] = {}
    for record in _parse_crossref_items(data):
        normalized = _normalize_live_record(record, start_utc, end_utc, backend="live-crossref")
        if not normalized:
            continue
        _intel_merge_into(merged, normalized)
    return sorted(merged.values(), key=lambda item: item.get("published", ""), reverse=True)


def _scirate_range_query() -> str:
    v = (os.environ.get("QUANTAMIND_SCIRATE_RANGE") or "1d").strip()
    return v if v else "1d"


def _split_scirate_paper_chunks(html: str) -> List[str]:
    starts = [m.start() for m in re.finditer(r'<li class="paper[^"]*">', html, flags=re.IGNORECASE)]
    if not starts:
        return []
    chunks: List[str] = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(html)
        chunks.append(html[s:e])
    return chunks


def _parse_scirate_uid_published(chunk: str) -> str:
    m = re.search(r'<div class="uid">\s*([A-Za-z]{3}\s+\d{1,2}\s+\d{4})', chunk)
    if not m:
        return ""
    try:
        dt = datetime.strptime(m.group(1).strip(), "%b %d %Y").replace(
            hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
        )
        return dt.isoformat().replace("+00:00", "Z")
    except Exception:
        return ""


def _parse_scirate_authors_chunk(chunk: str) -> List[str]:
    m = re.search(r'<div class="authors">(.*?)</div>', chunk, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    text = _strip_html(m.group(1))
    parts = re.split(r"[,;]", text)
    return [p.strip() for p in parts if p.strip()]


def _parse_scirate_paper_chunk(chunk: str, feed_category: str) -> Optional[Dict[str, Any]]:
    uid_m = re.search(r'data-paper-uid="(\d{4}\.\d{5})"', chunk)
    title_m = re.search(
        r'<div class="title">\s*<a href="/arxiv/\d{4}\.\d{5}(?:v\d+)?[^"]*">([^<]+)</a>',
        chunk,
        flags=re.IGNORECASE,
    )
    arxiv_m = re.search(r'href="/arxiv/(\d{4}\.\d{5})(?:v\d+)?"', chunk)
    paper_id = (uid_m.group(1) if uid_m else "") or (arxiv_m.group(1) if arxiv_m else "")
    if not paper_id:
        return None
    title = _strip_html(title_m.group(1)) if title_m else ""
    scite_m = re.search(
        r'<div class="scites-count">[\s\S]*?class="btn btn-default count">(\d+)</button>',
        chunk,
        flags=re.IGNORECASE,
    )
    scite_count = int(scite_m.group(1)) if scite_m else 0
    abs_m = re.search(r'<div class="abstract">(.*?)</div>', chunk, flags=re.DOTALL | re.IGNORECASE)
    summary = _strip_html(abs_m.group(1)) if abs_m else ""
    published = _parse_scirate_uid_published(chunk)
    authors = _parse_scirate_authors_chunk(chunk)
    return {
        "paper_id": paper_id,
        "arxiv_id": paper_id,
        "arxiv_url": f"https://arxiv.org/abs/{paper_id}",
        "scirate_url": f"{SCIRATE_BASE_URL}/arxiv/{paper_id}",
        "title": title or f"arXiv:{paper_id}",
        "summary": summary,
        "published": published,
        "updated": published,
        "authors": authors,
        "corresponding_author": "",
        "categories": [feed_category],
        "primary_category": feed_category,
        "source": "SciRate",
        "scite_count": scite_count,
    }


def _parse_scirate_listing(html: str, feed_category: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for chunk in _split_scirate_paper_chunks(html):
        rec = _parse_scirate_paper_chunk(chunk, feed_category)
        if rec:
            out.append(rec)
    return out


def _fetch_scirate_recent_papers(client: httpx.Client, start_utc: datetime, end_utc: datetime,
                                deadline_monotonic: Optional[float] = None) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    rparam = _scirate_range_query()
    for category in SCIRATE_ARXIV_CATEGORIES:
        if _fetch_deadline_exceeded(deadline_monotonic):
            _log.warning("SciRate 抓取超出时间预算，提前结束")
            break
        url = f"{SCIRATE_BASE_URL}/arxiv/{category}"
        try:
            _respect_fetch_interval(deadline_monotonic)
            resp = client.get(
                url,
                params={"range": rparam},
                headers={"User-Agent": "QuantaMind/0.1 (arxiv-intel; scirate)"},
                timeout=_bounded_fetch_timeout(deadline_monotonic, INTEL_FETCH_HTTP_TIMEOUT_SECONDS),
            )
            resp.raise_for_status()
            for record in _parse_scirate_listing(resp.text, category):
                normalized = _normalize_live_record(record, start_utc, end_utc, backend="live-scirate")
                if not normalized:
                    continue
                _intel_merge_into(merged, normalized)
        except Exception as e:
            _log.warning("SciRate 抓取失败 [%s]: %s", category, e)
            continue
    return sorted(merged.values(), key=lambda item: item.get("published", ""), reverse=True)


def fetch_recent_papers(days_back: Optional[int] = None,
                        max_per_topic: int = 8,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        max_runtime_seconds: Optional[float] = INTEL_FETCH_SOFT_LIMIT_SECONDS) -> List[Dict[str, Any]]:
    if start_time or end_time:
        start_utc = start_time.astimezone(timezone.utc) if start_time else datetime.min.replace(tzinfo=timezone.utc)
        end_utc = end_time.astimezone(timezone.utc) if end_time else datetime.now(timezone.utc)
    else:
        start_utc = datetime.now(timezone.utc) - timedelta(days=days_back or config.INTEL_LOOKBACK_DAYS)
        end_utc = datetime.now(timezone.utc)
    deadline_monotonic = time.monotonic() + max_runtime_seconds if max_runtime_seconds else None
    with httpx.Client(timeout=INTEL_FETCH_HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
        merged: Dict[str, Dict[str, Any]] = {}

        rss_records = _fetch_rss_recent_papers(client, start_utc, end_utc, deadline_monotonic=deadline_monotonic)
        for record in rss_records:
            _intel_merge_into(merged, record)

        if _fetch_deadline_exceeded(deadline_monotonic):
            _log.warning("情报实时抓取达到时间预算，使用当前结果提前结束")
            results = sorted(_dedupe_records(list(merged.values())), key=lambda item: item.get("published", ""), reverse=True)
            return results or _fallback_recent_papers(start_utc, end_utc)

        search_records = _fetch_search_recent_papers(
            client,
            start_utc,
            end_utc,
            size=min(max_per_topic * len(TOPIC_QUERIES) * 3, 100),
            deadline_monotonic=deadline_monotonic,
        )
        for record in search_records:
            _intel_merge_into(merged, record)

        if _fetch_deadline_exceeded(deadline_monotonic):
            _log.warning("情报实时抓取达到时间预算，使用 RSS/Search 当前结果提前结束")
            results = sorted(_dedupe_records(list(merged.values())), key=lambda item: item.get("published", ""), reverse=True)
            return results or _fallback_recent_papers(start_utc, end_utc)

        for record in _fetch_scirate_recent_papers(client, start_utc, end_utc, deadline_monotonic=deadline_monotonic):
            _intel_merge_into(merged, record)

        combined_query = " OR ".join(f"({topic['query']})" for topic in TOPIC_QUERIES)
        params = {
            "search_query": f"({SEARCH_BASE_QUERY}) OR ({combined_query})",
            "start": 0,
            "max_results": min(max_per_topic * len(TOPIC_QUERIES) * 2, 100),
            "sortBy": "lastUpdatedDate",
            "sortOrder": "descending",
        }
        url = f"{ARXIV_API_URL}?{urlencode(params)}"
        try:
            parsed = _parse_feed(_fetch_arxiv_feed(client, url, deadline_monotonic=deadline_monotonic))
        except Exception as e:
            _log.warning("arXiv 联合查询失败，尝试其他渠道/缓存: %s", e)
            parsed = []

        for record in parsed:
            normalized = _normalize_live_record({**record, "source": "arXiv"}, start_utc, end_utc, backend="live-api")
            if not normalized:
                continue
            _intel_merge_into(merged, normalized)

        if _fetch_deadline_exceeded(deadline_monotonic):
            _log.warning("情报实时抓取达到时间预算，跳过联合查询后续后端")
            results = sorted(_dedupe_records(list(merged.values())), key=lambda item: item.get("published", ""), reverse=True)
            return results or _fallback_recent_papers(start_utc, end_utc)

        openalex_records = _fetch_openalex_recent_papers(
            client,
            start_utc,
            end_utc,
            per_page=min(max_per_topic * 2, 25),
            deadline_monotonic=deadline_monotonic,
        )
        for record in openalex_records:
            _intel_merge_into(merged, record)

        if len(merged) < max(6, max_per_topic) and not _fetch_deadline_exceeded(deadline_monotonic):
            crossref_records = _fetch_crossref_recent_papers(
                client,
                start_utc,
                end_utc,
                deadline_monotonic=deadline_monotonic,
            )
            for record in crossref_records:
                _intel_merge_into(merged, record)

    results = sorted(_dedupe_records(list(merged.values())), key=lambda item: item.get("published", ""), reverse=True)
    return results or _fallback_recent_papers(start_utc, end_utc)


def persist_paper(record: Dict[str, Any]) -> Dict[str, Any]:
    record = _enrich_structured_fields(record)
    _papers_cache[record["paper_id"]] = record
    try:
        state_store.upsert_intel_paper(record["paper_id"], record)
    except Exception as e:
        _log.warning("保存情报论文失败 %s: %s", record["paper_id"], e)
    keywords = list(dict.fromkeys(record.get("matched_topics", []) + record.get("categories", [])))[:16]
    kb_parts = [
        f"Title: {record['title']}",
        f"Authors: {', '.join(record.get('authors', []))}",
        f"Topics: {', '.join(record.get('matched_topics', []))}",
        f"Technical route: {record.get('technical_route', '')}",
        f"Conclusion: {record.get('core_conclusion', '')}",
        f"Tech system path: {' > '.join(record.get('tech_system_map', {}).get('highlighted_path', []))}",
        f"Abstract: {record.get('summary', '')}",
        f"URL: {record.get('arxiv_url', '')}",
    ]
    if isinstance(record.get("scite_count"), int):
        kb_parts.append(f"SciRate scite: {record['scite_count']}")
        if (record.get("scirate_url") or "").strip():
            kb_parts.append(f"SciRate URL: {record['scirate_url']}")
    return knowledge_base.index_external_record(
        record_id=f"paper_{record['paper_id']}",
        source=f"arxiv:{record['paper_id']}",
        title=record["title"],
        content="\n\n".join(kb_parts),
        keywords=keywords,
    )


def warm_recent_cache(days_back: Optional[int] = None, max_per_topic: int = 6) -> Dict[str, Any]:
    records = fetch_recent_papers(days_back=days_back or config.INTEL_LOOKBACK_DAYS, max_per_topic=max_per_topic)
    live_records = [record for record in records if record.get("retrieval_backend") != "cache"]
    for record in live_records:
        persist_paper(record)
    return {
        "status": "warmed" if live_records else "cache_only",
        "records_count": len(records),
        "live_records_count": len(live_records),
        "backends": _build_source_summary(records).get("backend_counts", {}),
    }


def build_report_payload(records: List[Dict[str, Any]],
                         report_date: Optional[str] = None,
                         report_id_prefix: str = "intel",
                         title_cn: str = "QuantaMind 情报日报",
                         title_en: str = "QuantaMind Intel Daily Brief",
                         card_title: Optional[str] = None,
                         track_key: Optional[str] = None,
                         track_label: Optional[str] = None) -> Dict[str, Any]:
    report_day = report_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    records = [_enrich_structured_fields(record) for record in records]
    top_records = records[: config.INTEL_MAX_PAPERS]
    window_start, window_end = get_report_window()
    trend_summary = _build_trend_summary(top_records)
    source_summary = _build_source_summary(records)
    topic_counts = trend_summary["topic_counts"]
    report_id = f"{report_id_prefix}-{report_day}"
    body_lines = [
        f"{title_cn} {report_day}",
        title_en,
        f"检索窗口：{window_start.astimezone().strftime('%Y-%m-%d %H:%M')} 至 {window_end.astimezone().strftime('%Y-%m-%d %H:%M')}",
        f"共检索到 {len(records)} 篇近 24 小时新论文，精选 {len(top_records)} 篇。",
        f"来源分布：{', '.join(f'{k} {v}篇' for k, v in source_summary['source_counts'].items()) or '暂无'}",
        f"检索通道：{', '.join(f'{k} {v}篇' for k, v in source_summary['backend_counts'].items()) or '暂无'}",
        f"热点主题：{', '.join(trend_summary['hot_topics']) or '暂无'}",
        f"技术路线变化：{', '.join(trend_summary['route_changes']) or '暂无'}",
        f"热点关键词：{', '.join(trend_summary['hot_terms']) or '暂无'}",
    ]
    if trend_summary["team_actions"]:
        body_lines.append("团队建议：\n- " + "\n- ".join(trend_summary["team_actions"][:4]))
    for idx, record in enumerate(top_records, start=1):
        scite_extra = ""
        if isinstance(record.get("scite_count"), int):
            scite_extra = f"\n   SciRate scite: {record['scite_count']}"
            if (record.get("scirate_url") or "").strip():
                scite_extra += f" · {record['scirate_url']}"
        body_lines.append(
            f"{idx}. {record['title']}\n"
            f"   主题: {', '.join(TOPIC_LABELS.get(topic, topic) for topic in record.get('matched_topics', [])) or '未分类'}\n"
            f"   来源: {_display_source(record)} / {_display_backend(record)}{scite_extra}\n"
            f"   技术路线: {record.get('technical_route', '') or '待人工复核'}\n"
            f"   结论: {record.get('core_conclusion', '') or '待人工复核'}\n"
            f"   对团队启发: {(record.get('team_relevance') or {}).get('suggestion', '待知识工程师复核')}\n"
            f"   链接: {record.get('arxiv_url', '')}"
        )
    return {
        "report_id": report_id,
        "report_date": report_day,
        "created_at": _now_iso(),
        "papers_count": len(records),
        "window_start": window_start.isoformat().replace("+00:00", "Z"),
        "window_end": window_end.isoformat().replace("+00:00", "Z"),
        "top_papers": top_records,
        "topic_counts": topic_counts,
        "trend_summary": trend_summary,
        "source_summary": source_summary,
        "card_title": card_title or title_cn,
        "title_cn": title_cn,
        "title_en": title_en,
        "track_key": track_key,
        "track_label": track_label,
        "delivery": {"feishu": {"status": "pending" if config.INTEL_FEISHU_WEBHOOK else "skipped", "reason": ""}},
        "text": "\n\n".join(body_lines),
    }


def _shorten_text(text: str, limit: int = 240) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(limit - 1, 1)].rstrip() + "..."


def _build_zh_brief(record: Dict[str, Any]) -> str:
    return _shorten_text(
        record.get("summary_cn")
        or (
            f"研究主题：{record.get('title', '')}。"
            f" 技术路线：{record.get('technical_route') or '基于摘要自动提取，建议人工复核。'}"
            f" 结论：{record.get('core_conclusion') or '基于摘要自动提取，建议人工复核。'}"
        ),
        limit=220,
    )


def _build_en_abstract(record: Dict[str, Any]) -> str:
    return _shorten_text(record.get("summary") or _build_en_brief(record), limit=320)


def _build_en_brief(record: Dict[str, Any]) -> str:
    return _shorten_text(
        (
            f"Topic: {record.get('title', '')}. "
            f"Technical route: {record.get('technical_route') or 'Auto-extracted from abstract; manual review recommended.'} "
            f"Conclusion: {record.get('core_conclusion') or 'Auto-extracted from abstract; manual review recommended.'}"
        ),
        limit=260,
    )


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _clean_translation_text(text: str) -> str:
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^\s*```(?:json|text)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    cleaned = re.sub(r"^(?:title_zh|summary_zh|标题翻译|摘要翻译|中文标题|中文摘要)\s*[:：]\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip().strip('"').strip("'")


def _is_valid_zh_translation(source_text: str, translated_text: str) -> bool:
    source = re.sub(r"\s+", " ", source_text or "").strip().lower()
    translated = re.sub(r"\s+", " ", translated_text or "").strip()
    if not translated or not _contains_chinese(translated):
        return False
    if translated.lower() == source:
        return False
    return True


async def _translate_text_once_async(text: str, kind: str, retry: bool = False) -> str:
    from quantamind.server.brain import get_brain
    from quantamind.shared.api import ChatMessage, MessageRole

    if not (text or "").strip():
        return ""
    if kind == "title":
        task_desc = "Translate this English quantum paper title into accurate Simplified Chinese."
        rules = "Do not summarize. Preserve technical meaning and acronyms like TLS, CZ, QEC, Ramsey, transmon."
    else:
        task_desc = "Translate this English quantum paper abstract into accurate Simplified Chinese."
        rules = "Do not summarize, compress, or explain. Preserve technical details, formulas, and acronyms."
    retry_hint = (
        "Your previous answer did not satisfy the requirement because it was not Chinese translation. "
        "Output only the final Simplified Chinese translation."
        if retry
        else "Output only the final Simplified Chinese translation."
    )
    messages = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content=(
                "You are a professional translator for quantum computing and superconducting qubit research papers. "
                "You only translate, never summarize."
            ),
        ),
        ChatMessage(
            role=MessageRole.USER,
            content=f"{task_desc}\n{rules}\n{retry_hint}\n\nSource text:\n{text}",
        ),
    ]
    brain = get_brain()
    chunks: List[str] = []
    async for chunk in brain.chat(messages, stream=False):
        chunks.append(chunk)
    return _clean_translation_text("".join(chunks))


async def _translate_record_async(record: Dict[str, Any]) -> Dict[str, str]:
    cache_key = record.get("paper_id") or record.get("arxiv_url") or record.get("title") or ""
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
    source_title = (record.get("title") or "").strip()
    source_summary = (record.get("summary") or "").strip()
    translated = {
        "title_zh": "（标题翻译暂不可用，请查看下方英文标题）" if source_title else "",
        "summary_zh": "（摘要翻译暂不可用，请查看下方英文摘要）" if source_summary else "",
    }
    try:
        title_zh = await _translate_text_once_async(source_title, "title", retry=False)
        if not _is_valid_zh_translation(source_title, title_zh):
            title_zh = await _translate_text_once_async(source_title, "title", retry=True)
        if _is_valid_zh_translation(source_title, title_zh):
            translated["title_zh"] = _shorten_text(title_zh, 160)
        summary_zh = await _translate_text_once_async(source_summary, "abstract", retry=False)
        if not _is_valid_zh_translation(source_summary, summary_zh):
            summary_zh = await _translate_text_once_async(source_summary, "abstract", retry=True)
        if _is_valid_zh_translation(source_summary, summary_zh):
            translated["summary_zh"] = _shorten_text(summary_zh, 260)
    except Exception as e:
        _log.warning("论文翻译失败，回退占位文本: %s", e)
    _translation_cache[cache_key] = translated
    return translated


def _translate_record(record: Dict[str, Any]) -> Dict[str, str]:
    try:
        return asyncio.run(_translate_record_async(record))
    except Exception as e:
        _log.warning("论文翻译失败，回退原文: %s", e)
        return {
            "title_zh": "（标题翻译暂不可用，请查看下方英文标题）" if record.get("title") else "",
            "summary_zh": "（摘要翻译暂不可用，请查看下方英文摘要）" if record.get("summary") else "",
        }


def build_bilingual_digest_text(records: List[Dict[str, Any]],
                                window_start: Optional[datetime] = None,
                                window_end: Optional[datetime] = None,
                                source_note: str = "",
                                max_items: int = 5,
                                title_cn: str = "QuantaMind 情报员周报",
                                title_en: str = "QuantaMind Weekly Intel Brief") -> str:
    selected = records[:max_items]
    start_label = window_start.astimezone().strftime("%Y-%m-%d") if window_start else "—"
    end_label = window_end.astimezone().strftime("%Y-%m-%d") if window_end else "—"
    lines = [
        title_cn,
        title_en,
        f"时间范围 / Window: {start_label} 至 {end_label}",
        f"来源说明 / Source note: {source_note or 'Multi-source intel pipeline'}",
        f"重点论文 / Highlight papers: {len(selected)}",
        "",
    ]
    for idx, record in enumerate(selected, start=1):
        translated = _translate_record(record)
        src_lines = [
            f"{idx}. {record.get('title', '')}",
            f"- 主题 / Topics: {', '.join(TOPIC_LABELS.get(topic, topic) for topic in record.get('matched_topics', [])) or '未分类 / Unclassified'}",
            f"- 来源 / Source: {_display_source(record)} / {_display_backend(record)}",
        ]
        if isinstance(record.get("scite_count"), int):
            su = (record.get("scirate_url") or "").strip()
            src_lines.append(f"- SciRate scite: {record['scite_count']}" + (f" · {su}" if su else ""))
        src_lines.extend(
            [
                f"- 中文标题: {translated.get('title_zh', '')}",
                f"- 中文摘要: {translated.get('summary_zh', '')}",
                f"- English Abstract: {_build_en_abstract(record)}",
                f"- 链接 / Link: {record.get('arxiv_url', '')}",
                "",
            ]
        )
        lines.extend(src_lines)
    return "\n".join(lines).strip()


def _feishu_safe_markdown(text: str, limit: int = 900) -> str:
    return _shorten_text((text or "").replace("\r", " ").strip(), limit=limit)


def _priority_label(record: Dict[str, Any]) -> str:
    return {
        "high": "高",
        "medium": "中",
        "info": "低",
    }.get(record.get("importance", "info"), "低")


def _priority_emoji(record: Dict[str, Any]) -> str:
    return {
        "high": "🔴",
        "medium": "🟡",
        "info": "🔵",
    }.get(record.get("importance", "info"), "🔵")


def _build_topic_lane(records: List[Dict[str, Any]], topic_id: str, title: str, limit: int = 2) -> str:
    lane = [record for record in records if topic_id in (record.get("matched_topics") or [])][:limit]
    if not lane:
        return f"**{title}**\n- 暂无重点论文"
    lines = [f"**{title}**"]
    for record in lane:
        lines.append(
            f"- {_priority_emoji(record)} {_priority_label(record)}优先级 | "
            f"{_feishu_safe_markdown(record.get('title', ''), 90)}"
        )
    return "\n".join(lines)


def _feishu_scirate_md(record: Dict[str, Any]) -> str:
    n = record.get("scite_count")
    if not isinstance(n, int):
        return ""
    url = (record.get("scirate_url") or "").strip()
    if url:
        return f"**SciRate scite**：{n} · [SciRate]({url})"
    return f"**SciRate scite**：{n}"


def _build_feishu_card(report: Dict[str, Any],
                       record: Optional[Dict[str, Any]] = None,
                       index: int = 1,
                       total: Optional[int] = None,
                       image_keys: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    top_papers = (report.get("top_papers") or [])[:4]
    focus = record or (top_papers[0] if top_papers else {})
    title = f"{report.get('card_title') or 'QuantaMind 情报员日报'} {report.get('report_date') or ''}".strip()
    if config.INTEL_FEISHU_KEYWORD:
        title = f"{config.INTEL_FEISHU_KEYWORD} {title}".strip()
    if total:
        title = f"{title} · {index}/{total}"
    translated = _lightweight_feishu_translation(focus) if focus else {"title_zh": "", "summary_zh": ""}
    topics = ", ".join(TOPIC_LABELS.get(topic, topic) for topic in focus.get("matched_topics", [])) or "未分类"
    scirate_line = _feishu_scirate_md(focus)
    card_md_parts = [
        f"**中文标题**：{_feishu_safe_markdown(translated.get('title_zh', ''), 160)}",
        f"**英文标题**：{_feishu_safe_markdown(focus.get('title', ''), 160)}",
        f"**作者信息**：第一作者 {_feishu_safe_markdown(_first_author(focus), 80)} | 通讯作者 {_feishu_safe_markdown(_corresponding_author(focus), 80)}",
        f"**杂志/会议**：{_feishu_safe_markdown(_journal_or_venue(focus), 120)}",
    ]
    if scirate_line:
        card_md_parts.append(_feishu_safe_markdown(scirate_line, 140))
    card_md_parts.extend(
        [
            f"**中文摘要**：{_feishu_safe_markdown(translated.get('summary_zh', ''), 260)}",
            f"**English Abstract**：{_feishu_safe_markdown(_build_en_abstract(focus), 320)}",
            f"**主题标签**：{_feishu_safe_markdown(topics, 120)}",
            f"**原文链接**：[查看论文]({focus.get('arxiv_url', '')})",
        ]
    )
    elements: List[Dict[str, Any]] = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "\n".join(card_md_parts),
            },
        }
    ]
    if image_keys:
        if image_keys.get("tech_system_map"):
            elements.extend(
                [
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "**技术体系定位图**"},
                    },
                    {
                        "tag": "img",
                        "img_key": image_keys["tech_system_map"],
                        "alt": {"tag": "plain_text", "content": "技术体系定位图"},
                        "mode": "fit_horizontal",
                        "compact_width": False,
                    },
                ]
            )
        if image_keys.get("tech_route_graph"):
            elements.extend(
                [
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "**技术路线图**"},
                    },
                    {
                        "tag": "img",
                        "img_key": image_keys["tech_route_graph"],
                        "alt": {"tag": "plain_text", "content": "技术路线图"},
                        "mode": "fit_horizontal",
                        "compact_width": False,
                    },
                ]
            )
        method_figure = (focus.get("tech_route_graph") or {}).get("method_figure") or {}
        if image_keys.get("method_figure"):
            caption = _feishu_safe_markdown(method_figure.get("caption", "论文方法图"), 220)
            elements.extend(
                [
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": f"**论文方法图**\n{caption}"},
                    },
                    {
                        "tag": "img",
                        "img_key": image_keys["method_figure"],
                        "alt": {"tag": "plain_text", "content": "论文方法图"},
                        "mode": "fit_horizontal",
                        "compact_width": False,
                    },
                ]
            )
    return {
        "config": {"wide_screen_mode": True, "enable_forward": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": title},
        },
        "elements": elements,
    }


def _build_feishu_text_payload(text: str) -> Dict[str, Any]:
    final_text = text or ""
    if config.INTEL_FEISHU_KEYWORD:
        final_text = f"{config.INTEL_FEISHU_KEYWORD}\n{final_text}"
    return {"msg_type": "text", "content": {"text": final_text[:3800]}}


def _post_feishu_payload(webhook: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(webhook, json=payload)
        resp.raise_for_status()
        data = resp.json()
    if data.get("code", 0) != 0:
        raise RuntimeError(data.get("msg", "unknown_error"))
    return data


def _get_feishu_tenant_access_token() -> Optional[str]:
    if not (config.INTEL_FEISHU_APP_ID and config.INTEL_FEISHU_APP_SECRET):
        return None
    now = time.time()
    cached = _feishu_token_cache.get("token")
    if cached and now < float(_feishu_token_cache.get("expires_at", 0.0)):
        return cached
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": config.INTEL_FEISHU_APP_ID, "app_secret": config.INTEL_FEISHU_APP_SECRET},
        )
        resp.raise_for_status()
        data = resp.json()
    if data.get("code", 0) != 0:
        raise RuntimeError(data.get("msg", "failed_to_get_tenant_access_token"))
    token = data.get("tenant_access_token") or ""
    expire = int(data.get("expire", 7200))
    _feishu_token_cache["token"] = token
    _feishu_token_cache["expires_at"] = now + max(expire - 120, 60)
    return token


def _upload_feishu_image(image_bytes: bytes) -> Optional[str]:
    token = _get_feishu_tenant_access_token()
    if not token or not image_bytes:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    last_error: Optional[Exception] = None
    for attempt in range(1, FEISHU_IMAGE_UPLOAD_MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    "https://open.feishu.cn/open-apis/im/v1/images",
                    headers=headers,
                    data={"image_type": "message"},
                    files={"image": ("intel-chart.png", image_bytes, "image/png")},
                )
                resp.raise_for_status()
                data = resp.json()
            if data.get("code", 0) != 0:
                raise RuntimeError(data.get("msg", "failed_to_upload_image"))
            return (((data.get("data") or {}).get("image_key")) or "").strip() or None
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError, httpx.HTTPStatusError) as e:
            last_error = e
            response = getattr(e, "response", None)
            retryable = response is None or response.status_code >= 500
            if attempt >= FEISHU_IMAGE_UPLOAD_MAX_RETRIES or not retryable:
                raise
            delay = FEISHU_IMAGE_UPLOAD_RETRY_DELAY_SECONDS * attempt
            _log.warning("飞书图片上传失败（第 %d/%d 次），%.1f 秒后重试: %s", attempt, FEISHU_IMAGE_UPLOAD_MAX_RETRIES, delay, e)
            time.sleep(delay)
    if last_error:
        raise last_error
    return None


def _normalize_image_to_png_bytes(image_bytes: bytes) -> bytes:
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA")
            buf = BytesIO()
            image.save(buf, format="PNG")
            return buf.getvalue()
    except Exception:
        return image_bytes


def _download_method_figure_bytes(method_figure: Dict[str, Any]) -> bytes:
    image_url = (method_figure or {}).get("image_url", "")
    if not image_url:
        return b""
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        resp = client.get(image_url)
        resp.raise_for_status()
        return _normalize_image_to_png_bytes(resp.content)


def _build_feishu_image_keys(record: Dict[str, Any]) -> Dict[str, str]:
    keys: Dict[str, str] = {}
    tech_system_map = record.get("tech_system_map") or {}
    tech_route_graph = record.get("tech_route_graph") or {}
    method_figure = tech_route_graph.get("method_figure") or record.get("method_figure") or {}
    try:
        if tech_system_map:
            image_key = _upload_feishu_image(_png_bytes_from_system_map(tech_system_map, record))
            if image_key:
                keys["tech_system_map"] = image_key
        if tech_route_graph:
            image_key = _upload_feishu_image(_png_bytes_from_route_graph(tech_route_graph, record))
            if image_key:
                keys["tech_route_graph"] = image_key
        if method_figure:
            image_key = _upload_feishu_image(_download_method_figure_bytes(method_figure))
            if image_key:
                keys["method_figure"] = image_key
    except Exception as e:
        _log.warning("飞书图片上传失败，回退无图卡片: %s", e)
    return keys


def send_feishu_report(report: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
    webhook = webhook_url or config.INTEL_FEISHU_WEBHOOK
    if not webhook:
        return {"status": "skipped", "reason": "webhook_not_configured"}
    text = report.get("text", "")
    top_papers = report.get("top_papers") or []
    try:
        if top_papers:
            total = len(top_papers)
            for idx, record in enumerate(top_papers, start=1):
                enriched = _attach_method_figure(_enrich_structured_fields(record))
                image_keys = _build_feishu_image_keys(enriched)
                card_payload = {
                    "msg_type": "interactive",
                    "card": _build_feishu_card(report, record=enriched, index=idx, total=total, image_keys=image_keys),
                }
                _post_feishu_payload(webhook, card_payload)
            return {"status": "sent", "reason": "", "format": "card", "messages": total}
    except Exception as e:
        _log.warning("飞书卡片推送失败，回退纯文本: %s", e)
    try:
        if top_papers:
            total = len(top_papers)
            for idx, record in enumerate(top_papers, start=1):
                translated = _lightweight_feishu_translation(record)
                topics = ", ".join(TOPIC_LABELS.get(topic, topic) for topic in record.get("matched_topics", [])) or "未分类"
                lines = [
                    f"{idx}/{total}",
                    f"论文标题（中文）：{translated.get('title_zh', '')}",
                    f"Paper Title: {record.get('title', '')}",
                    f"优先级：{_priority_label(record)}优先级",
                    f"主题：{topics}",
                ]
                if isinstance(record.get("scite_count"), int):
                    lines.append(f"SciRate scite：{record['scite_count']}")
                    if (record.get("scirate_url") or "").strip():
                        lines.append(f"SciRate：{record['scirate_url']}")
                lines.extend(
                    [
                        f"中文摘要：{translated.get('summary_zh', '')}",
                        f"English Abstract: {_build_en_abstract(record)}",
                        f"链接：{record.get('arxiv_url', '')}",
                    ]
                )
                paper_text = "\n".join(lines)
                _post_feishu_payload(webhook, _build_feishu_text_payload(paper_text))
            return {"status": "sent", "reason": "", "format": "text", "messages": total}
        _post_feishu_payload(webhook, _build_feishu_text_payload(text))
        return {"status": "sent", "reason": "", "format": "text", "messages": 1}
    except Exception as e:
        _log.warning("飞书推送失败: %s", e)
        return {"status": "failed", "reason": str(e)}


def _intel_feishu_needs_delivery_push(delivery: Dict[str, Any]) -> bool:
    """已配置 Webhook 且飞书侧尚未标记为成功时，允许补推（避免「已生成日报但未推送」永久卡住）。"""
    if not (config.INTEL_FEISHU_WEBHOOK or "").strip():
        return False
    status = (delivery or {}).get("status", "")
    if status == "sent":
        return False
    return True


def _persist_intel_report(report_id: str, report: Dict[str, Any]) -> None:
    _reports_cache[report_id] = report
    try:
        state_store.upsert_intel_report(report_id, report)
    except Exception as e:
        _log.warning("保存情报日报失败 %s: %s", report_id, e)


def _build_digest_short_summary(report: Dict[str, Any], prefix: str = "今日情报日报") -> str:
    delivery = ((report.get("delivery") or {}).get("feishu") or {})
    source_mode = report.get("source_mode", "")
    papers = report.get("papers_count", 0)
    top_papers = report.get("top_papers") or []
    topic_counts = report.get("topic_counts") or {}
    topics = ", ".join(list(topic_counts.keys())[:4]) or "暂无"
    return (
        f"{prefix}：{report.get('report_date', '')}\n"
        f"状态：{delivery.get('status', 'unknown')}\n"
        f"来源模式：{source_mode or 'unknown'}\n"
        f"收录论文：{papers} 篇，精选 {len(top_papers)} 篇\n"
        f"热点主题：{topics}"
    ).strip()


def _send_feishu_report_text_only(report: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
    webhook = webhook_url or config.INTEL_FEISHU_WEBHOOK
    if not webhook:
        return {"status": "skipped", "reason": "webhook_not_configured", "format": "text", "messages": 0}
    try:
        _post_feishu_payload(webhook, _build_feishu_text_payload(report.get("text", "")))
        return {"status": "sent", "reason": "", "format": "text", "messages": 1}
    except Exception as e:
        _log.warning("飞书文本捷径推送失败: %s", e)
        return {"status": "failed", "reason": str(e), "format": "text", "messages": 0}


def run_daily_digest_shortcut(force: bool = False) -> Dict[str, Any]:
    """稳定捷径：仅使用缓存论文生成并发送今日文本日报，不走实时抓取/翻译/卡片。"""
    now_local = _local_now()
    report_day = now_local.strftime("%Y-%m-%d")
    report_id = f"intel-{report_day}"
    existing = state_store.get_intel_report(report_id) or _reports_cache.get(report_id)
    if existing and not force:
        delivery = (existing.get("delivery") or {}).get("feishu") or {}
        if delivery.get("status") == "sent":
            return {
                "status": "already_sent",
                "report": existing,
                "summary": _build_digest_short_summary(existing, prefix="今日情报已发送"),
            }

    window_start, window_end = get_report_window(now_local)
    records = _fallback_recent_papers(window_start, window_end)
    if not records:
        records = list_recent_papers(limit=max(config.INTEL_MAX_PAPERS, 12))
    if not records:
        return {
            "status": "empty",
            "report": None,
            "summary": "今日情报快捷路径未找到可用缓存论文，请稍后再试。",
        }

    report = build_report_payload(records, report_day)
    report["source_mode"] = "cache_shortcut"
    report.setdefault("delivery", {})["feishu"] = _send_feishu_report_text_only(report)
    _persist_intel_report(report_id, report)
    memory.append_memory(
        f"[intel_officer] 通过快捷路径生成/发送情报日报 {report_day}，飞书状态：{report['delivery']['feishu'].get('status', '')}",
        project_id="default",
    )
    return {
        "status": "sent" if report["delivery"]["feishu"].get("status") == "sent" else "failed",
        "report": report,
        "summary": _build_digest_short_summary(report, prefix="今日情报已通过快捷路径发送"),
    }


def _finalize_report_feishu_delivery(
    report: Dict[str, Any],
    records_for_tracks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """主日报 + 分轨道报表一并推送，并写回 delivery / track_reports。"""
    updated = dict(report)
    main_delivery = send_feishu_report(updated)
    updated.setdefault("delivery", {})["feishu"] = main_delivery

    if records_for_tracks is not None:
        track_reports = build_formal_track_reports(records_for_tracks, updated.get("report_date"))
    else:
        track_reports = dict(updated.get("track_reports") or {})
        if not track_reports and updated.get("top_papers"):
            track_reports = build_formal_track_reports(updated["top_papers"], updated.get("report_date"))
    track_deliveries: Dict[str, Dict[str, Any]] = {}
    for track_key, track_report in track_reports.items():
        tr = dict(track_report)
        td = send_feishu_report(tr)
        tr.setdefault("delivery", {})["feishu"] = td
        track_deliveries[track_key] = td
        track_reports[track_key] = tr
    updated["track_reports"] = track_reports
    if track_deliveries:
        updated.setdefault("delivery", {})["feishu_tracks"] = track_deliveries
    return updated


def flush_pending_feishu_for_today() -> None:
    """Gateway 启动后：若当日日报已在库但飞书未成功，立即补推一次。"""
    report_day = _local_now().strftime("%Y-%m-%d")
    report_id = f"intel-{report_day}"
    existing = state_store.get_intel_report(report_id) or _reports_cache.get(report_id)
    if not existing:
        return
    prev = (existing.get("delivery") or {}).get("feishu") or {}
    if not _intel_feishu_needs_delivery_push(prev):
        return
    _log.info("启动补推：当日情报日报 %s 飞书状态=%s，正在下发", report_id, prev.get("status", "?"))
    report = _finalize_report_feishu_delivery(dict(existing), records_for_tracks=None)
    _persist_intel_report(report_id, report)


def run_daily_digest(force: bool = False) -> Dict[str, Any]:
    now_local = _local_now()
    report_day = now_local.strftime("%Y-%m-%d")
    report_id = f"intel-{report_day}"
    existing = state_store.get_intel_report(report_id) or _reports_cache.get(report_id)
    if existing and not force:
        prev_delivery = (existing.get("delivery") or {}).get("feishu") or {}
        if _intel_feishu_needs_delivery_push(prev_delivery):
            _log.info(
                "情报日报 %s 已存在但飞书未成功（status=%s），执行补推",
                report_id,
                prev_delivery.get("status", "?"),
            )
            report = _finalize_report_feishu_delivery(dict(existing), records_for_tracks=None)
            _persist_intel_report(report_id, report)
            memory.append_memory(
                f"[intel_officer] 补推情报日报 {report_day} 至飞书，状态：{report['delivery']['feishu'].get('status', '')}",
                project_id="default",
            )
            return {"status": "resent", "report": report}
        return {"status": "exists", "report": existing}

    window_start, window_end = get_report_window(now_local)
    fetch_error: Optional[Exception] = None
    records: List[Dict[str, Any]] = []
    source_mode = "live"
    try:
        records = fetch_recent_papers(
            days_back=config.INTEL_LOOKBACK_DAYS,
            max_per_topic=8,
            start_time=window_start,
            end_time=window_end,
        )
    except Exception as e:
        fetch_error = e
        _log.warning("实时情报抓取失败，回退到缓存论文生成当日报告: %s", e)
        records = _fallback_recent_papers(window_start, window_end)
        source_mode = "cache_fallback"

    if fetch_error is None:
        for record in records:
            persist_paper(record)
    elif not records:
        raise fetch_error
    elif source_mode == "cache_fallback":
        _log.info("情报日报 %s 使用缓存回退生成，共 %d 篇论文", report_id, len(records))

    report = build_report_payload(records, report_day)
    report["source_mode"] = source_mode
    report = _finalize_report_feishu_delivery(report, records_for_tracks=records)
    delivery = report["delivery"]["feishu"]
    _persist_intel_report(report_id, report)

    memory.append_memory(
        f"[intel_officer] 生成情报日报 {report_day}，收录 {len(report['top_papers'])} 篇精选论文。"
        f"\n主题分布：{report['topic_counts']}\n飞书状态：{delivery['status']}\n来源模式：{source_mode}",
        project_id="default",
    )
    return {"status": "created_from_cache" if source_mode == "cache_fallback" else "created", "report": report}


def enrich_intel_paper_for_overview(record: Dict[str, Any]) -> Dict[str, Any]:
    """仪表盘情报面板：补齐技术路线图结构，并去掉 SVG/data_uri 以减小 JSON 体积。"""
    enriched = _enrich_structured_fields(dict(record))
    tr = dict(enriched.get("tech_route_graph") or {})
    for k in ("svg", "data_uri", "mime_type"):
        tr.pop(k, None)
    enriched["tech_route_graph"] = tr
    ts = dict(enriched.get("tech_system_map") or {})
    for k in ("svg", "data_uri", "mime_type"):
        ts.pop(k, None)
    enriched["tech_system_map"] = ts
    return enriched


def list_recent_papers(limit: int = 20, topic: Optional[str] = None) -> List[Dict[str, Any]]:
    papers = state_store.list_intel_papers(limit=limit, topic=topic)
    if papers:
        return [_enrich_structured_fields(item) for item in papers]
    items = list(_papers_cache.values())
    if topic:
        items = [item for item in items if topic in item.get("matched_topics", [])]
    return [_enrich_structured_fields(item) for item in sorted(items, key=lambda item: item.get("updated", ""), reverse=True)[:limit]]


def list_reports(limit: int = 10) -> List[Dict[str, Any]]:
    reports = state_store.list_intel_reports(limit=limit)
    if reports:
        return reports
    return sorted(_reports_cache.values(), key=lambda item: item.get("created_at", ""), reverse=True)[:limit]
