import json
from datetime import datetime
from quantamind.server import arxiv_intel
from quantamind.server import brain as brain_module
from quantamind.agents.orchestrator import _route


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2503.12345v1</id>
    <updated>2026-03-29T01:00:00Z</updated>
    <published>2026-03-28T10:00:00Z</published>
    <title>AI-assisted superconducting qubit readout calibration</title>
    <summary>We present a machine learning workflow for superconducting qubit readout calibration. Using adaptive pulse optimization and Bayesian tuning, we improve readout fidelity. Our results show a consistent reduction in calibration time.</summary>
    <author><name>Alice</name></author>
    <author><name>Bob</name></author>
    <arxiv:primary_category term="quant-ph" />
    <category term="quant-ph" />
  </entry>
</feed>
"""

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Surface-code decoder for superconducting quantum chips</title>
      <link>https://arxiv.org/abs/2503.88888</link>
      <description>We present a decoder for surface code on superconducting qubit processors.</description>
      <pubDate>Sat, 29 Mar 2026 01:00:00 GMT</pubDate>
      <category>quant-ph</category>
    </item>
  </channel>
</rss>
"""

SAMPLE_SEARCH_HTML = """
<ol class="breathe-horizontal">
  <li class="arxiv-result">
    <p class="list-title is-inline-block">
      <a href="https://arxiv.org/abs/2603.25671">arXiv:2603.25671</a>
    </p>
    <p class="title is-5 mathjax">EPAR: Electromagnetic Pathways to Architectural Reliability in Quantum Processors</p>
    <p class="authors">
      <a href="/search/?searchtype=author&amp;query=Choudhury%2C+N">Navnil Choudhury</a>
    </p>
    <p class="tags is-inline-block">
      <span class="tag is-small is-link tooltip is-tooltip-top">cs.ET</span>
      <span class="tag is-small is-link tooltip is-tooltip-top">quant-ph</span>
    </p>
    <span class="abstract-full has-text-grey-dark mathjax">
      <span class="search-hit mathjax">Abstract:</span>
      We present an electromagnetic-to-architecture framework for superconducting quantum processors.
    </span>
    <p class="is-size-7">
      Submitted 26 March, 2026; originally announced March 2026.
    </p>
  </li>
</ol>
"""


def test_parse_feed_extracts_arxiv_entry() -> None:
    records = arxiv_intel._parse_feed(SAMPLE_FEED)
    assert len(records) == 1
    record = records[0]
    assert record["paper_id"] == "2503.12345v1"
    assert record["title"].startswith("AI-assisted superconducting qubit")
    assert record["authors"] == ["Alice", "Bob"]
    assert record["primary_category"] == "quant-ph"


def test_parse_rss_feed_extracts_recent_entry() -> None:
    records = arxiv_intel._parse_rss_feed(SAMPLE_RSS)
    assert len(records) == 1
    record = records[0]
    assert record["paper_id"] == "2503.88888"
    assert record["source"] == "arXiv RSS"
    assert record["published"].startswith("2026-03-29T01:00:00")


def test_parse_arxiv_search_html_extracts_recent_entry() -> None:
    records = arxiv_intel._parse_arxiv_search_html(SAMPLE_SEARCH_HTML)
    assert len(records) == 1
    record = records[0]
    assert record["paper_id"] == "2603.25671"
    assert record["source"] == "arXiv Search"
    assert record["primary_category"] == "cs.ET"
    assert record["published"].startswith("2026-03-26T00:00:00")


def test_build_report_payload_contains_structured_digest() -> None:
    record = arxiv_intel._parse_feed(SAMPLE_FEED)[0]
    record["matched_topics"] = ["measurement_control", "ai_for_quantum"]
    record["technical_route"] = arxiv_intel._extract_technical_route(record["summary"])
    record["core_conclusion"] = arxiv_intel._extract_conclusion(record["summary"])
    record["team_relevance"] = arxiv_intel._team_relevance(record)
    record["source"] = "arXiv RSS"
    record["retrieval_backend"] = "live-rss"
    report = arxiv_intel.build_report_payload([record], report_date="2026-03-29")
    assert report["report_id"] == "intel-2026-03-29"
    assert report["papers_count"] == 1
    assert report["top_papers"][0]["matched_topics"] == ["measurement_control", "ai_for_quantum"]
    assert "技术路线" in report["text"]
    assert "链接" in report["text"]
    assert "来源分布" in report["text"]
    assert "arXiv RSS" in report["text"]
    assert "热点主题" in report["text"]
    assert "trend_summary" in report
    assert report["source_summary"]["source_counts"]["arXiv RSS"] == 1
    assert report["trend_summary"]["hot_topics"]
    assert report["top_papers"][0]["tech_system_map"]["highlighted_path"]
    assert report["top_papers"][0]["tech_route_graph"]["nodes"]


