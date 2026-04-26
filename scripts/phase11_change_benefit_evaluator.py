#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase11_变更收益评估报告模板.md"


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
    parser = argparse.ArgumentParser(description="Phase 11 change benefit evaluator.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--weekly-report", default="docs/reports/phase9_executive_weekly_latest.json")
    parser.add_argument("--gate-report", default="docs/reports/phase10_quality_gate_latest.json")
    parser.add_argument("--strategy-report", default="docs/reports/phase11_strategy_learning_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase11_change_benefit_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase11_change_benefit_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    weekly = load_json(args.weekly_report)
    gate = load_json(args.gate_report)
    strategy = load_json(args.strategy_report)

    weekly_score = float(weekly.get("score", 0.0))
    gate_result = str(gate.get("result", "BLOCK"))
    strategy_score = float(strategy.get("score", 0.0))
    strategy_action = str(strategy.get("action", "TIGHTEN"))

    gate_bonus = {"PASS": 30, "WARN": 10, "BLOCK": -20}.get(gate_result, -20)
    action_bonus = {"RELAX": 10, "KEEP": 5, "TIGHTEN": 0}.get(strategy_action, 0)

    benefit_score = max(0.0, min(100.0, weekly_score * 0.5 + strategy_score * 0.3 + gate_bonus + action_bonus))
    if benefit_score >= 80:
        result = "HIGH"
    elif benefit_score >= 60:
        result = "MEDIUM"
    else:
        result = "LOW"
    summary = f"benefit={benefit_score:.1f}, weekly={weekly_score:.1f}, strategy={strategy_score:.1f}, gate={gate_result}."

    rows = [
        ("weekly_score", f"{weekly_score:.1f}", "周度经营表现"),
        ("strategy_score", f"{strategy_score:.1f}", f"策略学习动作={strategy_action}"),
        ("quality_gate", gate_result, "门禁结果对收益折算"),
    ]
    out = {
        "timestamp": datetime.now().isoformat(),
        "benefit_score": benefit_score,
        "result": result,
        "summary": summary,
        "rows": rows,
    }

    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "BENEFIT_SCORE": f"{benefit_score:.1f}",
            "RESULT": result,
            "SUMMARY": summary,
            "BENEFIT_TABLE": "\n".join(f"| {a} | {b} | {c} |" for a, b, c in rows),
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase11-benefit] score={benefit_score:.1f} result={result} json={out_json} markdown={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
