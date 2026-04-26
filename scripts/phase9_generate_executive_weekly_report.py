#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "templates" / "Phase9_管理驾驶舱周报模板.md"


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 9 executive weekly report generator.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="release-manager")
    parser.add_argument("--policy", default="docs/phase9_executive_weekly_policy.json")
    parser.add_argument("--ops-report", default="docs/reports/phase8_ops_metrics_dashboard_latest.json")
    parser.add_argument("--oncall-report", default="docs/reports/phase8_oncall_handbook_latest.json")
    parser.add_argument("--wave-report", default="docs/reports/phase8_wave_rollout_backpressure_latest.json")
    parser.add_argument("--drill-report", default="docs/reports/phase8_fault_drill_scoring_latest.json")
    parser.add_argument("--bundle-report", default="docs/reports/phase9_daily_ops_bundle_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase9_executive_weekly_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase9_executive_weekly_latest.md")
    args = parser.parse_args()

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE_PATH}")

    policy = load_json(args.policy)
    ops = load_json(args.ops_report)
    oncall = load_json(args.oncall_report)
    wave = load_json(args.wave_report)
    drill = load_json(args.drill_report)
    bundle = load_json(args.bundle_report)

    status_weights = policy.get("status_weights") or {"GREEN": 100, "YELLOW": 70, "RED": 30}
    oncall_weights = policy.get("oncall_weights") or {"P3": 100, "P2": 70, "P1": 30}
    grade_threshold = policy.get("grade_threshold") or {"A": 85, "B": 70, "C": 55}

    ops_status = str((ops.get("assessment") or {}).get("overall_status", "RED"))
    oncall_level = str(oncall.get("current_level", "P1"))
    wave_decision = str(wave.get("decision", "HOLD"))
    drill_grade = str((drill.get("score") or {}).get("grade", "D"))
    bundle_result = str((bundle.get("summary") or {}).get("result", "ATTENTION"))

    drill_score_map = {"A": 100, "B": 80, "C": 60, "D": 30}
    wave_score_map = {"PROCEED": 100, "HOLD": 70, "ROLLBACK": 30, "PARTIAL_APPROVED": 75, "APPROVED": 100}
    bundle_score_map = {"PASS": 100, "ATTENTION": 60}

    score = (
        status_weights.get(ops_status, 30) * 0.25
        + oncall_weights.get(oncall_level, 30) * 0.2
        + wave_score_map.get(wave_decision, 50) * 0.2
        + drill_score_map.get(drill_grade, 30) * 0.2
        + bundle_score_map.get(bundle_result, 50) * 0.15
    )

    if score >= float(grade_threshold.get("A", 85)):
        grade = "A"
    elif score >= float(grade_threshold.get("B", 70)):
        grade = "B"
    elif score >= float(grade_threshold.get("C", 55)):
        grade = "C"
    else:
        grade = "D"

    risks = []
    next_actions = []
    if ops_status == "RED":
        risks.append("生产运行总览为 RED。")
        next_actions.append("优先恢复可用性并清理容量积压。")
    if oncall_level in {"P1", "P2"}:
        risks.append(f"on-call 等级偏高（{oncall_level}）。")
        next_actions.append("降低告警级别并完成值班交接闭环。")
    if wave_decision in {"HOLD", "ROLLBACK"}:
        risks.append(f"发布波次决策为 {wave_decision}。")
        next_actions.append("修复阻断项后重新评估发布窗口。")
    if drill_grade in {"C", "D"}:
        risks.append(f"故障演练评分等级为 {drill_grade}。")
        next_actions.append("按改进台账推进并完成复测。")
    if bundle_result != "PASS":
        risks.append("每日批任务存在 attention。")
        next_actions.append("排查失败任务并补齐证据归档。")
    if not risks:
        risks.append("本周关键指标整体稳定。")
        next_actions.append("保持节奏并推进下一阶段优化。")

    summary = (
        f"score={score:.1f}, grade={grade}, ops={ops_status}, oncall={oncall_level}, "
        f"wave={wave_decision}, drill={drill_grade}, bundle={bundle_result}."
    )

    status_rows = [
        ("Ops Dashboard", ops_status, "来源 phase8_ops_metrics_dashboard"),
        ("Oncall Level", oncall_level, "来源 phase8_oncall_handbook"),
        ("Wave Decision", wave_decision, "来源 phase8_wave_rollout_backpressure"),
        ("Drill Grade", drill_grade, "来源 phase8_fault_drill_scoring"),
        ("Daily Bundle", bundle_result, "来源 phase9_daily_ops_bundle"),
    ]

    report = {
        "timestamp": utc_now_iso(),
        "inputs": {
            "version": args.version,
            "owner": args.owner,
            "policy": args.policy,
            "ops_report": args.ops_report,
            "oncall_report": args.oncall_report,
            "wave_report": args.wave_report,
            "drill_report": args.drill_report,
            "bundle_report": args.bundle_report,
        },
        "score": score,
        "grade": grade,
        "summary": summary,
        "status_rows": status_rows,
        "risks": risks,
        "next_actions": next_actions,
    }

    report_md = render(
        TEMPLATE_PATH.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "SCORE": f"{score:.1f}",
            "GRADE": grade,
            "SUMMARY": summary,
            "STATUS_TABLE": "\n".join(f"| {a} | {b} | {c} |" for a, b, c in status_rows),
            "RISK_ITEMS": "\n".join(f"- {item}" for item in risks),
            "NEXT_ACTIONS": "\n".join(f"- {item}" for item in next_actions),
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(report_md, encoding="utf-8")

    print(f"[phase9-exec-weekly] grade={grade} score={score:.1f} json={out_json} markdown={out_md}")
    return 1 if grade == "D" else 0


if __name__ == "__main__":
    raise SystemExit(main())
