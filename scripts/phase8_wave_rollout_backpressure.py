#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_TEMPLATE = ROOT / "docs" / "templates" / "Phase8_发布波次与回压计划模板.md"
LOG_TEMPLATE = ROOT / "docs" / "templates" / "Phase8_发布波次执行记录模板.md"


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


def level_rank(level: str) -> int:
    # Lower number means stricter severity.
    mapping = {"P1": 1, "P2": 2, "P3": 3}
    return mapping.get(level, 99)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 8 multi-env rollout waves with capacity backpressure.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="release-manager")
    parser.add_argument("--policy", default="docs/phase8_rollout_backpressure_policy.json")
    parser.add_argument("--ops-report", default="docs/reports/phase8_ops_metrics_dashboard_latest.json")
    parser.add_argument("--oncall-report", default="docs/reports/phase8_oncall_handbook_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase8_wave_rollout_backpressure_latest.json")
    parser.add_argument("--output-plan", default="docs/reports/phase8_wave_rollout_backpressure_latest.md")
    parser.add_argument("--output-log", default="docs/reports/phase8_wave_rollout_execution_latest.md")
    args = parser.parse_args()

    if not PLAN_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {PLAN_TEMPLATE}")
    if not LOG_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {LOG_TEMPLATE}")

    policy = load_json(args.policy)
    ops = load_json(args.ops_report)
    oncall = load_json(args.oncall_report)
    waves = policy.get("waves") or []
    actions_map = policy.get("backpressure_actions") or {}

    oncall_level = str(oncall.get("current_level", "P3"))
    overall = str((ops.get("assessment") or {}).get("overall_status", "UNKNOWN"))
    capacity_pressure = float((ops.get("metrics") or {}).get("capacity_pressure", 1.0))

    decision = "PROCEED"
    reasons: list[str] = []
    if oncall_level == "P1" or overall == "RED":
        decision = "ROLLBACK"
        reasons.append("oncall 级别为 P1 或 ops 总体为 RED")
    elif oncall_level == "P2" or overall == "YELLOW":
        decision = "HOLD"
        reasons.append("oncall 级别为 P2 或 ops 总体为 YELLOW")

    wave_rows = []
    first_blocked = False
    for wave in waves:
        required_level = str(wave.get("required_oncall_max_level", "P3"))
        max_pressure = float(wave.get("max_capacity_pressure", 1.0))
        gates = []
        status = "ready"
        note = "可推进"

        if level_rank(oncall_level) < level_rank(required_level):
            gates.append(f"oncall<={required_level}")
            status = "blocked"
            note = f"当前 oncall={oncall_level}"
        if capacity_pressure > max_pressure:
            gates.append(f"capacity<={max_pressure:.2f}")
            status = "blocked"
            note = f"当前 capacity_pressure={capacity_pressure:.4f}"
        if first_blocked:
            status = "queued"
            note = "等待前序波次通过"
        if status == "blocked":
            first_blocked = True
        wave_rows.append(
            {
                "id": str(wave.get("id", "-")),
                "environment": str(wave.get("environment", "-")),
                "traffic_percent": str(wave.get("traffic_percent", "-")),
                "gate": ", ".join(gates) if gates else "oncall/capacity gate",
                "status": status,
                "note": note,
            }
        )

    if any(row["status"] == "blocked" for row in wave_rows) and decision == "PROCEED":
        decision = "HOLD"
        reasons.append("存在波次门禁未通过")

    if decision in actions_map:
        backpressure_items = actions_map.get(decision) or []
    else:
        backpressure_items = ["按计划推进下一波次并持续观测。"]
    summary = (
        f"decision={decision}, oncall={oncall_level}, ops={overall}, "
        f"capacity_pressure={capacity_pressure:.4f}, blocked_waves={sum(1 for r in wave_rows if r['status']=='blocked')}."
    )

    report = {
        "timestamp": utc_now_iso(),
        "inputs": {
            "version": args.version,
            "owner": args.owner,
            "policy": args.policy,
            "ops_report": args.ops_report,
            "oncall_report": args.oncall_report,
        },
        "context": {
            "oncall_level": oncall_level,
            "ops_overall_status": overall,
            "capacity_pressure": capacity_pressure,
        },
        "decision": decision,
        "reasons": reasons,
        "waves": wave_rows,
        "backpressure_actions": backpressure_items,
        "summary": summary,
    }

    plan_text = render(
        PLAN_TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "DECISION": decision,
            "SUMMARY": summary + ("; reasons=" + "; ".join(reasons) if reasons else ""),
            "WAVE_TABLE": "\n".join(
                f"| {row['id']} | {row['environment']} | {row['traffic_percent']}% | {row['gate']} | {row['status']} | {row['note']} |"
                for row in wave_rows
            ),
            "BACKPRESSURE_ITEMS": "\n".join(f"- {item}" for item in backpressure_items),
            "EVIDENCE_ITEMS": "\n".join(
                [
                    f"- policy: `{args.policy}`",
                    f"- ops report: `{args.ops_report}`",
                    f"- oncall report: `{args.oncall_report}`",
                ]
            ),
        },
    )
    log_text = render(
        LOG_TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
        },
    )

    output_json = ROOT / args.output_json
    output_plan = ROOT / args.output_plan
    output_log = ROOT / args.output_log
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_plan.parent.mkdir(parents=True, exist_ok=True)
    output_log.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output_plan.write_text(plan_text, encoding="utf-8")
    output_log.write_text(log_text, encoding="utf-8")

    print(f"[phase8-wave-rollout] decision={decision} json={output_json} plan={output_plan} log={output_log}")
    return 1 if decision == "ROLLBACK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
