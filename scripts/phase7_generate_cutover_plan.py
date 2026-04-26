#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "templates" / "Phase7_正式切换窗口与值班预案模板.md"


def now_local() -> datetime:
    return datetime.now()


def render_template(text: str, mapping: dict[str, str]) -> str:
    output = text
    for key, value in mapping.items():
        output = output.replace("{{" + key + "}}", value)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Phase7 formal cutover window plan from template.")
    parser.add_argument("--date", default=now_local().strftime("%Y-%m-%d"), help="Cutover date (YYYY-MM-DD)")
    parser.add_argument("--version", default="v2-cutover", help="Cutover version label")
    parser.add_argument("--window-start", default="20:00", help="Cutover start time (HH:MM)")
    parser.add_argument("--window-end", default="23:00", help="Cutover end time (HH:MM)")
    parser.add_argument("--commander", default="release-manager", help="Incident commander")
    parser.add_argument("--dev-oncall", default="dev-oncall", help="Development oncall")
    parser.add_argument("--qa-oncall", default="qa-oncall", help="QA oncall")
    parser.add_argument("--ops-oncall", default="ops-oncall", help="Ops oncall")
    parser.add_argument("--output", default="", help="Output markdown file path")
    args = parser.parse_args()

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE_PATH}")

    date_stamp = args.date.replace("-", "")
    default_output = ROOT / "docs" / "reports" / "cutover-plan" / f"{date_stamp}_正式切换窗口与值班预案.md"
    output_path = Path(args.output) if args.output else default_output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = render_template(
        template,
        {
            "DATE": args.date,
            "VERSION": args.version,
            "WINDOW_START": args.window_start,
            "WINDOW_END": args.window_end,
            "COMMANDER": args.commander,
            "DEV_ONCALL": args.dev_oncall,
            "QA_ONCALL": args.qa_oncall,
            "OPS_ONCALL": args.ops_oncall,
        },
    )
    output_path.write_text(rendered, encoding="utf-8")
    print(f"[phase7-cutover-plan] generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
