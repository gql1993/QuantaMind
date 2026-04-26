#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "templates" / "Phase7_归档索引模板.md"


def now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def render(text: str, mapping: dict[str, str]) -> str:
    output = text
    for key, val in mapping.items():
        output = output.replace("{{" + key + "}}", val)
    return output


def collect_files(root: Path) -> list[dict[str, Any]]:
    mapping: list[tuple[str, str, str]] = [
        ("drills", "phase7_observability_guard_latest.json", "docs/reports/phase7_observability_guard_latest.json"),
        ("drills", "phase7_canary_rollout_latest.json", "docs/reports/phase7_canary_rollout_latest.json"),
        ("drills", "phase7_pre_cutover_drill_latest.json", "docs/reports/phase7_pre_cutover_drill_latest.json"),
        ("drills", "phase7_rollback_drill_latest.json", "docs/reports/phase7_rollback_drill_latest.json"),
        ("reviews", "phase7_biweekly_stability_review_latest.json", "docs/reports/phase7_biweekly_stability_review_latest.json"),
        ("reviews", "phase7_biweekly_stability_review_latest.md", "docs/reports/phase7_biweekly_stability_review_latest.md"),
        ("reviews", "phase7_quarterly_regression_audit_latest.json", "docs/reports/phase7_quarterly_regression_audit_latest.json"),
        ("reviews", "phase7_quarterly_regression_audit_latest.md", "docs/reports/phase7_quarterly_regression_audit_latest.md"),
        ("reviews", "phase7_quarterly_regression_signoff_latest.md", "docs/reports/phase7_quarterly_regression_signoff_latest.md"),
        ("reviews", "phase7_version_change_audit_latest.json", "docs/reports/phase7_version_change_audit_latest.json"),
        ("reviews", "phase7_version_change_audit_latest.md", "docs/reports/phase7_version_change_audit_latest.md"),
        ("reviews", "phase7_version_accountability_trace_latest.md", "docs/reports/phase7_version_accountability_trace_latest.md"),
    ]

    files: list[dict[str, Any]] = []
    for group, name, rel in mapping:
        src = root / rel
        files.append(
            {
                "group": group,
                "name": name,
                "source_rel": rel,
                "exists": src.exists(),
            }
        )

    postmortem_dir = root / "docs" / "reports" / "postmortem-pack"
    if postmortem_dir.exists():
        for p in sorted(postmortem_dir.glob("*.md")):
            files.append(
                {
                    "group": "postmortem",
                    "name": p.name,
                    "source_rel": str(p.relative_to(root)).replace("\\", "/"),
                    "exists": True,
                }
            )
    return files


def sync_file(src: Path, dst: Path, mode: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if mode == "move":
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive Phase7 drill/release materials with naming convention.")
    parser.add_argument("--archive-id", default=datetime.now().strftime("%Y%m%d"), help="Archive batch id, e.g. 20260410")
    parser.add_argument("--version", default="v2-cutover", help="Version label")
    parser.add_argument("--owner", default="release-manager", help="Archive owner")
    parser.add_argument("--mode", choices=["copy", "move"], default="copy", help="Archive mode")
    parser.add_argument("--archive-root", default="docs/archive/phase7", help="Archive root directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not write files")
    args = parser.parse_args()

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE_PATH}")

    files = collect_files(ROOT)
    missing = [item for item in files if not item["exists"]]
    archive_root = ROOT / args.archive_root / args.archive_id

    plan_lines = [f"[phase7-archive] mode={args.mode} archive={archive_root}"]
    for item in files:
        mark = "ok" if item["exists"] else "missing"
        plan_lines.append(f" - [{mark}] {item['source_rel']} -> {item['group']}/{item['name']}")

    if args.dry_run:
        print("\n".join(plan_lines))
        if missing:
            print(f"[phase7-archive] warning: missing files={len(missing)}")
        return 0

    written: list[dict[str, str]] = []
    for item in files:
        if not item["exists"]:
            continue
        src = ROOT / item["source_rel"]
        dst = archive_root / item["group"] / item["name"]
        sync_file(src, dst, args.mode)
        written.append(
            {
                "group": item["group"],
                "name": item["name"],
                "source_rel": item["source_rel"],
                "archive_rel": str(dst.relative_to(ROOT)).replace("\\", "/"),
            }
        )

    manifest = {
        "archive_id": args.archive_id,
        "date": now_date(),
        "version": args.version,
        "owner": args.owner,
        "mode": args.mode,
        "archive_root": str(archive_root.relative_to(ROOT)).replace("\\", "/"),
        "written_count": len(written),
        "missing_count": len(missing),
        "written_files": written,
        "missing_files": [item["source_rel"] for item in missing],
    }
    manifest_path = archive_root / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    file_rows = "\n".join(
        f"| {item['group']} | {item['name']} | `{item['source_rel']}` |" for item in written
    ) or "| - | - | - |"
    index_text = render(
        TEMPLATE_PATH.read_text(encoding="utf-8"),
        {
            "ARCHIVE_ID": args.archive_id,
            "DATE": now_date(),
            "VERSION": args.version,
            "OWNER": args.owner,
            "MODE": args.mode,
            "ARCHIVE_ROOT": str(archive_root.relative_to(ROOT)).replace("\\", "/"),
            "FILE_ROWS": file_rows,
        },
    )
    index_path = archive_root / "ARCHIVE_INDEX.md"
    index_path.write_text(index_text, encoding="utf-8")

    print(f"[phase7-archive] archived={len(written)} missing={len(missing)} root={archive_root}")
    print(f"[phase7-archive] manifest={manifest_path}")
    print(f"[phase7-archive] index={index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
