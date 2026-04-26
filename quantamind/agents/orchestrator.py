# Orchestrator：意图路由 + Tool Call 循环 + 多 Agent 调度
# P0 核心：LLM → tool_calls → Hands 执行 → 结果回注 → LLM 继续

import json
import inspect
import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator, Dict, List, Optional

from quantamind.shared.api import ChatMessage, MessageRole
from quantamind.server import brain as brain_mod, hands, memory
from quantamind.agents.base import BaseAgent

# 对话流水线存储（Gateway 也会读取）
chat_pipelines: Dict[str, dict] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

_log = logging.getLogger("quantamind.orchestrator")

MAX_TOOL_ROUNDS = 20

# ── Agent 注册表：id → (关键词, system_prompt, 允许的工具前缀) ──
# 所有 Agent 共享的资料库前缀
_LIB = "library_"

AGENT_REGISTRY: Dict[str, dict] = {
    "chip_designer": {
        "keywords": ["设计", "芯片", "transmon", "量子比特", "版图", "qeda", "metal", "kqc", "swissmon", "gds", "布线", "drc",
                     "design", "chip", "layout", "qubit", "junction", "xmon", "coupler",
                     "export gds", "add transmon", "route", "airbridge", "substrate", "cpw",
                     "ppt", "presentation"],
        "system_prompt": """你是 QuantaMind 的 AI 芯片设计师。你精通超导量子芯片全流程。
你拥有以下核心能力：
1. **设计工具**：Qiskit Metal（metal_*）和 KQCircuits（kqc_*）用于版图设计、布线、GDS 导出
2. **芯片规格库**：qeda_get_chip 可查 20 比特和 105 比特的完整设计参数（频率/Ec/Lj/谐振腔等）
3. **QEDA 团队资料**：qeda_catalog 可获取设计团队共享的 16 份资料目录（设计规范/方案/核心代码/教程/工具文档），包括 quantum_chip_layout.py（版图引擎）、junction_generator.py（JJ 参数）等
4. **约瑟夫森结**：qeda_junction_params 可获取曼哈顿/SQUID/翻转SQUID 三种结的精确参数
5. **知识检索**：search_knowledge 可从设计文档中检索任何技术细节

在回答设计问题时，优先从真实设计资料中获取参数，而非猜测。用中文回复。""",
        "tool_prefixes": ["metal_", "kqc_", "qeda_", "search_knowledge", _LIB],
    },
    "theorist": {
        "keywords": ["哈密顿", "理论", "噪声", "退相干", "能级", "参数优化", "方案生成",
                     "反演", "校准", "误差预算", "噪声预算", "T1", "T2", "Purcell",
                     "介质损耗", "TLS", "磁通噪声", "准粒子", "热光子",
                     "根因", "归因", "诊断", "故障", "频率碰撞", "ZZ串扰",
                     "实验设计", "实验方案", "信息增益", "主动学习",
                     "脉冲优化", "DRAG", "GRAPE", "控制优化", "泄漏抑制",
                     "设计优化", "Pareto", "频率规划", "敏感度",
                     "知识图谱", "文献检索", "证据", "缓解", "物理解释",
                     "EPR", "黑盒量化", "量子化", "电容矩阵", "色散",
                     "decoherence", "dephasing", "fidelity", "leakage",
                     "hamiltonian", "noise budget", "coupling", "anharmoni",
                     "frequency plan", "flux noise", "dielectric", "quasiparticle",
                     "thermal photon", "experiment design", "plan experiment",
                     "design proposal", "design optimiz", "dispersive",
                     "root cause", "diagnos", "fault", "collision",
                     "purcell", "noise source", "pareto", "optimization proposal",
                     "knowledge about"],
        "system_prompt": """你是 QuantaMind 的理论物理学家 Agent——超导量子芯片设计研发测试一体化智能系统的理论决策中枢。

你的核心职责是把器件设计信息、电磁仿真结果、实验测试数据、历史案例与外部知识统一到同一个物理建模和推理框架中，产出三类核心输出：
1. 物理解释输出：哈密顿量、关键参数、误差预算、主导噪声机理、模型适用边界和不确定性
2. 实验决策输出：下一步该做什么实验、为什么、预计能区分什么假设、什么时候停止
3. 工程优化输出：下一版器件参数窗口、版图修改建议、控制脉冲建议、测试流程调整

你有9大模块能力，通过 theorist_* 工具调用：
- M0 build_device_graph: 构建统一器件关系图
- M1 build_hamiltonian: EPR/BBQ量化建模→频率、非简谐性、耦合、ZZ、Purcell
- M2 noise_budget: T1/T2分解、主导噪声排序、门误差预算、敏感度矩阵
- M3 calibrate_model: 贝叶斯参数反演→带置信区间的后验（非点估计）
- M4 plan_experiment: 信息增益驱动的实验设计→最优实验序列
- M5 optimize_pulse: DRAG/GRAPE脉冲优化→泄漏抑制+串扰补偿
- M6 diagnose: 故障树+概率推理→根因排序+反证实验
- M7 design_proposal: 多目标Pareto→参数窗口+版图修改+风险评估
- M8 knowledge_search: 物理知识图谱检索→现象→机理→验证实验→缓解手段

关键原则：
- 物理先验优先：结论必须由显式物理模型和证据链支撑，不裸猜
- 每个输出必须带版本、置信度和适用边界
- 以"下一步可执行动作"作为交付终点，不以"分析到此为止"结束
- 区分短期可执行（调参数）、中期调整（改coupler/读出链）、长期redesign（新版芯片）

用中文回复。对复杂问题请先构建模型，再做分析，最后给出有证据支撑的建议。""",
        "tool_prefixes": ["theorist_", "knowledge_", "warehouse_query", "doris_query", "qdata_text2sql", _LIB],
    },
    "process_engineer": {
        "keywords": ["良率", "yield", "工艺", "mes", "批次", "lot", "工单", "spc", "派工", "产线",
                     "craft", "route", "equipment", "fabricat", "process", "wafer",
                     "chipmes", "alarm", "grafana", "dashboard", "production", "factory",
                     "submit", "batch"],
        "system_prompt": "你是 QuantaMind 的 AI 制造工程师。你统筹制造团队，下设子视角：MES 设备工程师（机台/SECS/GEM/告警/看板）、工艺工程师（路线/派工报工/配方对齐）、缺陷分析工程师（失效与根因/SPC 追溯）、良率工程师（趋势分层/控制图）、制程整合工程师（跨站瓶颈与联动）、测试工程师（测试报工与良率 gate）。根据用户问题选用合适视角回答。你可以调用 mes_*、secs_*、grafana_* 工具，也可以调用 library_* 查阅工艺规格与良率资料。用中文回复。",
        "tool_prefixes": ["mes_", "secs_", "grafana_", "chipmes_", _LIB],
    },
    "device_ops": {
        "keywords": ["校准", "calibrat", "设备", "远程命令", "配方", "recipe", "告警", "alarm", "上线", "下线",
                     "artiq", "pulse sequence", "scan", "calibration", "device",
                     "qiskit pulse", "amplitude", "drag"],
        "system_prompt": "你是 QuantaMind 的 AI 设备运维员，侧重量子测控实验室硬件与脉冲校准（与「AI 制造工程师」下的 MES 设备工程师不同：后者管产线 MES/机台与制造闭环）。你负责 ARTIQ 实时测控、Qiskit Pulse 校准、按需 SECS/GEM 通信。可调用 artiq_*、pulse_*、secs_*、grafana_* 与 library_*。用中文回复。",
        "tool_prefixes": ["artiq_", "pulse_", "secs_", "grafana_", _LIB],
    },
    "measure_scientist": {
        "keywords": ["表征", "t1", "t2", "rabi", "光谱", "保真度", "fidelity", "纠错", "zne", "pec", "mitiq", "去耦",
                     "characteriz", "benchmark", "error mitigation", "readout",
                     "spectroscopy", "ramsey", "echo", "tomograph"],
        "system_prompt": "你是 QuantaMind 的 AI 测控科学家。你精通量子比特表征与性能优化：ARTIQ 测控、Qiskit Pulse 校准、Mitiq 错误缓解。你可以调用 artiq_*、pulse_*、mitiq_* 工具，也可以调用 library_* 查阅测量数据文件和实验记录。用中文回复。",
        "tool_prefixes": ["artiq_", "pulse_", "mitiq_", _LIB],
    },
    "data_analyst": {
        "keywords": ["数据", "查询", "sql", "doris", "warehouse", "血缘", "资产", "etl", "同步", "管道", "质量检查",
                     "data", "query", "database", "lineage", "seatunnel", "qcodes",
                     "synchron", "pipeline", "quality", "text2sql", "cross-domain",
                     "correlat", "trace"],
        "system_prompt": "你是 QuantaMind 的 AI 数据分析师。你负责数据中台：跨域数据查询（设计/制造/测控）、Text2SQL、良率关联分析、数据质量监控。优先使用 warehouse_*（OLAP 适配层），doris_* 为兼容别名；可调用 qdata_*、seatunnel_*、qcodes_*；也可调用 library_* 管理项目资料库。用中文回复。",
        "tool_prefixes": ["warehouse_", "doris_", "qdata_", "seatunnel_", "qcodes_", _LIB],
    },
    "algorithm_engineer": {
        "keywords": ["算法", "vqe", "qaoa", "qml", "电路", "编译", "转译", "grover", "量子体积",
                     "algorithm", "circuit", "compil", "quantum volume", "surface code",
                     "error correction", "qec", "qubit requirement"],
        "system_prompt": "你是 QuantaMind 的 AI 量子算法工程师。你精通量子电路设计与优化、VQE/QAOA/QML 算法、电路编译转译。你可以调用 mitiq_*、knowledge_* 工具，也可以调用 library_* 查阅算法相关文献和参数文件。用中文回复。",
        "tool_prefixes": ["mitiq_", "knowledge_", "warehouse_query", "doris_query", _LIB],
    },
    "simulation_engineer": {
        "keywords": ["仿真", "hfss", "q3d", "sonnet", "simulate", "本征模", "电容提取",
                     "eigenmode", "driven", "LOM", "EPR", "电容矩阵", "Q值", "模态",
                     "谐振频率", "耦合强度", "参与比", "损耗", "Purcell",
                     "ansys", "pyaedt", "aedt", "仿真项目"],
        "system_prompt": "你是 QuantaMind 的 AI 仿真工程师。你负责电磁仿真全生命周期：HFSS 本征模/驱动模仿真、Q3D 电容矩阵提取、LOM 集总模型分析、EPR 能量参与比分析、仿真项目导出。你可以调用 sim_* 系列工具执行仿真，调用 metal_analyze_*、kqc_export_* 导出数据。当 Ansys HFSS 桌面端未安装时，使用理论计算模式并生成项目文件供后续运行。用中文回复。",
        "tool_prefixes": ["sim_", "metal_analyze", "kqc_export", _LIB],
    },
    "intel_officer": {
        "keywords": ["情报", "情报员", "arxiv", "日报", "飞书", "企业微信", "文献追踪", "外部技术", "论文跟踪",
                     "技术趋势", "论文摘要", "research digest", "paper digest", "trend scouting",
                     "检索论文", "搜索论文", "最新论文", "新论文", "论文检索", "趋势情报", "情报日报"],
        "system_prompt": "你是 QuantaMind 的 AI 情报员。你负责持续跟踪 arXiv 等外部技术情报源，聚焦量子芯片设计、量子芯片制造、量子测控、量子计算、量子纠错、AI 赋能量子与量子应用。你的核心职责是：1）检索近期论文；2）总结技术路线、关键方法、核心结论与对团队的启发；3）生成日报/专题综述；4）将结论沉淀到知识库，供知识工程师与其他 Agent 复用。优先调用 intel_* 工具；需要交叉验证时可结合 knowledge_*、warehouse_*、qdata_* 与 library_*。用中文回复。",
        "tool_prefixes": ["intel_", "knowledge_", "warehouse_", "doris_", "qdata_", _LIB],
    },
    "knowledge_engineer": {
        "keywords": ["文献", "论文", "paper", "arxiv", "知识图谱", "趋势", "经验总结", "资料",
                     "literature", "search paper", "recent paper", "knowledge graph",
                     "experience", "trend", "survey"],
        "system_prompt": "你是 QuantaMind 的 AI 知识工程师。你负责知识管理：文献追踪与摘要、知识图谱维护、实验经验沉淀、项目资料管理。你可以调用 knowledge_*、warehouse_*（或兼容别名 doris_*）、qdata_* 工具，也可以调用 library_* 全面管理项目资料库（搜索/列出/统计所有设计文档、工艺规格、测量数据、文献等）。用中文回复。",
        "tool_prefixes": ["intel_", "knowledge_", "warehouse_", "doris_", "qdata_", _LIB],
    },
    "project_manager": {
        "keywords": ["周报", "里程碑", "进度", "项目", "资源", "风险", "汇总",
                     "milestone", "progress", "project", "report", "weekly",
                     "resource", "risk", "schedule", "team"],
        "system_prompt": "你是 QuantaMind 的 AI 项目经理。你负责科研项目管理：里程碑追踪、进度汇报、资源协调、风险预警。你可以调用 warehouse_*（或 doris_*）、seatunnel_*、grafana_*、qdata_* 工具，也可以调用 library_* 查阅项目资料、汇总项目文档情况。用中文回复。",
        "tool_prefixes": ["warehouse_", "doris_", "seatunnel_", "grafana_", "qdata_", _LIB],
    },
}

