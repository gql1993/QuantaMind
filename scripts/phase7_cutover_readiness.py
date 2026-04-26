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


def check_file(path: str) -> Dict[str, Any]:
    p = Path(path)
    return {"path": path, "exists": p.exists(), "size": p.stat().st_size if p.exists() else 0}


def run_pytest() -> Dict[str, Any]:
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests/v2", "-q"], capture_output=True, text=True, check=False)
    return {
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-8:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-8:]),
    }


def check_baseline_report(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"path": path, "exists": False, "ok": False}
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"path": path, "exists": True, "ok": False, "error": str(exc)}
    summary = payload.get("summary", {})
    failed = int(summary.get("failed", 999))
    return {
        "path": path,
        "exists": True,
        "ok": failed == 0,
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 cutover readiness dry-run checker.")
    parser.add_argument("--baseline-report", default="docs/reports/phase6_v1_v2_baseline_latest.json")
    parser.add_argument("--output", default="docs/reports/phase7_cutover_readiness_latest.json")
    parser.add_argument("--run-tests", action="store_true", help="Run pytest tests/v2 during readiness check.")
    args = parser.parse_args()

    required_docs = [
        "docs/Phase6_资料库导入_V1_V2_链路对比报告.md",
        "docs/Phase6_标准流水线_V1_V2_稳定性对比报告.md",
        "docs/Phase6_V1_V2_对比基线与回归脚本.md",
    ]
    docs_status = [check_file(path) for path in required_docs]
    baseline = check_baseline_report(args.baseline_report)
    tests_status = run_pytest() if args.run_tests else {"skipped": True, "ok": True}

    checks = {
        "docs_ready": all(item["exists"] for item in docs_status),
        "baseline_ready": bool(baseline.get("ok")),
        "tests_ready": bool(tests_status.get("ok", False)),
    }
    ready = all(checks.values())

    report = {
        "timestamp": utc_now_iso(),
        "checks": checks,
        "ready_for_cutover": ready,
        "baseline_report": baseline,
        "docs_status": docs_status,
        "tests_status": tests_status,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        "[phase7-cutover] ready="
        + str(ready)
        + " docs="
        + str(checks["docs_ready"])
        + " baseline="
        + str(checks["baseline_ready"])
        + " tests="
        + str(checks["tests_ready"])
        + f" report={output}"
    )
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
