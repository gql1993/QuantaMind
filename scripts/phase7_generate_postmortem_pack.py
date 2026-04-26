#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "docs" / "templates"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "reports" / "postmortem-pack"


def now_local() -> datetime:
    return datetime.now()


def render(text: str, mapping: dict[str, str]) -> str:
    out = text
    for k, v in mapping.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Phase7 postmortem templates pack.")
    parser.add_argument("--date", default=now_local().strftime("%Y-%m-%d"), help="Postmortem date (YYYY-MM-DD)")
    parser.add_argument("--version", default="v2-cutover", help="Version/cutover label")
    parser.add_argument("--owner", default="incident-manager", help="Postmortem owner")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    template_mapping = {
        "Phase7_切换后复盘报告模板.md": "切换后复盘报告",
        "Phase7_问题分级与改进跟踪模板.md": "问题分级与改进跟踪",
        "Phase7_复盘行动项台账模板.md": "复盘行动项台账",
    }

    date_stamp = args.date.replace("-", "")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for template_name, label in template_mapping.items():
        template_path = TEMPLATE_DIR / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"template not found: {template_path}")
        target = out_dir / f"{date_stamp}_{label}.md"
        content = render(
            template_path.read_text(encoding="utf-8"),
            {
                "DATE": args.date,
                "VERSION": args.version,
                "OWNER": args.owner,
            },
        )
        target.write_text(content, encoding="utf-8")
        generated.append(target)

    print("[phase7-postmortem-pack] generated:")
    for path in generated:
        print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
