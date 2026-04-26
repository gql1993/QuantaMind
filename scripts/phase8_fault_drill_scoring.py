#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_TEMPLATE = ROOT / "docs" / "templates" / "Phase8_故障演练评分报告模板.md"
LEDGER_TEMPLATE = ROOT / "docs" / "templates" / "Phase8_改进行动闭环台账模板.md"


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


def render(template: str, mapping: dict[str, str]) -> str:
    out = template
    for key, val in mapping.items():
        out = out.replace("{{" + key + "}}", val)
    return out


def clamp_score(v: float) -> float:
    return max(0.0, min(100.0, v))


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 8 fault drill auto scoring and improvement loop.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="drill-manager")
    parser.add_argument("--policy", default="docs/phase8_drill_scoring_policy.json")
    parser.add_argument("--pre-cutover-report", default="docs/reports/phase7_pre_cutover_drill_latest.json")
    parser.add_argument("--canary-report", default="docs/reports/phase7_canary_rollout_latest.json")
    parser.add_argument("--rollback-report", default="docs/reports/phase7_rollback_drill_latest.json")
    parser.add_argument("--oncall-report", default="docs/reports/phase8_oncall_handbook_latest.json")
    parser.add_argument("--ops-report", default="docs/reports/phase8_ops_metrics_dashboard_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase8_fault_drill_scoring_latest.json")
    parser.add_argument("--output-report", default="docs/reports/phase8_fault_drill_scoring_latest.md")
    parser.add_argument("--output-ledger", default="docs/reports/phase8_fault_drill_improvement_ledger_latest.md")
    args = parser.parse_args()

    if not REPORT_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {REPORT_TEMPLATE}")
    if not LEDGER_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {LEDGER_TEMPLATE}")

    policy = load_json(args.policy)
    weights = policy.get("weights") or {}
    grading = policy.get("grading") or {}
    sla = policy.get("improvement_sla_days") or {}

    pre = load_json(args.pre_cutover_report)
    canary = load_json(args.canary_report)
    rollback = load_json(args.rollback_report)
    oncall = load_json(args.oncall_report)
    ops = load_json(args.ops_report)

    pre_summary = pre.get("summary") or {}
    pre_total = int(pre_summary.get("total", 0))
    pre_passed = int(pre_summary.get("passed", 0))
    pre_rate = (pre_passed / pre_total) if pre_total > 0 else 0.0

    canary_summary = canary.get("summary") or {}
    canary_total = int(canary_summary.get("total_phases", 0))
    canary_passed = int(canary_summary.get("passed_phases", 0))
    canary_rate = (canary_passed / canary_total) if canary_total > 0 else 0.0

    rollback_ready = bool(rollback.get("rollback_ready"))
    oncall_level = str(oncall.get("current_level", "P3"))
    ops_status = str((ops.get("assessment") or {}).get("overall_status", "UNKNOWN"))

    # Subscores in [0, 1]
    rollback_score = 1.0 if rollback_ready else 0.0
    oncall_score_map = {"P1": 0.2, "P2": 0.6, "P3": 1.0}
    oncall_score = oncall_score_map.get(oncall_level, 0.5)
    ops_score_map = {"RED": 0.2, "YELLOW": 0.6, "GREEN": 1.0}
    ops_score = ops_score_map.get(ops_status, 0.5)

    w_pre = float(weights.get("pre_cutover_pass_rate", 35))
    w_canary = float(weights.get("canary_pass_rate", 25))
    w_rollback = float(weights.get("rollback_ready", 20))
    w_oncall = float(weights.get("oncall_level", 10))
    w_ops = float(weights.get("ops_overall_status", 10))
    total_weight = w_pre + w_canary + w_rollback + w_oncall + w_ops
    if total_weight <= 0:
        total_weight = 100.0

    total_score = clamp_score(
        (pre_rate * w_pre + canary_rate * w_canary + rollback_score * w_rollback + oncall_score * w_oncall + ops_score * w_ops)
        / total_weight
        * 100.0
    )

    grade_a = float(grading.get("A", 85))
    grade_b = float(grading.get("B", 70))
    grade_c = float(grading.get("C", 50))
    if total_score >= grade_a:
        grade = "A"
    elif total_score >= grade_b:
        grade = "B"
    elif total_score >= grade_c:
        grade = "C"
    else:
        grade = "D"

    risks: list[str] = []
    actions: list[dict[str, str]] = []

    def add_action(source: str, priority: str, owner: str, content: str, sla_days: int) -> None:
        due = (datetime.now() + timedelta(days=sla_days)).strftime("%Y-%m-%d")
        actions.append(
            {
                "source": source,
                "priority": priority,
                "owner": owner,
                "content": content,
                "due": due,
            }
        )

    if pre_rate < 1.0:
        risks.append(f"pre-cutover 通过率不足（{pre_passed}/{pre_total}）。")
        add_action("pre_cutover", "high", args.owner, "补齐预切换演练失败项并复测", int(sla.get("high", 3)))
    if canary_rate < 1.0:
        risks.append(f"canary 通过率不足（{canary_passed}/{canary_total}）。")
        add_action("canary", "high", args.owner, "修复灰度失败阶段并重跑 canary", int(sla.get("high", 3)))
    if not rollback_ready:
        risks.append("rollback drill 未就绪。")
        add_action("rollback", "critical", args.owner, "修复回退预检并验证恢复链路", int(sla.get("critical", 1)))
    if oncall_level in {"P1", "P2"}:
        risks.append(f"当前 on-call 级别偏高（{oncall_level}）。")
        add_action("oncall", "medium", args.owner, "降低告警等级并完成交接闭环", int(sla.get("medium", 7)))
    if ops_status in {"RED", "YELLOW"}:
        risks.append(f"ops 看板状态为 {ops_status}。")
        add_action("ops", "medium", args.owner, "处理容量/可用性风险后刷新看板", int(sla.get("medium", 7)))
    if not risks:
        risks.append("演练链路整体稳定，无阻塞风险。")
        add_action("stability", "low", args.owner, "保持周期性演练并复核评分策略", int(sla.get("low", 14)))

    score_rows = [
        ("pre_cutover_pass_rate", f"{w_pre:g}", f"{pre_rate:.4f}", f"{pre_rate * w_pre / total_weight * 100:.2f}"),
        ("canary_pass_rate", f"{w_canary:g}", f"{canary_rate:.4f}", f"{canary_rate * w_canary / total_weight * 100:.2f}"),
        ("rollback_ready", f"{w_rollback:g}", str(rollback_ready), f"{rollback_score * w_rollback / total_weight * 100:.2f}"),
        ("oncall_level", f"{w_oncall:g}", oncall_level, f"{oncall_score * w_oncall / total_weight * 100:.2f}"),
        ("ops_overall_status", f"{w_ops:g}", ops_status, f"{ops_score * w_ops / total_weight * 100:.2f}"),
    ]

    summary = (
        f"score={total_score:.2f}, grade={grade}, pre_rate={pre_rate:.4f}, canary_rate={canary_rate:.4f}, "
        f"rollback_ready={rollback_ready}, oncall={oncall_level}, ops={ops_status}."
    )
    result = {
        "timestamp": utc_now_iso(),
        "inputs": {
            "version": args.version,
            "owner": args.owner,
            "policy": args.policy,
            "pre_cutover_report": args.pre_cutover_report,
            "canary_report": args.canary_report,
            "rollback_report": args.rollback_report,
            "oncall_report": args.oncall_report,
            "ops_report": args.ops_report,
        },
        "metrics": {
            "pre_cutover_pass_rate": pre_rate,
            "canary_pass_rate": canary_rate,
            "rollback_ready": rollback_ready,
            "oncall_level": oncall_level,
            "ops_overall_status": ops_status,
        },
        "score": {
            "total": total_score,
            "grade": grade,
            "rows": score_rows,
        },
        "risks": risks,
        "actions": actions,
        "summary": summary,
    }

    report_text = render(
        REPORT_TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "TOTAL_SCORE": f"{total_score:.2f}",
            "GRADE": grade,
            "SUMMARY": summary,
            "SCORE_TABLE": "\n".join(f"| {a} | {b} | {c} | {d} |" for a, b, c, d in score_rows),
            "RISK_ITEMS": "\n".join(f"- {item}" for item in risks),
            "EVIDENCE_ITEMS": "\n".join(
                [
                    f"- policy: `{args.policy}`",
                    f"- pre-cutover: `{args.pre_cutover_report}`",
                    f"- canary: `{args.canary_report}`",
                    f"- rollback: `{args.rollback_report}`",
                    f"- oncall: `{args.oncall_report}`",
                    f"- ops: `{args.ops_report}`",
                ]
            ),
        },
    )

    action_rows = []
    for idx, action in enumerate(actions, start=1):
        action_rows.append(
            f"| DRILL-ACT-{idx:03d} | {action['source']} | {action['priority']} | {action['owner']} | "
            f"{action['due']} | 完成复测并更新报告 | 待开始 |"
        )
    ledger_text = render(
        LEDGER_TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d"),
            "VERSION": args.version,
            "ACTION_ROWS": "\n".join(action_rows),
        },
    )

    output_json = ROOT / args.output_json
    output_report = ROOT / args.output_report
    output_ledger = ROOT / args.output_ledger
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_ledger.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    output_report.write_text(report_text, encoding="utf-8")
    output_ledger.write_text(ledger_text, encoding="utf-8")

    print(
        f"[phase8-drill-score] score={total_score:.2f} grade={grade} json={output_json} "
        f"report={output_report} ledger={output_ledger}"
    )
    return 1 if grade == "D" else 0


if __name__ == "__main__":
    raise SystemExit(main())
