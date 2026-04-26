# 统一输出管理器 — 所有环节产出的文件自动保存到 outputs 目录 + 资料库
# 覆盖：设计（GDS/掩膜）、仿真（Ansys/Sonnet）、制造（工艺/良率/SPC 报告）、
#       校准（参数）、测控（测量数据）、数据（导出/血缘）

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from quantamind import config

_log = logging.getLogger("quantamind.output_manager")

OUTPUT_DIR = config.DEFAULT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_output_records = []


def save_output(filename: str, content: Any, category: str = "其他",
                pipeline_id: str = "", step_title: str = "") -> Dict[str, Any]:
    """保存任意输出文件到统一目录 + 资料库"""
    cat_dir = OUTPUT_DIR / category.replace("/", "_").replace(" ", "_")
    cat_dir.mkdir(parents=True, exist_ok=True)
    filepath = str(cat_dir / filename)

    if isinstance(content, bytes):
        with open(filepath, "wb") as f:
            f.write(content)
    elif isinstance(content, str):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    elif isinstance(content, (dict, list)):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2, default=str)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(content))

    size = os.path.getsize(filepath)

    record = {
        "filename": filename, "category": category, "path": filepath,
        "size_bytes": size, "pipeline_id": pipeline_id, "step": step_title,
        "saved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _output_records.append(record)

    # 同步到资料库
    try:
        from quantamind.server import project_library as lib
        with open(filepath, "rb") as f:
            lib.save_file(filename, f.read(), project_id="default", folder_id="")
    except Exception as e:
        _log.warning("保存到资料库失败: %s", e)

    _log.info("输出保存: [%s] %s (%d bytes)", category, filename, size)
    return {"saved": filepath, "filename": filename, "category": category, "size_bytes": size}


def save_json_output(name: str, data: dict, category: str = "数据", **kwargs) -> Dict:
    """保存 JSON 格式输出"""
    filename = name if name.endswith(".json") else name + ".json"
    return save_output(filename, data, category, **kwargs)


def save_csv_output(name: str, headers: list, rows: list, category: str = "数据", **kwargs) -> Dict:
    """保存 CSV 格式输出"""
    import csv, io
    filename = name if name.endswith(".csv") else name + ".csv"
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return save_output(filename, buf.getvalue(), category, **kwargs)


def save_report(name: str, content: str, category: str = "报告", **kwargs) -> Dict:
    """保存文本/Markdown 报告"""
    return save_output(name, content, category, **kwargs)


def list_outputs(category: Optional[str] = None) -> list:
    if category:
        return [r for r in _output_records if r["category"] == category]
    return list(_output_records)


def get_stats() -> dict:
    by_cat = {}
    for r in _output_records:
        c = r["category"]
        by_cat.setdefault(c, {"count": 0, "size": 0})
        by_cat[c]["count"] += 1
        by_cat[c]["size"] += r["size_bytes"]
    return {"total_outputs": len(_output_records), "by_category": by_cat}
