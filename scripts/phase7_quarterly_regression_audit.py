#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_TEMPLATE = ROOT / "docs" / "templates" / "Phase7_季度回归审计报告模板.md"
SIGNOFF_TEMPLATE = ROOT / "docs" / "templates" / "Phase7_季度回归审计签核记录模板.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def render(text: str, mapping: dict[str, str]) -> str:
    output = text
    for key, val in mapping.items():
        output = output.replace("{{" + key + "}}", val)
    return output


def list_biweekly_reports(reports_dir: Path, start: datetime, end: datetime) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for p in reports_dir.glob("phase7_biweekly_stability_review*.json"):
        payload = load_json(p)
        ts = parse_iso(payload.get("timestamp"))
        if ts is None:
            continue
        if start <= ts <= end:
            records.append({"path": str(p), "timestamp": ts, "payload": payload})
    records.sort(key=lambda x: x["timestamp"])
    return records


def quarter_text(current: datetime) -> str:
    q = ((current.month - 1) // 3) + 1
    return f"{current.year}Q{q}"


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    window_end = now
    window_start = now - timedelta(days=args.window_days)

    reports_dir = ROOT / "docs" / "reports"
    policy = load_json(ROOT / args.policy)
    guard = load_json(ROOT / args.guard_report)
    baseline = load_json(ROOT / args.baseline_report)
    canary = load_json(ROOT / args.canary_report)
    pre_cutover = load_json(ROOT / args.pre_cutover_report)
    rollback = load_json(ROOT / args.rollback_report)

    biweekly = list_biweekly_reports(reports_dir, window_start, window_end)
    biweekly_levels = [
        str((item.get("payload", {}).get("assessment", {}) or {}).get("stability_level", "UNKNOWN")) for item in biweekly
    ]
    red_count = sum(1 for lv in biweekly_levels if lv == "RED")
    yellow_count = sum(1 for lv in biweekly_levels if lv == "YELLOW")
    green_count = sum(1 for lv in biweekly_levels if lv == "GREEN")

    guard_summary = guard.get("summary") or {}
    guard_decision = str(guard_summary.get("decision", "unknown"))
    guard_critical = int(guard_summary.get("critical_count", 0))
    guard_warn = int(guard_summary.get("warn_count", 0))
    rollback_ready = bool(rollback.get("rollback_ready", False))
    baseline_failed = int((baseline.get("summary") or {}).get("failed", 999))
    canary_failed = int((canary.get("summary") or {}).get("failed_phases", 999))

    warn_cfg = policy.get("warn") or {}
    critical_cfg = policy.get("critical") or {}
    stale_limit = float(warn_cfg.get("report_stale_hours_max", 24))

    freshness_hours: list[float] = []
    for payload in [baseline, canary, pre_cutover, rollback, guard]:
        ts = parse_iso(payload.get("timestamp"))
        if ts is None:
            continue
        freshness_hours.append((now - ts).total_seconds() / 3600.0)
    freshest_ok = bool(freshness_hours) and max(freshness_hours) <= stale_limit

    risks: list[str] = []
    actions: list[str] = []

    if guard_critical > 0 or guard_decision == "rollback_now":
        audit_result = "FAIL"
        risks.append("观测守护存在 critical 告警或已触发回退建议。")
        actions.append("冻结版本推进并完成问题清零后重新审计。")
    elif red_count > 0:
        audit_result = "CONDITIONAL_PASS"
        risks.append("季度窗口内出现 RED 级稳定性复评记录。")
        actions.append("对 RED 样本完成 RCA + 复测，再次组织签核。")
    elif baseline_failed > 0 or canary_failed > 0:
        audit_result = "CONDITIONAL_PASS"
        risks.append("基线/灰度报告存在失败项。")
        actions.append("补齐失败项修复证据并重新执行回归。")
    else:
        audit_result = "PASS"

    if not rollback_ready:
        audit_result = "CONDITIONAL_PASS" if audit_result == "PASS" else audit_result
        risks.append("回退预检未显示就绪。")
        actions.append("补齐回退预检并更新 rollback drill 报告。")
    if not freshest_ok:
        audit_result = "CONDITIONAL_PASS" if audit_result == "PASS" else audit_result
        risks.append("输入报告存在时效性风险（超过 stale 阈值）。")
        actions.append("刷新关键报告并再次执行观测守护。")
    if len(biweekly) < args.expected_biweekly_min:
        audit_result = "CONDITIONAL_PASS" if audit_result == "PASS" else audit_result
        risks.append(f"季度窗口内双周复评次数不足（{len(biweekly)} < {args.expected_biweekly_min}）。")
        actions.append("补齐双周复评执行记录，确保节奏持续。")

    if not risks:
        risks.append("未发现阻塞性风险，审计输入满足阈值要求。")
    if not actions:
        actions.append("维持季度审计节奏并继续跟踪重点指标。")

    summary = (
        f"guard={guard_decision}（critical={guard_critical}, warn={guard_warn}），"
        f"biweekly={len(biweekly)}（green={green_count}, yellow={yellow_count}, red={red_count}），"
        f"audit={audit_result}。"
    )

    return {
        "timestamp": utc_now_iso(),
        "window": {
            "days": args.window_days,
            "start": window_start.isoformat().replace("+00:00", "Z"),
            "end": window_end.isoformat().replace("+00:00", "Z"),
        },
        "quarter": quarter_text(now),
        "inputs": {
            "policy": args.policy,
            "guard_report": args.guard_report,
            "baseline_report": args.baseline_report,
            "canary_report": args.canary_report,
            "pre_cutover_report": args.pre_cutover_report,
            "rollback_report": args.rollback_report,
            "expected_biweekly_min": args.expected_biweekly_min,
        },
        "metrics": {
            "guard_decision": guard_decision,
            "guard_critical_count": guard_critical,
            "guard_warn_count": guard_warn,
            "baseline_failed_checks": baseline_failed,
            "canary_failed_phases": canary_failed,
            "rollback_ready": rollback_ready,
            "max_report_age_hours": round(max(freshness_hours), 2) if freshness_hours else None,
            "report_freshness_ok": freshest_ok,
            "biweekly_total": len(biweekly),
            "biweekly_green": green_count,
            "biweekly_yellow": yellow_count,
            "biweekly_red": red_count,
            "biweekly_paths": [item["path"] for item in biweekly],
            "failed_run_ratio_max_policy": critical_cfg.get("failed_run_ratio_max"),
        },
        "assessment": {
            "audit_result": audit_result,
            "summary": summary,
            "risks": risks,
            "actions": actions,
        },
    }


def to_report_markdown(report: dict[str, Any], template: str, version_scope: str, owner: str) -> str:
    metrics = report.get("metrics") or {}
    metric_rows = [
        ("guard decision", metrics.get("guard_decision"), "ok（理想）", "关注" if metrics.get("guard_decision") != "ok" else "正常"),
        ("guard critical_count", metrics.get("guard_critical_count"), "0", "异常" if int(metrics.get("guard_critical_count", 0)) > 0 else "正常"),
        ("baseline failed", metrics.get("baseline_failed_checks"), "0", "关注" if int(metrics.get("baseline_failed_checks", 0)) > 0 else "正常"),
        ("canary failed phases", metrics.get("canary_failed_phases"), "0", "关注" if int(metrics.get("canary_failed_phases", 0)) > 0 else "正常"),
        ("rollback ready", metrics.get("rollback_ready"), "true", "关注" if not bool(metrics.get("rollback_ready")) else "正常"),
        ("max report age(h)", metrics.get("max_report_age_hours"), "within stale threshold", "关注" if not bool(metrics.get("report_freshness_ok")) else "正常"),
        ("biweekly reviews", metrics.get("biweekly_total"), ">= expected min", "关注" if int(metrics.get("biweekly_total", 0)) < 1 else "正常"),
        ("biweekly RED count", metrics.get("biweekly_red"), "0（理想）", "关注" if int(metrics.get("biweekly_red", 0)) > 0 else "正常"),
    ]
    metric_table = "\n".join(
        f"| {name} | {value} | {threshold} | {result} |" for name, value, threshold, result in metric_rows
    )

    inputs = report.get("inputs") or {}
    input_lines = [
        f"- policy: `{inputs.get('policy')}`",
        f"- guard: `{inputs.get('guard_report')}`",
        f"- baseline: `{inputs.get('baseline_report')}`",
        f"- canary: `{inputs.get('canary_report')}`",
        f"- pre_cutover: `{inputs.get('pre_cutover_report')}`",
        f"- rollback: `{inputs.get('rollback_report')}`",
    ]
    assessment = report.get("assessment") or {}
    mapping = {
        "DATE": datetime.now().strftime("%Y-%m-%d"),
        "QUARTER": str(report.get("quarter", "-")),
        "VERSION_SCOPE": version_scope,
        "OWNER": owner,
        "AUDIT_RESULT": str(assessment.get("audit_result", "UNKNOWN")),
        "EXEC_SUMMARY": str(assessment.get("summary", "")),
        "INPUT_ITEMS": "\n".join(input_lines),
        "METRIC_TABLE": metric_table,
        "RISK_ITEMS": "\n".join(f"- {item}" for item in assessment.get("risks", [])),
        "ACTION_ITEMS": "\n".join(f"- {item}" for item in assessment.get("actions", [])),
    }
    return render(template, mapping)


def to_signoff_markdown(template: str, *, report_path: str, quarter: str) -> str:
    return render(
        template,
        {
            "DATE": datetime.now().strftime("%Y-%m-%d"),
            "QUARTER": quarter,
            "REPORT_PATH": report_path,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 quarterly regression audit with sign-off closure.")
    parser.add_argument("--version-scope", default="v2-cutover", help="Version scope included in this quarterly audit")
    parser.add_argument("--owner", default="release-manager", help="Audit owner")
    parser.add_argument("--window-days", type=int, default=90, help="Audit window size in days")
    parser.add_argument("--expected-biweekly-min", type=int, default=4, help="Minimum expected biweekly reviews in the quarter")
    parser.add_argument("--policy", default="docs/phase7_observability_policy.json")
    parser.add_argument("--guard-report", default="docs/reports/phase7_observability_guard_latest.json")
    parser.add_argument("--baseline-report", default="docs/reports/phase6_v1_v2_baseline_latest.json")
    parser.add_argument("--canary-report", default="docs/reports/phase7_canary_rollout_latest.json")
    parser.add_argument("--pre-cutover-report", default="docs/reports/phase7_pre_cutover_drill_latest.json")
    parser.add_argument("--rollback-report", default="docs/reports/phase7_rollback_drill_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase7_quarterly_regression_audit_latest.json")
    parser.add_argument("--output-report", default="docs/reports/phase7_quarterly_regression_audit_latest.md")
    parser.add_argument("--output-signoff", default="docs/reports/phase7_quarterly_regression_signoff_latest.md")
    args = parser.parse_args()

    if not REPORT_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {REPORT_TEMPLATE}")
    if not SIGNOFF_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {SIGNOFF_TEMPLATE}")

    report = evaluate(args)
    report_md = to_report_markdown(
        report,
        REPORT_TEMPLATE.read_text(encoding="utf-8"),
        version_scope=args.version_scope,
        owner=args.owner,
    )

    output_json = ROOT / args.output_json
    output_report = ROOT / args.output_report
    output_signoff = ROOT / args.output_signoff
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_signoff.parent.mkdir(parents=True, exist_ok=True)

    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output_report.write_text(report_md, encoding="utf-8")
    output_signoff.write_text(
        to_signoff_markdown(
            SIGNOFF_TEMPLATE.read_text(encoding="utf-8"),
            report_path=str(output_report).replace("\\", "/"),
            quarter=str(report.get("quarter", "-")),
        ),
        encoding="utf-8",
    )

    result = str((report.get("assessment") or {}).get("audit_result", "UNKNOWN"))
    print(
        f"[phase7-quarterly-audit] result={result} json={output_json} report={output_report} signoff={output_signoff}"
    )
    return 1 if result == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
