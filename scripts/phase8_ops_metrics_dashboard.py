#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "templates" / "Phase8_生产运行度量看板模板.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: str) -> dict[str, Any]:
    p = ROOT / path
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def http_get_json(url: str, timeout: float) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return int(resp.getcode()), (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:  # noqa: BLE001
            payload = {"raw": raw}
        return int(exc.code), payload
    except Exception as exc:  # noqa: BLE001
        return 0, {"error": str(exc)}


def render(text: str, mapping: dict[str, str]) -> str:
    out = text
    for key, val in mapping.items():
        out = out.replace("{{" + key + "}}", val)
    return out


def level_from_ratio(*, ratio: float, warn_ratio: float, critical_ratio: float) -> str:
    if ratio >= critical_ratio:
        return "red"
    if ratio >= warn_ratio:
        return "yellow"
    return "green"


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    policy = load_json(args.policy)
    slo_cfg = policy.get("slo") or {}
    cap_cfg = policy.get("capacity") or {}

    availability_target = float(slo_cfg.get("availability_target", 0.995))
    budget_breach_ratio = float(slo_cfg.get("error_budget_breach_ratio", 1.0))
    budget_warn_ratio = float(slo_cfg.get("error_budget_warn_ratio", 0.7))
    pending_max = int(cap_cfg.get("pending_approvals_max", 20))
    timeout_max = int(cap_cfg.get("timeout_tasks_max", 5))
    warn_util = float(cap_cfg.get("warn_utilization_ratio", 0.7))
    critical_util = float(cap_cfg.get("critical_utilization_ratio", 1.0))

    guard = load_json(args.guard_report)
    biweekly = load_json(args.biweekly_report)

    guard_summary = guard.get("summary") or {}
    guard_decision = str(guard_summary.get("decision", "unknown"))
    guard_critical = int(guard_summary.get("critical_count", 0))
    guard_warn = int(guard_summary.get("warn_count", 0))

    live: dict[str, Any] = {
        "health_ok": None,
        "failed_runs": None,
        "total_runs": None,
        "failed_run_ratio": None,
        "pending_approvals": None,
        "timeout_tasks": None,
    }

    if not args.skip_live_probes:
        v2_base = args.v2_base.rstrip("/")
        code, payload = http_get_json(v2_base + "/health", timeout=args.timeout)
        live["health_ok"] = code == 200 and payload.get("status") == "ok"

        code, payload = http_get_json(v2_base + "/api/v2/console/runs", timeout=args.timeout)
        if code == 200:
            items = payload.get("items", [])
            total = len(items)
            failed = sum(1 for item in items if (item.get("run") or {}).get("state") == "failed")
            live["total_runs"] = total
            live["failed_runs"] = failed
            live["failed_run_ratio"] = (failed / total) if total else 0.0

        code, payload = http_get_json(v2_base + "/api/v2/approvals?status=pending", timeout=args.timeout)
        if code == 200:
            live["pending_approvals"] = len(payload.get("items", []))

        code, payload = http_get_json(v2_base + "/api/v2/tasks?state=timeout", timeout=args.timeout)
        if code == 200:
            live["timeout_tasks"] = len(payload.get("items", []))

    fallback_ratio = (((biweekly.get("live") or {}).get("failed_run_ratio")) if biweekly else None)
    failed_run_ratio = live["failed_run_ratio"] if isinstance(live["failed_run_ratio"], float) else fallback_ratio
    availability_data_missing = not isinstance(failed_run_ratio, float)
    if availability_data_missing:
        availability = availability_target
        failed_run_ratio_value = None
    else:
        failed_run_ratio_value = float(failed_run_ratio)
        availability = max(0.0, 1.0 - failed_run_ratio_value)

    error_budget_total = max(0.0, 1.0 - availability_target)
    error_budget_burn = max(0.0, availability_target - availability)
    error_budget_consumed_ratio = 0.0 if error_budget_total == 0 else (error_budget_burn / error_budget_total)

    if availability_data_missing:
        slo_level = "yellow"
    elif availability < availability_target:
        slo_level = "red"
    elif availability < availability_target + (error_budget_total * 0.3):
        slo_level = "yellow"
    else:
        slo_level = "green"

    budget_level = level_from_ratio(
        ratio=error_budget_consumed_ratio,
        warn_ratio=budget_warn_ratio,
        critical_ratio=budget_breach_ratio,
    )

    pending_missing = not isinstance(live["pending_approvals"], int)
    timeout_missing = not isinstance(live["timeout_tasks"], int)
    pending = live["pending_approvals"] if isinstance(live["pending_approvals"], int) else 0
    timeout_tasks = live["timeout_tasks"] if isinstance(live["timeout_tasks"], int) else 0
    pending_util = pending / pending_max if pending_max > 0 else 1.0
    timeout_util = timeout_tasks / timeout_max if timeout_max > 0 else 1.0
    capacity_pressure = max(pending_util, timeout_util)
    capacity_level = level_from_ratio(ratio=capacity_pressure, warn_ratio=warn_util, critical_ratio=critical_util)
    if pending_missing and timeout_missing:
        capacity_level = "yellow"

    risks: list[str] = []
    actions: list[str] = []
    levels = [slo_level, budget_level, capacity_level]
    if guard_decision == "rollback_now" or guard_critical > 0:
        levels.append("red")
        risks.append("观测守护存在 critical 告警。")
        actions.append("立即冻结变更并执行故障处置/回退评估。")
    elif guard_decision == "warn" or guard_warn > 0:
        levels.append("yellow")
        risks.append("观测守护存在 warn 告警。")
        actions.append("24 小时内完成告警闭环并复测。")

    if live["health_ok"] is False:
        levels.append("red")
        risks.append("实时健康探针失败。")
        actions.append("优先恢复 V2 健康状态并回放关键链路。")

    if capacity_level != "green":
        risks.append("容量指标出现压力（pending approvals / timeout tasks）。")
        actions.append("调整任务预算与审批处理 SLA，降低积压。")

    if (not availability_data_missing) and slo_level != "green":
        risks.append("可用性低于 SLO 目标。")
        actions.append("分析失败 run 样本并加固高频故障点。")
    if availability_data_missing:
        risks.append("未获取到 failed_run_ratio，当前可用性按目标值占位。")
        actions.append("恢复 runs 指标采集后重新生成看板。")
    if pending_missing or timeout_missing:
        risks.append("容量实时指标不完整，当前结果为部分数据。")
        actions.append("恢复 approvals/tasks 探针后刷新容量结论。")

    if "red" in levels:
        overall = "RED"
    elif "yellow" in levels:
        overall = "YELLOW"
    else:
        overall = "GREEN"

    if not risks:
        risks.append("当前窗口未发现高风险异常。")
    if not actions:
        actions.append("保持当前运营节奏，持续巡检。")

    summary = (
        f"overall={overall}, availability={availability:.4f}, error_budget_ratio={error_budget_consumed_ratio:.4f}, "
        f"capacity_pressure={capacity_pressure:.4f}, guard={guard_decision}."
    )

    return {
        "timestamp": utc_now_iso(),
        "inputs": {
            "policy": args.policy,
            "guard_report": args.guard_report,
            "biweekly_report": args.biweekly_report,
            "skip_live_probes": args.skip_live_probes,
            "v2_base": args.v2_base.rstrip("/"),
        },
        "policy": {
            "availability_target": availability_target,
            "error_budget_warn_ratio": budget_warn_ratio,
            "error_budget_breach_ratio": budget_breach_ratio,
            "pending_approvals_max": pending_max,
            "timeout_tasks_max": timeout_max,
            "capacity_warn_utilization": warn_util,
            "capacity_critical_utilization": critical_util,
        },
        "live": live,
        "metrics": {
            "availability": availability,
            "failed_run_ratio": failed_run_ratio_value,
            "error_budget_total": error_budget_total,
            "error_budget_burn": error_budget_burn,
            "error_budget_consumed_ratio": error_budget_consumed_ratio,
            "pending_approvals": pending,
            "pending_utilization": pending_util,
            "timeout_tasks": timeout_tasks,
            "timeout_utilization": timeout_util,
            "capacity_pressure": capacity_pressure,
            "guard_decision": guard_decision,
            "guard_critical_count": guard_critical,
            "guard_warn_count": guard_warn,
        },
        "assessment": {
            "overall_status": overall,
            "slo_level": slo_level,
            "budget_level": budget_level,
            "capacity_level": capacity_level,
            "summary": summary,
            "risks": risks,
            "actions": actions,
        },
    }


def to_markdown(report: dict[str, Any], template: str, *, version: str, owner: str) -> str:
    metrics = report.get("metrics") or {}
    policy = report.get("policy") or {}
    assessment = report.get("assessment") or {}
    slo_rows = [
        (
            "Availability",
            f"{float(metrics.get('availability', 0.0)):.4f}",
            f">= {float(policy.get('availability_target', 0.995)):.4f}",
            str(assessment.get("slo_level", "unknown")),
        ),
        (
            "Error Budget Consumed Ratio",
            f"{float(metrics.get('error_budget_consumed_ratio', 0.0)):.4f}",
            f"warn>={float(policy.get('error_budget_warn_ratio', 0.7)):.2f}, breach>={float(policy.get('error_budget_breach_ratio', 1.0)):.2f}",
            str(assessment.get("budget_level", "unknown")),
        ),
        (
            "Guard Decision",
            str(metrics.get("guard_decision")),
            "ok（理想）",
            "green" if str(metrics.get("guard_decision")) == "ok" else "yellow",
        ),
    ]
    capacity_rows = [
        (
            "Pending Approvals",
            str(metrics.get("pending_approvals")),
            f"<= {int(policy.get('pending_approvals_max', 20))}",
            "green" if float(metrics.get("pending_utilization", 0.0)) < float(policy.get("capacity_warn_utilization", 0.7)) else str(assessment.get("capacity_level")),
        ),
        (
            "Timeout Tasks",
            str(metrics.get("timeout_tasks")),
            f"<= {int(policy.get('timeout_tasks_max', 5))}",
            "green" if float(metrics.get("timeout_utilization", 0.0)) < float(policy.get("capacity_warn_utilization", 0.7)) else str(assessment.get("capacity_level")),
        ),
        (
            "Capacity Pressure",
            f"{float(metrics.get('capacity_pressure', 0.0)):.4f}",
            f"warn>={float(policy.get('capacity_warn_utilization', 0.7)):.2f}, critical>={float(policy.get('capacity_critical_utilization', 1.0)):.2f}",
            str(assessment.get("capacity_level", "unknown")),
        ),
    ]
    mapping = {
        "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "VERSION": version,
        "OWNER": owner,
        "OVERALL_STATUS": str(assessment.get("overall_status", "UNKNOWN")),
        "EXEC_SUMMARY": str(assessment.get("summary", "")),
        "SLO_TABLE": "\n".join(f"| {a} | {b} | {c} | {d} |" for a, b, c, d in slo_rows),
        "CAPACITY_TABLE": "\n".join(f"| {a} | {b} | {c} | {d} |" for a, b, c, d in capacity_rows),
        "RISK_ITEMS": "\n".join(f"- {item}" for item in assessment.get("risks", [])),
        "EVIDENCE_ITEMS": "\n".join(
            [
                f"- policy: `{(report.get('inputs') or {}).get('policy')}`",
                f"- guard report: `{(report.get('inputs') or {}).get('guard_report')}`",
                f"- biweekly report: `{(report.get('inputs') or {}).get('biweekly_report')}`",
                f"- live probes: `{'disabled' if (report.get('inputs') or {}).get('skip_live_probes') else 'enabled'}`",
            ]
        ),
    }
    return render(template, mapping)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 8 production ops metrics dashboard generator.")
    parser.add_argument("--version", default="v2-cutover", help="Version/cutover label")
    parser.add_argument("--owner", default="release-manager", help="Dashboard owner")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--policy", default="docs/phase8_ops_metrics_policy.json")
    parser.add_argument("--guard-report", default="docs/reports/phase7_observability_guard_latest.json")
    parser.add_argument("--biweekly-report", default="docs/reports/phase7_biweekly_stability_review_latest.json")
    parser.add_argument("--skip-live-probes", action="store_true")
    parser.add_argument("--output-json", default="docs/reports/phase8_ops_metrics_dashboard_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase8_ops_metrics_dashboard_latest.md")
    args = parser.parse_args()

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE_PATH}")

    report = evaluate(args)
    output_json = ROOT / args.output_json
    output_md = ROOT / args.output_markdown
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(
        to_markdown(
            report,
            TEMPLATE_PATH.read_text(encoding="utf-8"),
            version=args.version,
            owner=args.owner,
        ),
        encoding="utf-8",
    )

    overall = (report.get("assessment") or {}).get("overall_status", "UNKNOWN")
    print(f"[phase8-ops-dashboard] overall={overall} json={output_json} markdown={output_md}")
    return 1 if overall == "RED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
