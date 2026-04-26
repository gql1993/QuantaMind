#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase9_多周期运营复盘与预算联动报告模板.md"


def load_json(path: str) -> dict[str, Any]:
    p = ROOT / path
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def render(text: str, mapping: dict[str, str]) -> str:
    out = text
    for key, val in mapping.items():
        out = out.replace("{{" + key + "}}", val)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 9 multi-cycle retro and budget linkage.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="release-manager")
    parser.add_argument("--policy", default="docs/phase9_budget_linkage_policy.json")
    parser.add_argument("--weekly-report", default="docs/reports/phase9_executive_weekly_latest.json")
    parser.add_argument("--drift-report", default="docs/reports/phase9_policy_drift_latest.json")
    parser.add_argument("--ops-report", default="docs/reports/phase8_ops_metrics_dashboard_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase9_ops_budget_linkage_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase9_ops_budget_linkage_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    policy = load_json(args.policy)
    weekly = load_json(args.weekly_report)
    drift = load_json(args.drift_report)
    ops = load_json(args.ops_report)

    grade = str(weekly.get("grade", "D"))
    ops_status = str((ops.get("assessment") or {}).get("overall_status", "RED"))
    drift_result = str(drift.get("result", "ADJUST_REQUIRED"))

    factor = float((policy.get("budget_per_grade") or {}).get(grade, 1.5))
    base_days = int(policy.get("base_engineering_days", 10))
    suggested_days = round(base_days * factor, 1)
    focus = str((policy.get("focus_mapping") or {}).get(ops_status, "stability-first"))

    table_rows = [
        ("weekly_grade", grade, f"资源系数={factor}"),
        ("ops_status", ops_status, f"工作焦点={focus}"),
        ("policy_drift", drift_result, "ADJUST_REQUIRED 时优先配置稳定性资源"),
    ]

    plans = [
        f"建议下周期投入 {suggested_days} 人天用于 {focus}。",
        "保留 20% 预算用于紧急回归与告警收敛。",
    ]
    if drift_result == "ADJUST_REQUIRED":
        plans.append("增加阈值调优专项并在下一周期复核效果。")

    summary = (
        f"grade={grade}, ops={ops_status}, drift={drift_result}, "
        f"budget_factor={factor}, suggested_days={suggested_days}."
    )
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": summary,
        "grade": grade,
        "ops_status": ops_status,
        "drift_result": drift_result,
        "budget_factor": factor,
        "suggested_engineering_days": suggested_days,
        "focus": focus,
        "plans": plans,
    }

    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "GRADE": grade,
            "BUDGET_FACTOR": f"{factor:.2f}",
            "SUMMARY": summary,
            "BUDGET_TABLE": "\n".join(f"| {a} | {b} | {c} |" for a, b, c in table_rows),
            "PLAN_ITEMS": "\n".join(f"- {p}" for p in plans),
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase9-budget-link] factor={factor:.2f} days={suggested_days} json={out_json} markdown={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
