#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except Exception:  # noqa: BLE001
        return None


def load_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def http_get_json(url: str, timeout: float) -> Tuple[int, Dict[str, Any]]:
    req = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(raw) if raw else {}
            return int(resp.getcode()), payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:  # noqa: BLE001
            payload = {"raw": raw}
        return int(exc.code), payload
    except Exception as exc:  # noqa: BLE001
        return 0, {"error": str(exc)}


def default_policy() -> Dict[str, Any]:
    return {
        "critical": {
            "v2_health_required": True,
            "rollback_precheck_required": True,
            "canary_failed_phases_max": 0,
            "baseline_failed_checks_max": 0,
            "failed_run_ratio_max": 0.2,
            "failed_runs_min_for_ratio": 3,
        },
        "warn": {
            "pending_approvals_max": 20,
            "timeout_tasks_max": 5,
            "report_stale_hours_max": 24,
        },
    }


def load_policy(path: str) -> Dict[str, Any]:
    policy = default_policy()
    incoming = load_json(path)
    for level in ("critical", "warn"):
        if isinstance(incoming.get(level), dict):
            policy[level].update(incoming[level])
    return policy


def evaluate(args: argparse.Namespace) -> Dict[str, Any]:
    policy = load_policy(args.policy)
    now = datetime.now(timezone.utc)
    alerts: List[Dict[str, Any]] = []

    def add_alert(level: str, key: str, message: str, value: Any, threshold: Any) -> None:
        alerts.append(
            {
                "level": level,
                "key": key,
                "message": message,
                "value": value,
                "threshold": threshold,
            }
        )

    baseline = load_json(args.baseline_report)
    canary = load_json(args.canary_report)
    pre_cutover = load_json(args.pre_cutover_report)
    rollback = load_json(args.rollback_report)

    # Report freshness warning
    stale_hours = policy["warn"]["report_stale_hours_max"]
    for name, payload, path in [
        ("baseline", baseline, args.baseline_report),
        ("canary", canary, args.canary_report),
        ("pre_cutover", pre_cutover, args.pre_cutover_report),
        ("rollback", rollback, args.rollback_report),
    ]:
        ts = parse_iso(payload.get("timestamp"))
        if ts is None:
            add_alert("warn", f"{name}_timestamp_missing", f"{name} report timestamp missing/invalid", None, "valid ISO timestamp")
            continue
        age_hours = (now - ts).total_seconds() / 3600.0
        if age_hours > float(stale_hours):
            add_alert(
                "warn",
                f"{name}_report_stale",
                f"{name} report is stale",
                round(age_hours, 2),
                f"<= {stale_hours}h",
            )

    # Critical checks from reports
    baseline_failed = int((baseline.get("summary") or {}).get("failed", 999))
    if baseline_failed > int(policy["critical"]["baseline_failed_checks_max"]):
        add_alert(
            "critical",
            "baseline_failed_checks",
            "Baseline report has failed checks",
            baseline_failed,
            f"<= {policy['critical']['baseline_failed_checks_max']}",
        )

    canary_failed = int((canary.get("summary") or {}).get("failed_phases", 999))
    if canary_failed > int(policy["critical"]["canary_failed_phases_max"]):
        add_alert(
            "critical",
            "canary_failed_phases",
            "Canary rollout has failed phases",
            canary_failed,
            f"<= {policy['critical']['canary_failed_phases_max']}",
        )

    rollback_ready = bool(rollback.get("rollback_ready"))
    if bool(policy["critical"]["rollback_precheck_required"]) and not rollback_ready:
        add_alert(
            "critical",
            "rollback_precheck",
            "Rollback precheck is not ready",
            rollback_ready,
            True,
        )

    # Live V2 probes
    v2_base = args.v2_base.rstrip("/")
    code, payload = http_get_json(v2_base + "/health", timeout=args.timeout)
    v2_health_ok = code == 200 and payload.get("status") == "ok"
    if bool(policy["critical"]["v2_health_required"]) and not v2_health_ok:
        add_alert("critical", "v2_health", "V2 health probe failed", {"code": code, "payload": payload}, "HTTP 200 + status=ok")

    # Live run ratio
    code, payload = http_get_json(v2_base + "/api/v2/console/runs", timeout=args.timeout)
    if code == 200:
        items = payload.get("items", [])
        total_runs = len(items)
        failed_runs = sum(1 for item in items if (item.get("run") or {}).get("state") == "failed")
        ratio = (failed_runs / total_runs) if total_runs else 0.0
        if failed_runs >= int(policy["critical"]["failed_runs_min_for_ratio"]) and ratio > float(
            policy["critical"]["failed_run_ratio_max"]
        ):
            add_alert(
                "critical",
                "failed_run_ratio",
                "Failed run ratio exceeds threshold",
                round(ratio, 4),
                f"<= {policy['critical']['failed_run_ratio_max']}",
            )
    else:
        add_alert("warn", "console_runs_probe", "Cannot query /api/v2/console/runs", code, 200)

    # Live pending approvals
    code, payload = http_get_json(v2_base + "/api/v2/approvals?status=pending", timeout=args.timeout)
    if code == 200:
        pending_approvals = len(payload.get("items", []))
        if pending_approvals > int(policy["warn"]["pending_approvals_max"]):
            add_alert(
                "warn",
                "pending_approvals",
                "Pending approvals exceed warning threshold",
                pending_approvals,
                f"<= {policy['warn']['pending_approvals_max']}",
            )
    else:
        add_alert("warn", "approvals_probe", "Cannot query pending approvals", code, 200)

    # Live timeout tasks
    code, payload = http_get_json(v2_base + "/api/v2/tasks?state=timeout", timeout=args.timeout)
    if code == 200:
        timeout_tasks = len(payload.get("items", []))
        if timeout_tasks > int(policy["warn"]["timeout_tasks_max"]):
            add_alert(
                "warn",
                "timeout_tasks",
                "Timeout tasks exceed warning threshold",
                timeout_tasks,
                f"<= {policy['warn']['timeout_tasks_max']}",
            )
    else:
        add_alert("warn", "timeout_tasks_probe", "Cannot query timeout tasks", code, 200)

    critical_count = sum(1 for alert in alerts if alert["level"] == "critical")
    warn_count = sum(1 for alert in alerts if alert["level"] == "warn")
    if critical_count > 0:
        decision = "rollback_now"
    elif warn_count > 0:
        decision = "warn"
    else:
        decision = "ok"

    return {
        "timestamp": utc_now_iso(),
        "policy": policy,
        "inputs": {
            "baseline_report": args.baseline_report,
            "canary_report": args.canary_report,
            "pre_cutover_report": args.pre_cutover_report,
            "rollback_report": args.rollback_report,
            "v2_base": v2_base,
        },
        "alerts": alerts,
        "summary": {
            "critical_count": critical_count,
            "warn_count": warn_count,
            "decision": decision,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 observability guard with rollback trigger decision.")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--policy", default="docs/phase7_observability_policy.json")
    parser.add_argument("--baseline-report", default="docs/reports/phase6_v1_v2_baseline_latest.json")
    parser.add_argument("--canary-report", default="docs/reports/phase7_canary_rollout_latest.json")
    parser.add_argument("--pre-cutover-report", default="docs/reports/phase7_pre_cutover_drill_latest.json")
    parser.add_argument("--rollback-report", default="docs/reports/phase7_rollback_drill_latest.json")
    parser.add_argument("--output", default="docs/reports/phase7_observability_guard_latest.json")
    args = parser.parse_args()

    report = evaluate(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    decision = report["summary"]["decision"]
    print(
        f"[phase7-observability] decision={decision} "
        f"critical={report['summary']['critical_count']} warn={report['summary']['warn_count']} report={output}"
    )
    return 1 if decision == "rollback_now" else 0


if __name__ == "__main__":
    raise SystemExit(main())
