#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "templates" / "Phase7_双周稳定性复评模板.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None


def http_get_json(url: str, timeout: float) -> tuple[int, dict[str, Any]]:
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


def render(template: str, mapping: dict[str, str]) -> str:
    output = template
    for key, val in mapping.items():
        output = output.replace("{{" + key + "}}", val)
    return output


def scan_postmortem_files(directory: Path, start_date: datetime, end_date: datetime) -> int:
    if not directory.exists():
        return 0
    count = 0
    for md in directory.glob("*.md"):
        name = md.name
        if len(name) < 8 or not name[:8].isdigit():
            continue
        try:
            file_date = datetime.strptime(name[:8], "%Y%m%d")
        except Exception:  # noqa: BLE001
            continue
        if start_date.date() <= file_date.date() <= end_date.date():
            count += 1
    return count


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    window_end = now
    window_start = now - timedelta(days=args.window_days)

    guard = load_json(args.guard_report)
    baseline = load_json(args.baseline_report)
    canary = load_json(args.canary_report)
    pre_cutover = load_json(args.pre_cutover_report)
    rollback = load_json(args.rollback_report)
    policy = load_json(args.policy)

    guard_summary = guard.get("summary") or {}
    guard_decision = str(guard_summary.get("decision", "unknown"))
    guard_critical = int(guard_summary.get("critical_count", 0))
    guard_warn = int(guard_summary.get("warn_count", 0))

    postmortem_count = scan_postmortem_files(Path(args.postmortem_dir), window_start, window_end)

    live: dict[str, Any] = {
        "health_ok": None,
        "failed_run_ratio": None,
        "failed_runs": None,
        "total_runs": None,
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
            live["failed_run_ratio"] = round((failed / total), 4) if total else 0.0

        code, payload = http_get_json(v2_base + "/api/v2/approvals?status=pending", timeout=args.timeout)
        if code == 200:
            live["pending_approvals"] = len(payload.get("items", []))

        code, payload = http_get_json(v2_base + "/api/v2/tasks?state=timeout", timeout=args.timeout)
        if code == 200:
            live["timeout_tasks"] = len(payload.get("items", []))

    warn_policy = policy.get("warn") or {}
    pending_max = int(warn_policy.get("pending_approvals_max", 20))
    timeout_max = int(warn_policy.get("timeout_tasks_max", 5))
    critical_policy = policy.get("critical") or {}
    run_ratio_max = float(critical_policy.get("failed_run_ratio_max", 0.2))

    risks: list[str] = []
    actions: list[str] = []

    if guard_decision == "rollback_now" or guard_critical > 0:
        stability_level = "RED"
        risks.append("观测守护出现 critical 告警，存在立即回退风险。")
        actions.append("立即冻结发布变更，进入回退预案并追加 RCA。")
    elif guard_decision == "warn" or guard_warn > 0:
        stability_level = "YELLOW"
        risks.append("观测守护存在 warn 告警，需要持续跟踪。")
        actions.append("24 小时内完成告警闭环并复测关键链路。")
    else:
        stability_level = "GREEN"
        actions.append("维持当前灰度节奏，进入下一轮复评。")

    if live["health_ok"] is False:
        stability_level = "RED"
        risks.append("V2 健康探针失败，稳定性不足。")
        actions.append("优先修复健康检查失败项并进行回归验证。")
    if isinstance(live["failed_run_ratio"], float) and live["failed_run_ratio"] > run_ratio_max:
        stability_level = "YELLOW" if stability_level == "GREEN" else stability_level
        risks.append(f"失败 run 比例偏高（{live['failed_run_ratio']} > {run_ratio_max}）。")
        actions.append("分析失败 run 样本，收敛同类问题。")
    if isinstance(live["pending_approvals"], int) and live["pending_approvals"] > pending_max:
        stability_level = "YELLOW" if stability_level == "GREEN" else stability_level
        risks.append(f"pending approvals 超阈值（{live['pending_approvals']} > {pending_max}）。")
        actions.append("清理审批积压并优化审批 SLA。")
    if isinstance(live["timeout_tasks"], int) and live["timeout_tasks"] > timeout_max:
        stability_level = "YELLOW" if stability_level == "GREEN" else stability_level
        risks.append(f"timeout tasks 超阈值（{live['timeout_tasks']} > {timeout_max}）。")
        actions.append("排查任务超时根因，必要时调整重试与预算策略。")

    if postmortem_count == 0:
        risks.append("观测窗口内未发现复盘材料，改进闭环证据不足。")
        actions.append("补齐复盘文档并登记行动项台账。")

    if not risks:
        risks.append("未发现新增高风险异常。")
    if not actions:
        actions.append("保持例行巡检与双周复评节奏。")

    exec_summary = (
        f"窗口内 guard={guard_decision}（critical={guard_critical}, warn={guard_warn}），"
        f"复盘材料数={postmortem_count}，建议等级={stability_level}。"
    )

    metrics = [
        {
            "name": "guard decision",
            "value": guard_decision,
            "threshold": "ok/warn/rollback_now",
            "result": "关注" if guard_decision != "ok" else "正常",
        },
        {
            "name": "guard critical_count",
            "value": guard_critical,
            "threshold": "0",
            "result": "异常" if guard_critical > 0 else "正常",
        },
        {
            "name": "guard warn_count",
            "value": guard_warn,
            "threshold": "0（理想）",
            "result": "关注" if guard_warn > 0 else "正常",
        },
        {
            "name": "failed run ratio",
            "value": live["failed_run_ratio"],
            "threshold": f"<= {run_ratio_max}",
            "result": "关注"
            if isinstance(live["failed_run_ratio"], float) and live["failed_run_ratio"] > run_ratio_max
            else "正常",
        },
        {
            "name": "pending approvals",
            "value": live["pending_approvals"],
            "threshold": f"<= {pending_max}",
            "result": "关注"
            if isinstance(live["pending_approvals"], int) and live["pending_approvals"] > pending_max
            else "正常",
        },
        {
            "name": "timeout tasks",
            "value": live["timeout_tasks"],
            "threshold": f"<= {timeout_max}",
            "result": "关注"
            if isinstance(live["timeout_tasks"], int) and live["timeout_tasks"] > timeout_max
            else "正常",
        },
        {
            "name": "postmortem artifacts count",
            "value": postmortem_count,
            "threshold": ">= 1",
            "result": "关注" if postmortem_count < 1 else "正常",
        },
    ]

    return {
        "timestamp": utc_now_iso(),
        "window": {
            "days": args.window_days,
            "start": window_start.isoformat().replace("+00:00", "Z"),
            "end": window_end.isoformat().replace("+00:00", "Z"),
        },
        "inputs": {
            "policy": args.policy,
            "guard_report": args.guard_report,
            "baseline_report": args.baseline_report,
            "canary_report": args.canary_report,
            "pre_cutover_report": args.pre_cutover_report,
            "rollback_report": args.rollback_report,
            "postmortem_dir": args.postmortem_dir,
            "skip_live_probes": args.skip_live_probes,
            "v2_base": args.v2_base.rstrip("/"),
        },
        "source_state": {
            "guard_summary": guard_summary,
            "baseline_timestamp": baseline.get("timestamp"),
            "canary_timestamp": canary.get("timestamp"),
            "pre_cutover_timestamp": pre_cutover.get("timestamp"),
            "rollback_timestamp": rollback.get("timestamp"),
        },
        "live": live,
        "metrics": metrics,
        "assessment": {
            "stability_level": stability_level,
            "summary": exec_summary,
            "risks": risks,
            "actions": actions,
        },
    }


def to_markdown(report: dict[str, Any], template: str, *, version: str, owner: str) -> str:
    window = report.get("window") or {}
    start = parse_iso(window.get("start"))
    end = parse_iso(window.get("end"))
    if start and end:
        window_text = f"{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}（{window.get('days')} 天）"
    else:
        window_text = f"{window.get('days', '-') } 天"

    metric_lines = []
    for m in report.get("metrics", []):
        metric_lines.append(
            "| "
            + str(m.get("name"))
            + " | "
            + str(m.get("value"))
            + " | "
            + str(m.get("threshold"))
            + " | "
            + str(m.get("result"))
            + " |"
        )

    risks = report.get("assessment", {}).get("risks", [])
    actions = report.get("assessment", {}).get("actions", [])
    inputs = report.get("inputs", {})
    evidence_lines = [
        f"- policy: `{inputs.get('policy')}`",
        f"- guard: `{inputs.get('guard_report')}`",
        f"- baseline: `{inputs.get('baseline_report')}`",
        f"- canary: `{inputs.get('canary_report')}`",
        f"- pre_cutover: `{inputs.get('pre_cutover_report')}`",
        f"- rollback: `{inputs.get('rollback_report')}`",
        f"- postmortem_dir: `{inputs.get('postmortem_dir')}`",
        f"- live_probes: `{'disabled' if inputs.get('skip_live_probes') else 'enabled'}`",
    ]

    mapping = {
        "DATE": datetime.now().strftime("%Y-%m-%d"),
        "WINDOW": window_text,
        "VERSION": version,
        "OWNER": owner,
        "STABILITY_LEVEL": str(report.get("assessment", {}).get("stability_level", "UNKNOWN")),
        "EXEC_SUMMARY": str(report.get("assessment", {}).get("summary", "")),
        "METRIC_TABLE": "\n".join(metric_lines),
        "RISK_ITEMS": "\n".join(f"- {item}" for item in risks),
        "ACTION_ITEMS": "\n".join(f"- {item}" for item in actions),
        "EVIDENCE_ITEMS": "\n".join(evidence_lines),
    }
    return render(template, mapping)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 biweekly stability review generator (continuous observation).")
    parser.add_argument("--version", default="v2-cutover", help="Version/cutover label")
    parser.add_argument("--owner", default="release-manager", help="Review owner")
    parser.add_argument("--window-days", type=int, default=14, help="Observation window size (days)")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--policy", default="docs/phase7_observability_policy.json")
    parser.add_argument("--guard-report", default="docs/reports/phase7_observability_guard_latest.json")
    parser.add_argument("--baseline-report", default="docs/reports/phase6_v1_v2_baseline_latest.json")
    parser.add_argument("--canary-report", default="docs/reports/phase7_canary_rollout_latest.json")
    parser.add_argument("--pre-cutover-report", default="docs/reports/phase7_pre_cutover_drill_latest.json")
    parser.add_argument("--rollback-report", default="docs/reports/phase7_rollback_drill_latest.json")
    parser.add_argument("--postmortem-dir", default="docs/reports/postmortem-pack")
    parser.add_argument("--output-json", default="docs/reports/phase7_biweekly_stability_review_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase7_biweekly_stability_review_latest.md")
    parser.add_argument("--skip-live-probes", action="store_true", help="Disable live HTTP probes and use report-only mode")
    args = parser.parse_args()

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE_PATH}")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    report = build_report(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_markdown)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(to_markdown(report, template, version=args.version, owner=args.owner), encoding="utf-8")

    level = report.get("assessment", {}).get("stability_level", "UNKNOWN")
    print(f"[phase7-biweekly-review] level={level} json={output_json} markdown={output_md}")
    return 1 if level == "RED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
