#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_command(cmd: list[str], *, title: str) -> Dict[str, Any]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return {
        "title": title,
        "command": cmd,
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-12:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-12:]),
    }


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def phase_library_canary(v1_base: str, v2_base: str) -> Dict[str, Any]:
    baseline_out = "docs/reports/phase7_canary_library_baseline.json"
    cmd = [
        sys.executable,
        "scripts/v1_v2_baseline_regression.py",
        "--v1-base",
        v1_base,
        "--v2-base",
        v2_base,
        "--output",
        baseline_out,
    ]
    result = run_command(cmd, title="library_canary_baseline")
    report = read_json(baseline_out)
    summary = report.get("summary", {})
    return {
        "step": "library_canary",
        "gate": "library first",
        "result": result,
        "report_path": baseline_out,
        "report_summary": summary,
        "ready": bool(result.get("ok")) and int(summary.get("failed", 999)) == 0,
        "next_action": "proceed to pipeline canary" if result.get("ok") else "hold and rollback",
    }


def phase_pipeline_canary(v1_base: str, v2_base: str) -> Dict[str, Any]:
    drill_out = "docs/reports/phase7_canary_pipeline_pre_cutover.json"
    rollback_out = "docs/reports/phase7_canary_pipeline_rollback.json"
    cmd = [
        sys.executable,
        "scripts/phase7_pre_cutover_drill.py",
        "--v1-base",
        v1_base,
        "--v2-base",
        v2_base,
        "--output",
        drill_out,
        "--rollback-output",
        rollback_out,
    ]
    result = run_command(cmd, title="pipeline_canary_pre_cutover_drill")
    report = read_json(drill_out)
    summary = report.get("summary", {})
    return {
        "step": "pipeline_canary",
        "gate": "pipeline second",
        "result": result,
        "report_path": drill_out,
        "rollback_report_path": rollback_out,
        "report_summary": summary,
        "ready": bool(result.get("ok")) and int(summary.get("failed", 999)) == 0,
        "next_action": "ready for cutover review" if result.get("ok") else "hold and rollback",
    }


def run_rollback_only(v1_base: str, v2_base: str) -> Dict[str, Any]:
    output = "docs/reports/phase7_canary_rollback_only.json"
    cmd = [
        sys.executable,
        "scripts/phase7_rollback_drill.py",
        "--v1-base",
        v1_base,
        "--v2-base",
        v2_base,
        "--output",
        output,
    ]
    result = run_command(cmd, title="rollback_only")
    report = read_json(output)
    return {"result": result, "report_path": output, "report": report}


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 canary rollout drill: library first, pipeline second.")
    parser.add_argument("--v1-base", default="http://127.0.0.1:18789")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790")
    parser.add_argument(
        "--stage",
        choices=["all", "library", "pipeline", "rollback"],
        default="all",
        help="Run full canary flow or a single stage.",
    )
    parser.add_argument("--output", default="docs/reports/phase7_canary_rollout_latest.json")
    args = parser.parse_args()

    v1_base = args.v1_base.rstrip("/")
    v2_base = args.v2_base.rstrip("/")
    report: Dict[str, Any] = {
        "timestamp": utc_now_iso(),
        "mode": args.stage,
        "v1_base": v1_base,
        "v2_base": v2_base,
        "phases": [],
    }

    ready = True
    if args.stage in {"all", "library"}:
        library = phase_library_canary(v1_base, v2_base)
        report["phases"].append(library)
        ready = ready and bool(library.get("ready"))

    if args.stage in {"all", "pipeline"}:
        # for all mode, pipeline stage should only proceed if library stage passed
        if args.stage == "pipeline" or ready:
            pipeline = phase_pipeline_canary(v1_base, v2_base)
            report["phases"].append(pipeline)
            ready = ready and bool(pipeline.get("ready"))
        else:
            report["phases"].append(
                {
                    "step": "pipeline_canary",
                    "skipped": True,
                    "reason": "library_canary not ready",
                }
            )
            ready = False

    if args.stage == "rollback":
        rollback = run_rollback_only(v1_base, v2_base)
        report["phases"].append({"step": "rollback_only", **rollback, "ready": bool(rollback["result"].get("ok"))})
        ready = bool(rollback["result"].get("ok"))

    total = len(report["phases"])
    passed = sum(1 for phase in report["phases"] if phase.get("ready"))
    report["summary"] = {
        "total_phases": total,
        "passed_phases": passed,
        "failed_phases": total - passed,
        "canary_ready": ready,
        "strategy": "library-first then pipeline",
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"[phase7-canary] mode={args.stage} phases={total} passed={passed} "
        f"failed={total - passed} ready={ready} report={out}"
    )
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