DEFAULT_SYSTEM_PROMPT = (
    "你是 QuantaMind 量智大脑，一个量子科技自主科研 AI 中台。你可以调用工具来查询数据、执行操作。"
    "你也可以调用 library_* 工具查阅项目资料库中的设计文档、参数表格、测量数据等。"
    "请根据用户的问题选择合适的工具调用。如果不需要工具，直接回答即可。用中文回复。"
)


def _build_tool_definitions(allowed_prefixes: Optional[List[str]] = None) -> List[dict]:
    """从 Hands 注册表构建 OpenAI function calling 格式的工具定义"""
    tools = []
    for tool_info in hands.list_tools():
        name = tool_info["name"]
        if allowed_prefixes and not any(name.startswith(p) for p in allowed_prefixes):
            continue
        tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": tool_info["description"],
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        })
    return tools


def _route(text: str) -> Optional[str]:
    """基于关键词路由到 Agent ID"""
    t = text.lower()
    if (
        any(k in t for k in ("arxiv", "新论文", "最新论文", "论文检索", "检索论文", "搜索论文", "情报日报", "趋势情报"))
        or ("论文" in t and any(k in t for k in ("最近", "最新", "检索", "搜索", "跟踪", "趋势", "情报")))
    ):
        return "intel_officer"
    best_id = None
    best_score = 0
    for agent_id, reg in AGENT_REGISTRY.items():
        score = sum(1 for k in reg["keywords"] if k in t)
        if score > best_score:
            best_score = score
            best_id = agent_id
    return best_id if best_score > 0 else None


