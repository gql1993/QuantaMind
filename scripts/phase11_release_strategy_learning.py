#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase11_发布策略学习报告模板.md"


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
    for k, v in mapping.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 11 release strategy learning.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="release-manager")
    parser.add_argument("--policy", default="docs/phase11_strategy_learning_policy.json")
    parser.add_argument("--weekly-report", default="docs/reports/phase9_executive_weekly_latest.json")
    parser.add_argument("--gate-report", default="docs/reports/phase10_quality_gate_latest.json")
    parser.add_argument("--drift-report", default="docs/reports/phase9_policy_drift_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase11_strategy_learning_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase11_strategy_learning_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    cfg = load_json(args.policy)
    sig = cfg.get("learning_signals") or {}
    weekly_w = float(sig.get("weekly_grade_weight", 0.4))
    gate_w = float(sig.get("quality_gate_weight", 0.3))
    drift_w = float(sig.get("drift_weight", 0.3))

    weekly = load_json(args.weekly_report)
    gate = load_json(args.gate_report)
    drift = load_json(args.drift_report)

    grade = str(weekly.get("grade", "D"))
    weekly_score_map = {"A": 95, "B": 80, "C": 65, "D": 40}
    weekly_score = float(weekly_score_map.get(grade, 40))

    gate_result = str(gate.get("result", "BLOCK"))
    gate_score_map = {"PASS": 95, "WARN": 70, "BLOCK": 35}
    gate_score = float(gate_score_map.get(gate_result, 35))

    drift_result = str(drift.get("result", "ADJUST_REQUIRED"))
    drift_score_map = {"STABLE": 90, "ADJUST_REQUIRED": 55}
    drift_score = float(drift_score_map.get(drift_result, 55))

    total = weekly_score * weekly_w + gate_score * gate_w + drift_score * drift_w

    th = cfg.get("action_thresholds") or {}
    tighten_max = float(th.get("tighten_policy_score_max", 45))
    relax_min = float(th.get("relax_policy_score_min", 80))
    if total <= tighten_max:
        action = "TIGHTEN"
        suggestions = [
            "收紧发布门禁，降低并行高风险变更上限。",
            "提升 P1/P2 告警触发后的冻结时长。",
        ]
    elif total >= relax_min:
        action = "RELAX"
        suggestions = [
            "可适度放宽低风险发布并行度。",
            "保留关键门禁不变，提升交付效率。",
        ]
    else:
        action = "KEEP"
        suggestions = [
            "维持当前策略并继续观察 1~2 个周期。",
        ]

    summary = f"score={total:.1f}, action={action}, weekly={grade}, gate={gate_result}, drift={drift_result}."
    out = {
        "timestamp": datetime.now().isoformat(),
        "score": total,
        "action": action,
        "summary": summary,
        "signals": {
            "weekly_grade": grade,
            "quality_gate": gate_result,
            "drift": drift_result,
        },
        "suggestions": suggestions,
    }

    rows = [
        ("weekly_grade", grade, f"{weekly_w:.2f}", f"{weekly_score * weekly_w:.1f}"),
        ("quality_gate", gate_result, f"{gate_w:.2f}", f"{gate_score * gate_w:.1f}"),
        ("policy_drift", drift_result, f"{drift_w:.2f}", f"{drift_score * drift_w:.1f}"),
    ]
    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "SCORE": f"{total:.1f}",
            "ACTION": action,
            "SUMMARY": summary,
            "SIGNAL_TABLE": "\n".join(f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows),
            "SUGGEST_ITEMS": "\n".join(f"- {s}" for s in suggestions),
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase11-strategy] score={total:.1f} action={action} json={out_json} markdown={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
