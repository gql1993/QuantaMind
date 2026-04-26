#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase10_产物索引报告模板.md"


def render(text: str, mapping: dict[str, str]) -> str:
    out = text
    for k, v in mapping.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 10 artifact lineage index generator.")
    parser.add_argument("--output-json", default="docs/reports/phase10_artifact_index_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase10_artifact_index_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    reports = sorted((ROOT / "docs" / "reports").glob("**/*.*"))
    archives = sorted((ROOT / "docs" / "archive").glob("**/*.*")) if (ROOT / "docs" / "archive").exists() else []

    entries = []
    for p in reports:
        if p.is_file():
            entries.append(
                {
                    "category": "report",
                    "file": str(p.relative_to(ROOT)).replace("\\", "/"),
                    "note": "runtime/generated report",
                }
            )
    for p in archives:
        if p.is_file():
            entries.append(
                {
                    "category": "archive",
                    "file": str(p.relative_to(ROOT)).replace("\\", "/"),
                    "note": "archived evidence",
                }
            )

    out = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "report_count": len([x for x in entries if x["category"] == "report"]),
            "archive_count": len([x for x in entries if x["category"] == "archive"]),
            "index_count": len(entries),
        },
        "entries": entries,
    }

    preview = entries[:80]
    table = "\n".join(f"| {e['category']} | `{e['file']}` | {e['note']} |" for e in preview)
    if len(entries) > len(preview):
        table += "\n| ... | ... | ... |"

    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "SCOPE": "`docs/reports` + `docs/archive`",
            "REPORT_COUNT": str(out["summary"]["report_count"]),
            "ARCHIVE_COUNT": str(out["summary"]["archive_count"]),
            "INDEX_COUNT": str(out["summary"]["index_count"]),
            "INDEX_TABLE": table if table else "| - | - | - |",
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase10-artifact-index] entries={len(entries)} json={out_json} markdown={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
