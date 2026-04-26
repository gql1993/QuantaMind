#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def json_request(
    method: str,
    url: str,
    *,
    timeout: float,
    body: Dict[str, Any] | None = None,
) -> Tuple[int, Dict[str, Any], str]:
    data = None
    headers: Dict[str, str] = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url=url, method=method.upper(), data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(raw) if raw else {}
            return int(resp.getcode()), payload, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:  # noqa: BLE001
            payload = {"raw": raw}
        return int(exc.code), payload, raw
    except Exception as exc:  # noqa: BLE001
        return 0, {"error": str(exc)}, str(exc)


def wait_task(v2_base: str, task_id: str, timeout: float) -> Dict[str, Any]:
    deadline = time.time() + timeout
    final: Dict[str, Any] = {}
    while time.time() < deadline:
        code, payload, _ = json_request("GET", f"{v2_base}/api/v2/tasks/{task_id}", timeout=timeout)
        if code != 200:
            return {"ok": False, "code": code, "payload": payload}
        final = payload
        state = str(payload.get("state", ""))
        if state in {"completed", "failed", "cancelled", "timeout"}:
            return {"ok": True, "task": payload}
        time.sleep(0.15)
    return {"ok": False, "error": "timeout", "task": final}


def run_rollback_drill(v1_base: str, v2_base: str, timeout: float, output: str) -> Dict[str, Any]:
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/phase7_rollback_drill.py",
            "--v1-base",
            v1_base,
            "--v2-base",
            v2_base,
            "--timeout",
            str(timeout),
            "--output",
            output,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    report_data: Dict[str, Any] = {}
    report_path = Path(output)
    if report_path.exists():
        try:
            report_data = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            report_data = {}
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-8:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-8:]),
        "report": report_data,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 pre-cutover drill (approval/task/rollback).")
    parser.add_argument("--v1-base", default="http://127.0.0.1:18789")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--reviewer", default="drill_reviewer")
    parser.add_argument("--output", default="docs/reports/phase7_pre_cutover_drill_latest.json")
    parser.add_argument(
        "--rollback-output",
        default="docs/reports/phase7_rollback_drill_latest.json",
        help="Output file path passed to rollback drill script.",
    )
    args = parser.parse_args()

    v1_base = args.v1_base.rstrip("/")
    v2_base = args.v2_base.rstrip("/")
    checks: list[Dict[str, Any]] = []

    def record(name: str, ok: bool, detail: Dict[str, Any]) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    code, payload, _ = json_request("GET", f"{v2_base}/health", timeout=args.timeout)
    record("v2_health", code == 200, {"code": code, "payload": payload})

    # 1) Approval drill: create run -> create approval -> approve
    code, payload, _ = json_request(
        "POST",
        f"{v2_base}/api/v2/shortcuts/system_status",
        timeout=args.timeout,
        body={"origin": "phase7_pre_cutover_drill", "force": False},
    )
    run_id = payload.get("run", {}).get("run_id") if isinstance(payload, dict) else None
    record("drill_create_run_for_approval", code == 200 and bool(run_id), {"code": code, "run_id": run_id, "payload": payload})

    approval_id = None
    if run_id:
        code, payload, _ = json_request(
            "POST",
            f"{v2_base}/api/v2/approvals",
            timeout=args.timeout,
            body={
                "run_id": run_id,
                "approval_type": "external_delivery",
                "summary": "Phase7 drill approval request",
                "details": {"source": "phase7_pre_cutover_drill"},
            },
        )
        approval_id = payload.get("approval", {}).get("approval_id") if isinstance(payload, dict) else None
        record(
            "drill_create_approval",
            code == 200 and bool(approval_id),
            {"code": code, "approval_id": approval_id, "payload": payload},
        )

    if approval_id:
        code, payload, _ = json_request(
            "POST",
            f"{v2_base}/api/v2/approvals/{approval_id}/approve",
            timeout=args.timeout,
            body={"reviewer": args.reviewer, "comment": "phase7 drill pass"},
        )
        status = payload.get("approval", {}).get("status") if isinstance(payload, dict) else None
        record(
            "drill_approve_approval",
            code == 200 and status == "approved",
            {"code": code, "status": status, "payload": payload},
        )

    # 2) Task drill: submit background shortcut and wait
    code, payload, _ = json_request(
        "POST",
        f"{v2_base}/api/v2/tasks/shortcuts/intel_today",
        timeout=args.timeout,
        body={"origin": "phase7_pre_cutover_drill", "force": False},
    )
    task_id = payload.get("task", {}).get("task_id") if isinstance(payload, dict) else None
    record("drill_submit_background_task", code == 200 and bool(task_id), {"code": code, "task_id": task_id, "payload": payload})

    if task_id:
        wait = wait_task(v2_base, task_id, timeout=args.timeout)
        state = wait.get("task", {}).get("state")
        record("drill_wait_background_task", bool(wait.get("ok")) and state in {"completed", "failed"}, {"wait": wait})

    # 3) Rollback drill linkage
    rollback = run_rollback_drill(v1_base, v2_base, timeout=args.timeout, output=args.rollback_output)
    record("drill_rollback_precheck", bool(rollback.get("ok")), rollback)

    total = len(checks)
    passed = sum(1 for item in checks if item["ok"])
    report = {
        "timestamp": utc_now_iso(),
        "v1_base": v1_base,
        "v2_base": v2_base,
        "checks": checks,
        "summary": {"total": total, "passed": passed, "failed": total - passed},
        "ready_for_cutover_drill": passed == total,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[phase7-pre-cutover] total={total} passed={passed} failed={total - passed} "
        f"ready={report['ready_for_cutover_drill']} report={output}"
    )
    return 0 if report["ready_for_cutover_drill"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
