#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HANDBOOK_TEMPLATE = ROOT / "docs" / "templates" / "Phase8_OnCall响应手册模板.md"
HANDOFF_TEMPLATE = ROOT / "docs" / "templates" / "Phase8_OnCall交接模板.md"


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


def decide_level(ops: dict[str, Any], guard: dict[str, Any], dep: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    ops_status = str((ops.get("assessment") or {}).get("overall_status", "UNKNOWN"))
    guard_decision = str((guard.get("summary") or {}).get("decision", "unknown"))
    dep_result = str((dep.get("assessment") or {}).get("result", "UNKNOWN"))

    if ops_status == "RED":
        reasons.append("ops dashboard 为 RED")
    if guard_decision == "rollback_now":
        reasons.append("observability guard 判定 rollback_now")
    if dep_result == "BLOCK":
        reasons.append("dependency compatibility 为 BLOCK")
    if reasons:
        return "P1", reasons

    if ops_status == "YELLOW":
        reasons.append("ops dashboard 为 YELLOW")
    if guard_decision == "warn":
        reasons.append("observability guard 为 warn")
    if dep_result == "CONDITIONAL_PASS":
        reasons.append("dependency compatibility 为 CONDITIONAL_PASS")
    if reasons:
        return "P2", reasons

    return "P3", ["当前输入无高优先级告警，进入常规跟踪"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Phase8 layered alert + on-call handbook.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="oncall-manager")
    parser.add_argument("--policy", default="docs/phase8_alert_policy.json")
    parser.add_argument("--guard-report", default="docs/reports/phase7_observability_guard_latest.json")
    parser.add_argument("--ops-report", default="docs/reports/phase8_ops_metrics_dashboard_latest.json")
    parser.add_argument("--dependency-report", default="docs/reports/phase8_dependency_compat_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase8_oncall_handbook_latest.json")
    parser.add_argument("--output-handbook", default="docs/reports/phase8_oncall_handbook_latest.md")
    parser.add_argument("--output-handoff", default="docs/reports/phase8_oncall_handoff_latest.md")
    args = parser.parse_args()

    if not HANDBOOK_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {HANDBOOK_TEMPLATE}")
    if not HANDOFF_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {HANDOFF_TEMPLATE}")

    policy = load_json(args.policy)
    guard = load_json(args.guard_report)
    ops = load_json(args.ops_report)
    dep = load_json(args.dependency_report)

    level, reasons = decide_level(ops, guard, dep)
    levels = policy.get("levels") or {}
    escalation = policy.get("escalation") or []

    level_table = []
    for lv in ["P1", "P2", "P3"]:
        cfg = levels.get(lv) or {}
        trigger_text = "; ".join(cfg.get("triggers") or [])
        level_table.append(
            f"| {lv} | {cfg.get('description', '-')} | {trigger_text} | {cfg.get('sla_minutes', '-')} min |"
        )
    escalation_table = []
    for row in escalation:
        escalation_table.append(
            f"| {row.get('level')} | {', '.join(row.get('notify_roles', []))} | {row.get('channel', '-')} |"
        )

    runbook_items = []
    if level == "P1":
        runbook_items.extend(
            [
                "- 0~5 分钟：确认告警源与影响面，拉起 war-room。",
                "- 5~15 分钟：执行止损动作（限流/降级/回退评估）。",
                "- 15 分钟后：持续同步进展并准备复盘证据。",
            ]
        )
    elif level == "P2":
        runbook_items.extend(
            [
                "- 0~15 分钟：定位异常子系统并安排负责人。",
                "- 15~60 分钟：完成修复/绕行并回归验证。",
                "- 60 分钟后：若未恢复，升级到 P1 流程。",
            ]
        )
    else:
        runbook_items.extend(
            [
                "- 纳入日常巡检队列并观察趋势。",
                "- 若出现连发或扩散迹象，升级到 P2。",
            ]
        )

    summary = f"current_level={level}; reasons=" + "; ".join(reasons)
    report = {
        "timestamp": utc_now_iso(),
        "inputs": {
            "policy": args.policy,
            "guard_report": args.guard_report,
            "ops_report": args.ops_report,
            "dependency_report": args.dependency_report,
            "version": args.version,
            "owner": args.owner,
        },
        "current_level": level,
        "reasons": reasons,
        "summary": summary,
    }

    handbook_text = render(
        HANDBOOK_TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "CURRENT_LEVEL": level,
            "EXEC_SUMMARY": summary,
            "LEVEL_TABLE": "\n".join(level_table),
            "ESCALATION_TABLE": "\n".join(escalation_table),
            "RUNBOOK_ITEMS": "\n".join(runbook_items),
        },
    )
    handoff_text = render(
        HANDOFF_TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "CURRENT_LEVEL": level,
        },
    )

    output_json = ROOT / args.output_json
    output_handbook = ROOT / args.output_handbook
    output_handoff = ROOT / args.output_handoff
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_handbook.parent.mkdir(parents=True, exist_ok=True)
    output_handoff.parent.mkdir(parents=True, exist_ok=True)

    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output_handbook.write_text(handbook_text, encoding="utf-8")
    output_handoff.write_text(handoff_text, encoding="utf-8")

    print(
        f"[phase8-oncall] level={level} json={output_json} handbook={output_handbook} handoff={output_handoff}"
    )
    return 1 if level == "P1" else 0


if __name__ == "__main__":
    raise SystemExit(main())
