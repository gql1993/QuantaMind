#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase9_策略漂移检测报告模板.md"


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


def rank_oncall(level: str) -> int:
    return {"P1": 1, "P2": 2, "P3": 3}.get(level, 99)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 9 policy drift detector and adaptive threshold advisor.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="ops-manager")
    parser.add_argument("--policy", default="docs/phase9_drift_policy.json")
    parser.add_argument("--ops-report", default="docs/reports/phase8_ops_metrics_dashboard_latest.json")
    parser.add_argument("--weekly-report", default="docs/reports/phase9_executive_weekly_latest.json")
    parser.add_argument("--oncall-report", default="docs/reports/phase8_oncall_handbook_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase9_policy_drift_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase9_policy_drift_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    cfg = load_json(args.policy)
    ops = load_json(args.ops_report)
    weekly = load_json(args.weekly_report)
    oncall = load_json(args.oncall_report)

    thr = cfg.get("drift_thresholds") or {}
    suggest_cfg = cfg.get("adaptive_suggestions") or {}

    capacity_current = float((ops.get("metrics") or {}).get("capacity_pressure", 1.0))
    capacity_baseline = 0.5
    capacity_delta = capacity_current - capacity_baseline

    score_current = float(weekly.get("score", 0.0))
    score_baseline = 70.0
    score_drop = score_baseline - score_current

    oncall_level = str(oncall.get("current_level", "P3"))
    oncall_base = "P3"
    oncall_worse = rank_oncall(oncall_level) < rank_oncall(oncall_base)

    capacity_warn = float(thr.get("capacity_pressure_delta_warn", 0.15))
    score_drop_warn = float(thr.get("score_drop_warn", 10))
    drift_rows = []
    alerts = 0

    cap_judgement = "drift" if capacity_delta > capacity_warn else "stable"
    if cap_judgement == "drift":
        alerts += 1
    drift_rows.append(("capacity_pressure", f"{capacity_current:.4f}", f"{capacity_baseline:.4f}", f"{capacity_delta:.4f}", cap_judgement))

    score_judgement = "drift" if score_drop > score_drop_warn else "stable"
    if score_judgement == "drift":
        alerts += 1
    drift_rows.append(("weekly_score", f"{score_current:.1f}", f"{score_baseline:.1f}", f"{score_drop:.1f}", score_judgement))

    oncall_judgement = "drift" if oncall_worse else "stable"
    if oncall_judgement == "drift":
        alerts += 1
    drift_rows.append(("oncall_level", oncall_level, oncall_base, f"{oncall_base}->{oncall_level}", oncall_judgement))

    suggestions = []
    if capacity_delta > capacity_warn:
        step = float(suggest_cfg.get("capacity_warn_ratio_step", 0.05))
        suggestions.append(f"建议将容量告警阈值收紧 {step:.2f}（短期）并配套限流策略。")
    if score_drop > score_drop_warn:
        step = float(suggest_cfg.get("error_budget_warn_ratio_step", 0.05))
        suggestions.append(f"建议将错误预算预警阈值下调 {step:.2f}，提前触发干预。")
    if oncall_worse:
        suggestions.append("建议提升 on-call 值班密度并提前预热回退预案。")
    if not suggestions:
        suggestions.append("当前未发现显著策略漂移，建议维持现行阈值并持续观察。")

    result = "ADJUST_REQUIRED" if alerts > 0 else "STABLE"
    summary = f"alerts={alerts}, capacity_delta={capacity_delta:.4f}, score_drop={score_drop:.1f}, oncall={oncall_level}."

    out = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "result": result,
        "summary": summary,
        "drift_rows": drift_rows,
        "suggestions": suggestions,
    }

    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "RESULT": result,
            "SUMMARY": summary,
            "DRIFT_TABLE": "\n".join(f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in drift_rows),
            "SUGGEST_ITEMS": "\n".join(f"- {x}" for x in suggestions),
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase9-drift] result={result} json={out_json} markdown={out_md}")
    return 1 if result == "ADJUST_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