def test_normalize_live_record_adds_structured_fields() -> None:
    record = arxiv_intel._parse_feed(SAMPLE_FEED)[0]
    record["source"] = "arXiv"
    start_utc = datetime.fromisoformat("2026-03-27T00:00:00+00:00")
    end_utc = datetime.fromisoformat("2026-03-29T00:00:00+00:00")
    normalized = arxiv_intel._normalize_live_record(record, start_utc, end_utc, backend="live-api")
    assert normalized is not None
    assert normalized["tech_system_map"]["version"] == "taxonomy_engineer_v1"
    assert normalized["tech_system_map"]["source_mode"] == "taxonomy_library"
    assert normalized["tech_system_map"]["library_id"] == "taxonomy_engineer_measurement_control_v1"
    assert normalized["tech_system_map"]["highlighted_topic"]["label"]
    assert normalized["tech_system_map"]["highlighted_layer"]
    assert normalized["tech_system_map"]["highlighted_module"]
    assert normalized["tech_system_map"]["highlighted_detail"] == "自动标定与参数调优"
    assert normalized["tech_route_graph"]["graph_type"] == "pipeline"
    assert [edge["source"] for edge in normalized["tech_route_graph"]["edges"]] == ["problem", "method", "implementation", "evaluation"]
    assert normalized["tech_system_map"]["svg"].startswith("<svg")
    assert normalized["tech_route_graph"]["svg"].startswith("<svg")
    assert normalized["tech_system_map"]["data_uri"].startswith("data:image/svg+xml")
    assert normalized["tech_route_graph"]["data_uri"].startswith("data:image/svg+xml")


def test_rendered_svgs_include_expected_labels() -> None:
    record = arxiv_intel._parse_feed(SAMPLE_FEED)[0]
    record["source"] = "arXiv"
    start_utc = datetime.fromisoformat("2026-03-27T00:00:00+00:00")
    end_utc = datetime.fromisoformat("2026-03-29T00:00:00+00:00")
    normalized = arxiv_intel._normalize_live_record(record, start_utc, end_utc, backend="live-api")
    assert "技术体系定位图" in normalized["tech_system_map"]["svg"]
    assert "技术路线图" in normalized["tech_route_graph"]["svg"]
    assert "论文落点" in normalized["tech_system_map"]["svg"]
    assert "技术体系工程师 v1" in normalized["tech_system_map"]["svg"]
    assert "自动标定与参数调优" in normalized["tech_system_map"]["svg"]
    assert "研究问题" in normalized["tech_route_graph"]["svg"]


def test_chip_design_taxonomy_engineer_library_marks_specific_point() -> None:
    record = {
        "paper_id": "chip-1",
        "title": "Transmon coupler layout optimization for scalable superconducting chips",
        "summary": "We optimize transmon frequencies, coupler geometry, and layout crosstalk for a scalable superconducting processor.",
        "matched_topics": ["chip_design"],
    }
    system_map = arxiv_intel._build_tech_system_map(record)
    assert system_map["library_id"] == "taxonomy_engineer_chip_design_v1"
    assert system_map["highlighted_layer"] == "比特与无源器件"
    assert system_map["highlighted_module"] in {"单元器件设计", "版图与封装互连"}
    assert system_map["highlighted_detail"] in {"Transmon/Fluxonium 参数设计", "耦合器与总线设计", "版图布线与串扰控制"}


