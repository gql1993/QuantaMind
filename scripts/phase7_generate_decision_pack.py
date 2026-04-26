#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "docs" / "templates"
OUTPUT_DIR = ROOT / "docs" / "reports" / "decision-pack"


def now_local() -> datetime:
    return datetime.now()


def render(template_text: str, *, date_text: str, version: str, owner: str) -> str:
    return (
        template_text.replace("{{DATE}}", date_text)
        .replace("{{VERSION}}", version)
        .replace("{{OWNER}}", owner)
    )


def generate_pack(*, version: str, owner: str, output_dir: Path) -> list[Path]:
    date_text = now_local().strftime("%Y-%m-%d")
    stamp = now_local().strftime("%Y%m%d")
    output_dir.mkdir(parents=True, exist_ok=True)

    mapping = {
        "Phase7_发布决策记录模板.md": f"{stamp}_发布决策记录.md",
        "Phase7_回退决策记录模板.md": f"{stamp}_回退决策记录.md",
        "Phase7_切换评审会议纪要模板.md": f"{stamp}_切换评审会议纪要.md",
    }

    written: list[Path] = []
    for template_name, output_name in mapping.items():
        template_path = TEMPLATE_DIR / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"template not found: {template_path}")
        text = template_path.read_text(encoding="utf-8")
        rendered = render(text, date_text=date_text, version=version, owner=owner)
        target = output_dir / output_name
        target.write_text(rendered, encoding="utf-8")
        written.append(target)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Phase7 decision review material pack from templates.")
    parser.add_argument("--version", default="v2-canary", help="Release/cutover version label")
    parser.add_argument("--owner", default="release-manager", help="Default owner field")
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory to write generated decision files",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    files = generate_pack(version=args.version, owner=args.owner, output_dir=output_dir)
    print("[phase7-decision-pack] generated:")
    for path in files:
        print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
