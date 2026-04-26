#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "docs" / "reports"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_cmd(cmd: list[str], *, title: str) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "title": title,
        "command": cmd,
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-12:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-12:]),
    }


def ensure_report(
    *,
    label: str,
    path: Path,
    cmd: list[str],
    force_regenerate: bool,
    allow_nonzero: bool = False,
) -> dict[str, Any]:
    existed_before = path.exists()
    should_run = force_regenerate or (not existed_before)
    result: dict[str, Any] = {
        "label": label,
        "report": str(path.relative_to(ROOT)).replace("\\", "/"),
        "existed_before": existed_before,
        "attempted": should_run,
    }
    if should_run:
        execution = run_cmd(cmd, title=label)
        result["execution"] = execution
        result["command_ok"] = bool(execution["ok"]) or allow_nonzero
    else:
        result["command_ok"] = True
    result["exists_after"] = path.exists()
    # "filled" targets archive completeness, "healthy" reflects command status.
    result["filled"] = bool(result["exists_after"])
    result["healthy"] = bool(result["command_ok"]) and bool(result["exists_after"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill missing Phase7 drill reports, then archive materials in one command."
    )
    parser.add_argument("--v1-base", default="http://127.0.0.1:18789")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--archive-id", default=datetime.now().strftime("%Y%m%d"))
    parser.add_argument("--version", default="v2-cutover")
    parser.add_argument("--owner", default="release-manager")
    parser.add_argument("--archive-mode", choices=["copy", "move"], default="copy")
    parser.add_argument("--archive-root", default="docs/archive/phase7")
    parser.add_argument("--force-regenerate", action="store_true", help="Regenerate drill reports even if they already exist")
    parser.add_argument("--skip-archive", action="store_true", help="Only backfill reports, skip archive step")
    parser.add_argument("--output", default="docs/reports/phase7_backfill_archive_latest.json")
    args = parser.parse_args()

    v1_base = args.v1_base.rstrip("/")
    v2_base = args.v2_base.rstrip("/")

    checks: list[dict[str, Any]] = []
    checks.append(
        ensure_report(
            label="canary_rollout",
            path=REPORTS_DIR / "phase7_canary_rollout_latest.json",
            cmd=[
                sys.executable,
                "scripts/phase7_canary_rollout_drill.py",
                "--v1-base",
                v1_base,
                "--v2-base",
                v2_base,
                "--stage",
                "all",
                "--output",
                "docs/reports/phase7_canary_rollout_latest.json",
            ],
            force_regenerate=args.force_regenerate,
        )
    )
    checks.append(
        ensure_report(
            label="pre_cutover_drill",
            path=REPORTS_DIR / "phase7_pre_cutover_drill_latest.json",
            cmd=[
                sys.executable,
                "scripts/phase7_pre_cutover_drill.py",
                "--v1-base",
                v1_base,
                "--v2-base",
                v2_base,
                "--timeout",
                str(args.timeout),
                "--output",
                "docs/reports/phase7_pre_cutover_drill_latest.json",
                "--rollback-output",
                "docs/reports/phase7_rollback_drill_latest.json",
            ],
            force_regenerate=args.force_regenerate,
        )
    )
    checks.append(
        ensure_report(
            label="rollback_drill",
            path=REPORTS_DIR / "phase7_rollback_drill_latest.json",
            cmd=[
                sys.executable,
                "scripts/phase7_rollback_drill.py",
                "--v1-base",
                v1_base,
                "--v2-base",
                v2_base,
                "--timeout",
                str(args.timeout),
                "--output",
                "docs/reports/phase7_rollback_drill_latest.json",
            ],
            force_regenerate=args.force_regenerate,
        )
    )
    checks.append(
        ensure_report(
            label="observability_guard",
            path=REPORTS_DIR / "phase7_observability_guard_latest.json",
            cmd=[
                sys.executable,
                "scripts/phase7_observability_guard.py",
                "--v2-base",
                v2_base,
                "--timeout",
                str(args.timeout),
                "--output",
                "docs/reports/phase7_observability_guard_latest.json",
            ],
            force_regenerate=args.force_regenerate,
            allow_nonzero=True,
        )
    )

    archive_result: dict[str, Any] | None = None
    archive_manifest: dict[str, Any] = {}
    if not args.skip_archive:
        archive_cmd = [
            sys.executable,
            "scripts/phase7_archive_materials.py",
            "--archive-id",
            args.archive_id,
            "--version",
            args.version,
            "--owner",
            args.owner,
            "--mode",
            args.archive_mode,
            "--archive-root",
            args.archive_root,
        ]
        archive_result = run_cmd(archive_cmd, title="archive_materials")
        manifest_path = ROOT / args.archive_root / args.archive_id / "manifest.json"
        if manifest_path.exists():
            try:
                archive_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                archive_manifest = {}

    backfill_filled = all(item.get("filled") for item in checks)
    backfill_healthy = all(item.get("healthy") for item in checks)
    archive_missing = int(archive_manifest.get("missing_count", 0)) if archive_manifest else None
    archive_ok = True if args.skip_archive else bool(archive_result and archive_result.get("ok"))
    all_ready = backfill_filled and archive_ok and (archive_missing in (None, 0))

    report = {
        "timestamp": utc_now_iso(),
        "inputs": {
            "v1_base": v1_base,
            "v2_base": v2_base,
            "archive_id": args.archive_id,
            "version": args.version,
            "owner": args.owner,
            "archive_mode": args.archive_mode,
            "archive_root": args.archive_root,
            "force_regenerate": args.force_regenerate,
            "skip_archive": args.skip_archive,
        },
        "backfill": checks,
        "archive": {
            "result": archive_result,
            "manifest": archive_manifest,
        },
        "summary": {
            "backfill_filled": backfill_filled,
            "backfill_healthy": backfill_healthy,
            "archive_ok": archive_ok,
            "archive_missing_count": archive_missing,
            "all_ready": all_ready,
        },
    }

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[phase7-backfill-archive] backfill_filled={backfill_filled} backfill_healthy={backfill_healthy} "
        f"archive_ok={archive_ok} "
        f"missing={archive_missing} all_ready={all_ready} report={out}"
    )
    return 0 if all_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