def test_load_taxonomy_engineer_libraries_from_knowledge_files(tmp_path, monkeypatch) -> None:
    library_dir = tmp_path / "taxonomy"
    library_dir.mkdir()
    runtime_dir = tmp_path / "runtime"
    runtime_file = runtime_dir / "runtime_overlays.json"
    (library_dir / "measurement_control.json").write_text(json.dumps({
        "topic_id": "measurement_control",
        "library_id": "taxonomy_engineer_measurement_control_v1",
        "system_label": "量子测控技术体系",
        "lanes": [
            {
                "id": "lane1",
                "label": "标定与闭环",
                "keywords": ["calibration"],
                "modules": [
                    {
                        "id": "module1",
                        "label": "自动标定",
                        "keywords": ["calibration"],
                        "points": [
                            {"id": "point1", "label": "自动标定与参数调优", "keywords": ["calibration", "bayesian"]}
                        ]
                    }
                ]
            }
        ]
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_LIBRARY_DIR", library_dir)
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_RUNTIME_FILE", runtime_file)
    monkeypatch.setattr(arxiv_intel, "_taxonomy_library_cache", {})
    monkeypatch.setattr(arxiv_intel, "_taxonomy_runtime_cache", {})
    libraries = arxiv_intel._load_taxonomy_engineer_libraries(force=True)
    assert libraries["measurement_control"]["library_id"] == "taxonomy_engineer_measurement_control_v1"
    assert libraries["measurement_control"]["lanes"][0]["modules"][0]["points"][0]["label"] == "自动标定与参数调优"


def test_run_taxonomy_engineer_update_writes_runtime_overlay(tmp_path, monkeypatch) -> None:
    library_dir = tmp_path / "taxonomy"
    library_dir.mkdir()
    runtime_dir = tmp_path / "runtime"
    runtime_file = runtime_dir / "runtime_overlays.json"
    pending_file = runtime_dir / "taxonomy_pending_updates.json"
    (library_dir / "measurement_control.json").write_text(json.dumps({
        "topic_id": "measurement_control",
        "library_id": "taxonomy_engineer_measurement_control_v1",
        "system_label": "量子测控技术体系",
        "review_sources": [{"id": "src1", "title": "QICK workflow", "url": "https://example.com/review", "kind": "workflow"}],
        "lanes": [
            {
                "id": "lane1",
                "label": "标定与闭环",
                "keywords": ["calibration"],
                "modules": [
                    {
                        "id": "module1",
                        "label": "机器学习闭环",
                        "keywords": ["machine learning", "readout"],
                        "points": [
                            {"id": "ml_readout", "label": "机器学习读出与状态判别", "keywords": ["machine learning", "readout fidelity", "qick"]}
                        ]
                    }
                ]
            }
        ]
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_LIBRARY_DIR", library_dir)
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_RUNTIME_FILE", runtime_file)
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_PENDING_FILE", pending_file)
    monkeypatch.setattr(arxiv_intel, "_taxonomy_library_cache", {})
    monkeypatch.setattr(arxiv_intel, "_taxonomy_runtime_cache", {})
    monkeypatch.setattr(arxiv_intel, "_taxonomy_pending_cache", {})
    monkeypatch.setattr(
        arxiv_intel,
        "_fetch_taxonomy_source_document",
        lambda _client, _source: {
            "source_id": "src1",
            "title": "QICK workflow",
            "url": "https://example.com/review",
            "kind": "workflow",
            "text": "QICK workflow for machine learning readout calibration on RFSoC hardware with hls4ml and adaptive control.",
        },
    )
    result = arxiv_intel.run_taxonomy_engineer_update(force=True)
    assert result["status"] == "pending_updated"
    saved = json.loads(pending_file.read_text(encoding="utf-8"))
    point_update = saved["updates"][0]
    assert point_update["topic_id"] == "measurement_control"
    assert point_update["point_id"] == "ml_readout"
    assert point_update["evidence_refs"][0]["source_id"] == "src1"
    assert "hls4ml" in [term.lower() for term in point_update["supplement_terms"]]


def test_approve_taxonomy_pending_update_moves_to_runtime_overlay(tmp_path, monkeypatch) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    runtime_file = runtime_dir / "runtime_overlays.json"
    pending_file = runtime_dir / "taxonomy_pending_updates.json"
    pending_file.write_text(json.dumps({
        "updated_at": "2026-03-30T00:00:00Z",
        "updates": [
            {
                "update_id": "taxupd_123",
                "topic_id": "measurement_control",
                "library_id": "taxonomy_engineer_measurement_control_v1",
                "point_id": "ml_readout",
                "supplement_terms": ["hls4ml"],
                "evidence_refs": [{"source_id": "src1", "title": "QICK workflow", "url": "https://example.com"}],
            }
        ],
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_RUNTIME_FILE", runtime_file)
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_PENDING_FILE", pending_file)
    monkeypatch.setattr(arxiv_intel, "_taxonomy_runtime_cache", {})
    monkeypatch.setattr(arxiv_intel, "_taxonomy_pending_cache", {})
    result = arxiv_intel.approve_taxonomy_pending_update("taxupd_123", reviewer="tester", note="looks good")
    assert result["status"] == "approved"
    runtime = json.loads(runtime_file.read_text(encoding="utf-8"))
    assert "hls4ml" in runtime["libraries"]["measurement_control"]["point_updates"]["ml_readout"]["supplement_terms"]
    pending = json.loads(pending_file.read_text(encoding="utf-8"))
    assert pending["updates"] == []


def test_reject_taxonomy_pending_update_removes_from_pending_pool(tmp_path, monkeypatch) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    pending_file = runtime_dir / "taxonomy_pending_updates.json"
    pending_file.write_text(json.dumps({
        "updated_at": "2026-03-30T00:00:00Z",
        "updates": [{"update_id": "taxupd_456", "topic_id": "chip_design", "point_id": "transmon_design"}],
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr(arxiv_intel, "TAXONOMY_PENDING_FILE", pending_file)
    monkeypatch.setattr(arxiv_intel, "_taxonomy_pending_cache", {})
    result = arxiv_intel.reject_taxonomy_pending_update("taxupd_456", reviewer="tester", note="noise")
    assert result["status"] == "rejected"
    pending = json.loads(pending_file.read_text(encoding="utf-8"))
    assert pending["updates"] == []


def test_build_bilingual_digest_text_contains_bullets_and_bilingual_summary() -> None:
    record = arxiv_intel._parse_feed(SAMPLE_FEED)[0]
    record["matched_topics"] = ["measurement_control"]
    record["technical_route"] = arxiv_intel._extract_technical_route(record["summary"])
    record["core_conclusion"] = arxiv_intel._extract_conclusion(record["summary"])
    record["summary_cn"] = "研究主题：超导量子比特读出标定。技术路线：机器学习 + 自适应脉冲优化。结论：缩短标定时间。"
    record["source"] = "arXiv RSS"
    record["retrieval_backend"] = "live-rss"
    record["paper_id"] = "paper-1"
    arxiv_intel._translation_cache["paper-1"] = {
        "title_zh": "AI辅助超导量子比特读出标定",
        "summary_zh": "我们将英文摘要准确翻译为中文。",
    }
    text = arxiv_intel.build_bilingual_digest_text([record])
    assert "中文摘要" in text
    assert "English Abstract" in text
    assert "中文标题: AI辅助超导量子比特读出标定" in text
    assert "1. AI-assisted superconducting qubit readout calibration" in text
    assert "- 来源 / Source: arXiv RSS / arXiv RSS" in text


def test_build_feishu_card_contains_header_and_paper_sections(monkeypatch) -> None:
    record = arxiv_intel._parse_feed(SAMPLE_FEED)[0]
    record["matched_topics"] = ["measurement_control"]
    record["technical_route"] = arxiv_intel._extract_technical_route(record["summary"])
    record["core_conclusion"] = arxiv_intel._extract_conclusion(record["summary"])
    record["summary_cn"] = "研究主题：超导量子比特读出标定。技术路线：机器学习。结论：提升读出保真度。"
    record["source"] = "arXiv RSS"
    record["retrieval_backend"] = "live-rss"
    record["importance"] = "high"
    monkeypatch.setattr(
        arxiv_intel,
        "_translate_record",
        lambda _record: {
            "title_zh": "AI辅助超导量子比特读出标定",
            "summary_zh": "这是一段中文摘要。",
        },
    )
    report = arxiv_intel.build_report_payload([record], report_date="2026-03-29")
    card = arxiv_intel._build_feishu_card(report)
    assert card["header"]["title"]["content"]
    assert card["elements"][0]["tag"] == "div"
    full_content = "\n".join(item.get("text", {}).get("content", "") for item in card["elements"] if item.get("tag") == "div")
    assert "中文标题" in full_content
    assert "AI辅助超导量子比特读出标定" in full_content
    assert "英文标题" in full_content
    assert "AI-assisted superconducting qubit readout calibration" in full_content
    assert "作者信息" in full_content
    assert "第一作者 Alice" in full_content
    assert "通讯作者 源数据未提供" in full_content
    assert "Alice" in full_content
    assert "源数据未提供" in full_content
    assert "杂志/会议" in full_content
    assert "arXiv 预印本" in full_content
    assert "量子测控" in full_content
    assert "中文摘要" in full_content
    assert "原文链接" in full_content
    assert "English Abstract" in full_content
    assert "热点主题区" not in full_content
    assert "专题分栏" not in full_content
    assert "优先级" not in full_content


def test_build_feishu_card_includes_uploaded_images(monkeypatch) -> None:
    record = arxiv_intel._parse_feed(SAMPLE_FEED)[0]
    record["matched_topics"] = ["measurement_control"]
    monkeypatch.setattr(
        arxiv_intel,
        "_translate_record",
        lambda _record: {"title_zh": "中文标题", "summary_zh": "中文摘要"},
    )
    report = arxiv_intel.build_report_payload([record], report_date="2026-03-29")
    report["top_papers"][0]["tech_route_graph"]["method_figure"] = {"caption": "Figure 1: Quantum control system structure."}
    card = arxiv_intel._build_feishu_card(
        report,
        record=report["top_papers"][0],
        index=1,
        total=1,
        image_keys={"tech_system_map": "img_system", "tech_route_graph": "img_route", "method_figure": "img_method"},
    )
    image_blocks = [item for item in card["elements"] if item.get("tag") == "img"]
    assert len(image_blocks) == 3
    assert image_blocks[0]["img_key"] == "img_system"
    assert image_blocks[1]["img_key"] == "img_route"
    assert image_blocks[2]["img_key"] == "img_method"


def test_parse_ar5iv_method_figure_prefers_architecture_diagram() -> None:
    html = """
    <html><body>
      <figure class="ltx_figure"><img src="/html/2408.06469/assets/x1.png"/><figcaption>Figure 1: The architecture of the quantum engine compiler and control system.</figcaption></figure>
      <figure class="ltx_figure"><img src="/html/2408.06469/assets/x2.png"/><figcaption>Figure 2: Benchmark results across routing settings.</figcaption></figure>
    </body></html>
    """
    record = {
        "title": "Design and architecture of the IBM Quantum Engine Compiler",
        "summary": "We present a compiler architecture and control system for superconducting quantum processors.",
        "matched_topics": ["quantum_computing"],
    }
    result = arxiv_intel._parse_ar5iv_method_figure(html, "https://ar5iv.labs.arxiv.org/html/2408.06469v1", record)
    assert result["source"] == "ar5iv"
    assert result["image_url"].endswith("/html/2408.06469/assets/x1.png")
    assert "architecture" in result["caption"].lower()


def test_parse_ar5iv_method_figure_prefers_primary_keywords_over_generic_system() -> None:
    html = """
    <html><body>
      <figure class="ltx_figure"><img src="/html/2501.06993/assets/x1.png"/><figcaption>Figure 1: System diagram for the compilation service.</figcaption></figure>
      <figure class="ltx_figure"><img src="/html/2501.06993/assets/x2.png"/><figcaption>Figure 2: QSteed workflow for resource-virtualized compilation.</figcaption></figure>
    </body></html>
    """
    record = {
        "title": "QSteed framework for quantum compilation",
        "summary": "We present a workflow and framework for hardware-aware quantum compilation.",
        "matched_topics": ["quantum_computing"],
    }
    result = arxiv_intel._parse_ar5iv_method_figure(html, "https://ar5iv.labs.arxiv.org/html/2501.06993v2", record)
    assert result["image_url"].endswith("/html/2501.06993/assets/x2.png")
    assert "workflow" in result["caption"].lower()


def test_parse_ar5iv_method_figure_rejects_results_only_diagram() -> None:
    html = """
    <html><body>
      <figure class="ltx_figure"><img src="/html/2501.06993/assets/x3.png"/><figcaption>Figure 3: Benchmark results and latency comparison across baselines.</figcaption></figure>
    </body></html>
    """
    record = {
        "title": "Quantum compiler evaluation",
        "summary": "We benchmark compilation quality and runtime across hardware-aware baselines.",
        "matched_topics": ["quantum_computing"],
    }
    result = arxiv_intel._parse_ar5iv_method_figure(html, "https://ar5iv.labs.arxiv.org/html/2501.06993v2", record)
    assert result == {}


def test_upload_feishu_image_retries_on_transient_disconnect(monkeypatch) -> None:
    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"code": 0, "data": {"image_key": "img_retry_ok"}}

    class FakeClient:
        calls = 0

        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, *args, **kwargs):
            FakeClient.calls += 1
            if FakeClient.calls == 1:
                raise arxiv_intel.httpx.RemoteProtocolError("Server disconnected without sending a response.")
            return FakeResponse()

    monkeypatch.setattr(arxiv_intel, "_get_feishu_tenant_access_token", lambda: "token")
    monkeypatch.setattr(arxiv_intel.httpx, "Client", FakeClient)
    monkeypatch.setattr(arxiv_intel.time, "sleep", lambda _seconds: None)
    image_key = arxiv_intel._upload_feishu_image(b"fake-png")
    assert image_key == "img_retry_ok"
    assert FakeClient.calls == 2


def test_build_feishu_text_payload_prefixes_keyword(monkeypatch) -> None:
    monkeypatch.setattr(arxiv_intel.config, "INTEL_FEISHU_KEYWORD", "量子")
    payload = arxiv_intel._build_feishu_text_payload("日报正文")
    assert payload["msg_type"] == "text"
    assert payload["content"]["text"].startswith("量子\n日报正文")


def test_translate_record_async_uses_strict_chinese_translation(monkeypatch) -> None:
    class FakeBrain:
        def __init__(self) -> None:
            self.calls = 0

        async def chat(self, messages, stream=False):
            self.calls += 1
            if self.calls == 1:
                yield "Original English Title"
            elif self.calls == 2:
                yield "中文标题"
            elif self.calls == 3:
                yield "Original English Abstract"
            else:
                yield "这是准确的中文摘要。"

    monkeypatch.setattr(arxiv_intel, "_translation_cache", {})
    fake_brain = FakeBrain()
    monkeypatch.setattr(brain_module, "get_brain", lambda: fake_brain)
    result = __import__("asyncio").run(arxiv_intel._translate_record_async({"paper_id": "p1", "title": "English", "summary": "Summary"}))
    assert result["title_zh"] == "中文标题"
    assert result["summary_zh"] == "这是准确的中文摘要。"


def test_translate_record_async_avoids_english_in_chinese_fields(monkeypatch) -> None:
    class FakeBrain:
        async def chat(self, messages, stream=False):
            yield "Still English"

    monkeypatch.setattr(arxiv_intel, "_translation_cache", {})
    monkeypatch.setattr(brain_module, "get_brain", lambda: FakeBrain())
    result = __import__("asyncio").run(
        arxiv_intel._translate_record_async(
            {"paper_id": "p2", "title": "Original English Title", "summary": "Original English Abstract"}
        )
    )
    assert "暂不可用" in result["title_zh"]
    assert "暂不可用" in result["summary_zh"]


def test_get_report_window_spans_previous_24_hours() -> None:
    report_at = datetime.fromisoformat("2026-03-29T09:00:00+08:00")
    start_utc, end_utc = arxiv_intel.get_report_window(report_at)
    assert int((end_utc - start_utc).total_seconds()) == 24 * 3600
    assert end_utc.isoformat().startswith("2026-03-29T01:00:00")


def test_route_recent_paper_queries_to_intel_officer() -> None:
    assert _route("列出最近检索到的量子芯片与量子计算相关论文") == "intel_officer"


def test_fallback_recent_papers_filters_cached_window(monkeypatch) -> None:
    cached = [
        {
            "paper_id": "p1",
            "title": "Recent chip design paper",
            "published": "2026-03-29T00:30:00Z",
            "matched_topics": ["chip_design"],
            "summary": "superconducting qubit chip design",
        },
        {
            "paper_id": "p2",
            "title": "Old paper",
            "published": "2026-03-20T00:30:00Z",
            "matched_topics": ["quantum_error_correction"],
            "summary": "surface code error correction",
        },
    ]
    monkeypatch.setattr(arxiv_intel.state_store, "list_intel_papers", lambda limit=300: cached)
    start_utc = datetime.fromisoformat("2026-03-28T01:00:00+00:00")
    end_utc = datetime.fromisoformat("2026-03-29T01:00:00+00:00")
    results = arxiv_intel._fallback_recent_papers(start_utc, end_utc)
    assert len(results) == 1
    assert results[0]["paper_id"] == "p1"
    assert results[0]["retrieval_backend"] == "cache"


def test_dedupe_records_merges_topics() -> None:
    records = [
        {"paper_id": "p1", "matched_topics": ["chip_design"], "authors": [], "summary": "", "corresponding_author": ""},
        {"paper_id": "p1", "matched_topics": ["quantum_error_correction"], "authors": ["Alice", "Bob"], "summary": "surface code", "corresponding_author": "Bob"},
    ]
    merged = arxiv_intel._dedupe_records(records)
    assert len(merged) == 1
    assert set(merged[0]["matched_topics"]) == {"chip_design", "quantum_error_correction"}
    assert merged[0]["authors"] == ["Alice", "Bob"]
    assert merged[0]["corresponding_author"] == "Bob"
    assert merged[0]["summary"] == "surface code"


def test_crossref_noise_is_filtered_outside_quantum_context() -> None:
    record = {
        "paper_id": "noise1",
        "title": "Vector error correction model for economic indicators",
        "summary": "",
        "published": "2026-03-28T00:00:00Z",
        "categories": [],
        "source": "Crossref",
    }
    start_utc = datetime.fromisoformat("2026-03-27T00:00:00+00:00")
    end_utc = datetime.fromisoformat("2026-03-29T00:00:00+00:00")
    assert arxiv_intel._normalize_live_record(record, start_utc, end_utc, backend="live-crossref") is None


def test_arxiv_noise_is_filtered_for_wireless_antenna_paper() -> None:
    record = {
        "paper_id": "noise2",
        "title": "Antenna Elements' Trajectory Optimization for Throughput Maximization in Continuous-Trajectory Fluid Antenna-Aided Wireless Communications",
        "summary": "We optimize antenna trajectories for wireless communications throughput.",
        "published": "2026-03-28T00:00:00Z",
        "categories": ["eess.SP"],
        "source": "arXiv",
    }
    start_utc = datetime.fromisoformat("2026-03-27T00:00:00+00:00")
    end_utc = datetime.fromisoformat("2026-03-29T00:00:00+00:00")
    assert arxiv_intel._normalize_live_record(record, start_utc, end_utc, backend="live-api") is None


def test_ai_agent_crossref_record_is_retained() -> None:
    record = {
        "paper_id": "agent1",
        "title": "Multi-agent tool use with large language models",
        "summary": "We present an AI agent workflow with memory and tool use for software tasks.",
        "published": "2026-03-28T00:00:00Z",
        "categories": ["cs.AI"],
        "source": "Crossref",
    }
    start_utc = datetime.fromisoformat("2026-03-27T00:00:00+00:00")
    end_utc = datetime.fromisoformat("2026-03-29T00:00:00+00:00")
    normalized = arxiv_intel._normalize_live_record(record, start_utc, end_utc, backend="live-crossref")
    assert normalized is not None
    assert "ai_agents" in normalized["matched_topics"]


def test_parse_openalex_items_reconstructs_abstract() -> None:
    data = {
        "results": [
            {
                "id": "https://openalex.org/W123",
                "display_name": "OpenAlex superconducting qubit paper",
                "abstract_inverted_index": {"superconducting": [0], "qubit": [1], "control": [2]},
                "publication_date": "2026-03-28",
                "authorships": [{"author": {"display_name": "Alice"}}],
                "primary_location": {"landing_page_url": "https://example.org/paper"},
                "primary_topic": {"display_name": "Quantum computing"},
                "concepts": [{"display_name": "Superconducting qubit"}],
            }
        ]
    }
    records = arxiv_intel._parse_openalex_items(data)
    assert len(records) == 1
    record = records[0]
    assert record["source"] == "OpenAlex"
    assert record["summary"] == "superconducting qubit control"
    assert record["published"].startswith("2026-03-28T00:00:00")


def test_csai_category_falls_back_to_ai_agents_topic() -> None:
    record = {
        "title": "Agentic planning for code generation",
        "summary": "",
        "categories": ["cs.AI"],
    }
    assert arxiv_intel._ensure_topics(record) == ["ai_agents"]


def test_select_formal_track_records_prefers_matching_quantum_lane() -> None:
    records = [
        {
            "paper_id": "c1",
            "title": "Transmon coupler design for scalable superconducting quantum processors",
            "summary": "We present a chip layout and resonator coupler design for superconducting qubits.",
            "matched_topics": ["chip_design"],
            "published": "2026-03-29T00:00:00Z",
            "source": "OpenAlex",
        },
        {
            "paper_id": "q1",
            "title": "Surface code decoder with logical qubit benchmarks",
            "summary": "We evaluate a decoder for fault-tolerant logical qubits.",
            "matched_topics": ["quantum_error_correction"],
            "published": "2026-03-29T00:00:00Z",
            "source": "OpenAlex",
        },
    ]
    selected = arxiv_intel.select_formal_track_records(records, "chip_design", limit=4)
    assert len(selected) == 1
    assert selected[0]["paper_id"] == "c1"


def test_build_formal_track_reports_creates_three_lane_titles() -> None:
    records = [
        {
            "paper_id": "a1",
            "title": "Multi-agent tool use and memory orchestration for coding workflows",
            "summary": "We present an agentic workflow with tool use, planning, and evaluation.",
            "matched_topics": ["ai_agents"],
            "published": "2026-03-29T00:00:00Z",
            "source": "OpenAlex",
        },
        {
            "paper_id": "c1",
            "title": "Transmon coupler design for scalable superconducting quantum processors",
            "summary": "We present a chip layout and resonator coupler design for superconducting qubits.",
            "matched_topics": ["chip_design"],
            "published": "2026-03-29T00:00:00Z",
            "source": "OpenAlex",
        },
        {
            "paper_id": "q1",
            "title": "Surface code decoder with logical qubit benchmarks",
            "summary": "We evaluate a decoder for fault-tolerant logical qubits.",
            "matched_topics": ["quantum_error_correction"],
            "published": "2026-03-29T00:00:00Z",
            "source": "OpenAlex",
        },
        {
            "paper_id": "m1",
            "title": "Readout calibration and Ramsey control for fixed-frequency transmons",
            "summary": "We improve readout fidelity and microwave pulse calibration for superconducting qubits.",
            "matched_topics": ["measurement_control"],
            "published": "2026-03-29T00:00:00Z",
            "source": "OpenAlex",
        },
        {
            "paper_id": "qc1",
            "title": "Quantum processor architecture benchmark for compiler mapping",
            "summary": "We benchmark quantum architecture and compiler mapping strategies.",
            "matched_topics": ["quantum_computing"],
            "published": "2026-03-29T00:00:00Z",
            "source": "OpenAlex",
        },
        {
            "paper_id": "qa1",
            "title": "Quantum chemistry algorithm benchmark for simulation workflows",
            "summary": "We study quantum chemistry and optimization algorithms for realistic simulation workloads.",
            "matched_topics": ["quantum_application"],
            "published": "2026-03-29T00:00:00Z",
            "source": "OpenAlex",
        },
    ]
    reports = arxiv_intel.build_formal_track_reports(records, report_date="2026-03-29")
    assert reports["ai_agents"]["card_title"] == "QuantaMind AI/智能体日报"
    assert reports["chip_design"]["card_title"] == "QuantaMind 芯片设计日报"
    assert reports["quantum_error_correction"]["card_title"] == "QuantaMind 量子纠错日报"
    assert reports["quantum_computing"]["card_title"] == "QuantaMind 量子计算日报"
    assert reports["measurement_control"]["card_title"] == "QuantaMind 测控与读出日报"
    assert reports["quantum_application"]["card_title"] == "QuantaMind 量子应用与算法日报"


def test_warm_recent_cache_persists_only_live_records(monkeypatch) -> None:
    source_records = [
        {"paper_id": "live1", "retrieval_backend": "live-openalex"},
        {"paper_id": "cache1", "retrieval_backend": "cache"},
    ]
    persisted = []
    monkeypatch.setattr(arxiv_intel, "fetch_recent_papers", lambda days_back=None, max_per_topic=6: source_records)
    monkeypatch.setattr(arxiv_intel, "persist_paper", lambda record: persisted.append(record["paper_id"]))
    result = arxiv_intel.warm_recent_cache(days_back=5, max_per_topic=6)
    assert result["status"] == "warmed"
    assert result["records_count"] == 2
    assert result["live_records_count"] == 1
    assert persisted == ["live1"]


def test_run_daily_digest_falls_back_to_cached_papers_when_live_fetch_fails(monkeypatch) -> None:
    now_local = datetime.fromisoformat("2026-03-29T09:00:00+08:00")
    cached_records = [
        {
            "paper_id": "cache-p1",
            "arxiv_id": "cache-p1",
            "title": "Cached superconducting calibration paper",
            "summary": "We present adaptive pulse optimization for superconducting qubit readout calibration and improve fidelity.",
            "published": "2026-03-29T00:20:00Z",
            "updated": "2026-03-29T00:20:00Z",
            "authors": ["Alice"],
            "corresponding_author": "Alice",
            "categories": ["quant-ph"],
            "primary_category": "quant-ph",
            "matched_topics": ["measurement_control"],
            "source": "arXiv RSS",
            "retrieval_backend": "cache",
        }
    ]
    upserted = {}
    memory_logs = []

    monkeypatch.setattr(arxiv_intel, "_local_now", lambda: now_local)
    monkeypatch.setattr(arxiv_intel, "fetch_recent_papers", lambda **_kwargs: (_ for _ in ()).throw(TimeoutError("arxiv timeout")))
    monkeypatch.setattr(arxiv_intel, "_fallback_recent_papers", lambda _start, _end: cached_records)
    monkeypatch.setattr(arxiv_intel, "send_feishu_report", lambda report, webhook_url=None: {"status": "sent", "reason": ""})
    monkeypatch.setattr(arxiv_intel.state_store, "get_intel_report", lambda report_id: None)
    monkeypatch.setattr(arxiv_intel.state_store, "upsert_intel_report", lambda report_id, payload: upserted.setdefault(report_id, payload))
    monkeypatch.setattr(arxiv_intel.memory, "append_memory", lambda text, project_id="default": memory_logs.append((project_id, text)))

    result = arxiv_intel.run_daily_digest(force=False)

    assert result["status"] == "created_from_cache"
    report = result["report"]
    assert report["report_id"] == "intel-2026-03-29"
    assert report["source_mode"] == "cache_fallback"
    assert report["delivery"]["feishu"]["status"] == "sent"
    assert report["top_papers"][0]["paper_id"] == "cache-p1"
    assert "来源模式：cache_fallback" in memory_logs[0][1]
    assert upserted["intel-2026-03-29"]["source_mode"] == "cache_fallback"