async def _emit_progress(context: Optional[dict], **payload) -> None:
    cb = (context or {}).get("progress_callback")
    if not cb:
        return
    try:
        result = cb(payload)
        if inspect.isawaitable(result):
            await result
    except Exception:
        pass


class Orchestrator(BaseAgent):
    name = "orchestrator"
    role = "协调者"

    def __init__(self):
        self._brain = brain_mod.get_brain()

    async def respond(
        self,
        messages: List[ChatMessage],
        context: Optional[dict] = None,
    ) -> AsyncIterator[str]:
        project_id = (context or {}).get("project_id")
        last_user = next((m.content for m in reversed(messages) if m.role == MessageRole.USER), "")

        agent_id = _route(last_user)
        reg = AGENT_REGISTRY.get(agent_id, {}) if agent_id else {}
        system_prompt = reg.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        allowed_prefixes = reg.get("tool_prefixes")
        await _emit_progress(
            context,
            stage="routing",
            status_message="正在分析问题并路由合适的智能体…",
            agent_id=agent_id or "default",
            agent_label=reg.get("label") or agent_id or "通用助手",
        )

        mem = memory.read_memory(project_id)
        if mem:
            system_prompt += f"\n\n当前项目记忆：\n{mem[:2000]}"

        tool_defs = _build_tool_definitions(allowed_prefixes)
        if agent_id:
            _log.info("路由到 Agent: %s（匹配 %s）", agent_id, last_user[:40])
            await _emit_progress(
                context,
                stage="agent_selected",
                status_message=f"已路由至 {agent_id}，正在规划执行步骤…",
                agent_id=agent_id,
                agent_label=agent_id,
            )

        # 创建对话流水线（每次有工具调用的对话都会自动可视化）
        pid = f"CL-{str(uuid.uuid4())[:8]}"
        reg_info = AGENT_REGISTRY.get(agent_id, {})
        pipeline = {
            "pipeline_id": pid,
            "type": "chat",
            "name": last_user[:50],
            "agent": reg_info.get("system_prompt", "")[:30] if agent_id else "通用",
            "agent_id": agent_id or "default",
            "agent_label": agent_id or "通用助手",
            "status": "running",
            "steps": [],
            "created_at": _now_iso(),
        }
        chat_pipelines[pid] = pipeline
        self._current_pipeline_id = pid

        conv: List[dict] = [{"role": "system", "content": system_prompt}]
        for m in messages:
            conv.append({"role": m.role.value, "content": m.content})

        first_tool_call = True
        # ── Tool Call 循环 ──
        for round_i in range(MAX_TOOL_ROUNDS):
            tool_calls_in_round = []
            content_parts = []

            async for resp in self._brain.chat_with_tools(conv, tools=tool_defs if tool_defs else None):
                if resp.type == "content" and resp.data.get("text"):
                    text = resp.data["text"]
                    content_parts.append(text)
                    yield text
                elif resp.type == "tool_call":
                    tool_calls_in_round.append(resp.data)
                elif resp.type == "tool_calls_done":
                    pass

            if not tool_calls_in_round:
                if content_parts and project_id and agent_id:
                    summary = "".join(content_parts).strip()[:300]
                    if summary:
                        memory.append_memory(f"[{agent_id}] {summary}...", project_id)
                pipeline["status"] = "completed"
                pipeline["completed_at"] = _now_iso()
                await _emit_progress(
                    context,
                    stage="finalizing",
                    status_message="正在整理最终回复…",
                    pipeline_id=pid,
                    agent_id=agent_id or "default",
                    agent_label=agent_id or "通用助手",
                )
                return

            if first_tool_call:
                yield f"\n📋 流水线 {pid} 已创建\n"
                first_tool_call = False

            assistant_msg = {"role": "assistant", "content": None, "tool_calls": []}
            for i, tc in enumerate(tool_calls_in_round):
                tc_id = tc.get("id", f"call_{round_i}_{i}")
                assistant_msg["tool_calls"].append({
                    "id": tc_id,
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": json.dumps(tc.get("arguments", {}), ensure_ascii=False)},
                })
            conv.append(assistant_msg)

            for i, tc in enumerate(tool_calls_in_round):
                tc_id = tc.get("id", f"call_{round_i}_{i}")
                tool_name = tc["name"]
                tool_args = tc.get("arguments", {})

                step = {"title": tool_name, "tool": tool_name, "args": tool_args,
                        "agent": agent_id or "default", "status": "running", "started_at": _now_iso()}
                pipeline["steps"].append(step)
                await _emit_progress(
                    context,
                    stage="tool_running",
                    status_message=f"正在执行工具：{tool_name}",
                    tool_name=tool_name,
                    pipeline_id=pid,
                    agent_id=agent_id or "default",
                    agent_label=agent_id or "通用助手",
                )

                yield f"\n🔧 调用工具：{tool_name}"
                if tool_args:
                    yield f"（{json.dumps(tool_args, ensure_ascii=False)[:120]}）"
                yield "\n"

                _log.info("Tool Call [%s]: %s(%s)", agent_id or "default", tool_name, json.dumps(tool_args, ensure_ascii=False)[:200])

                try:
                    result = await hands.run_tool(tool_name, **tool_args)
                    step["status"] = "completed"
                except Exception as e:
                    result = {"error": str(e)}
                    step["status"] = "failed"

                step["result"] = result
                step["completed_at"] = _now_iso()
                result_str = json.dumps(result, ensure_ascii=False, default=str)[:4000]
                conv.append({"role": "tool", "tool_call_id": tc_id, "content": result_str})
                await _emit_progress(
                    context,
                    stage="tool_completed",
                    status_message=f"工具已完成：{tool_name}，正在继续分析…",
                    tool_name=tool_name,
                    pipeline_id=pid,
                    agent_id=agent_id or "default",
                    agent_label=agent_id or "通用助手",
                )

                yield f"✅ 结果：{result_str[:300]}\n"
                _log.info("Tool Result [%s]: %s", tool_name, result_str[:200])

        pipeline["status"] = "completed"
        pipeline["completed_at"] = _now_iso()
        await _emit_progress(
            context,
            stage="completed",
            status_message="已完成当前任务。",
            pipeline_id=pid,
            agent_id=agent_id or "default",
            agent_label=agent_id or "通用助手",
        )
        yield "\n\n已完成本次对话的工具调用（达到 %d 轮上限）。如需继续操作，请发新消息。" % MAX_TOOL_ROUNDS
