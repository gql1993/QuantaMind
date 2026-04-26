#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase12_统一运营驾驶舱趋势报告模板.md"


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
    parser = argparse.ArgumentParser(description="Phase 12 unified dashboard trend generator.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="ops-manager")
    parser.add_argument("--weekly-report", default="docs/reports/phase9_executive_weekly_latest.json")
    parser.add_argument("--gate-report", default="docs/reports/phase10_quality_gate_latest.json")
    parser.add_argument("--drift-report", default="docs/reports/phase9_policy_drift_latest.json")
    parser.add_argument("--forecast-report", default="docs/reports/phase12_capacity_forecast_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase12_unified_dashboard_trend_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase12_unified_dashboard_trend_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    weekly = load_json(args.weekly_report)
    gate = load_json(args.gate_report)
    drift = load_json(args.drift_report)
    forecast = load_json(args.forecast_report)

    weekly_grade = str(weekly.get("grade", "D"))
    gate_result = str(gate.get("result", "BLOCK"))
    drift_result = str(drift.get("result", "ADJUST_REQUIRED"))
    forecast_risk = str(forecast.get("risk_level", "HIGH"))

    red_flags = 0
    if weekly_grade == "D":
        red_flags += 1
    if gate_result == "BLOCK":
        red_flags += 1
    if drift_result == "ADJUST_REQUIRED":
        red_flags += 1
    if forecast_risk == "HIGH":
        red_flags += 1

    if red_flags >= 3:
        trend = "CRITICAL"
    elif red_flags >= 1:
        trend = "WATCH"
    else:
        trend = "STABLE"

    rows = [
        ("weekly_grade", weekly_grade, "down" if weekly_grade in {"C", "D"} else "up/stable"),
        ("quality_gate", gate_result, "down" if gate_result == "BLOCK" else "stable"),
        ("policy_drift", drift_result, "watch" if drift_result == "ADJUST_REQUIRED" else "stable"),
        ("capacity_forecast", forecast_risk, "down" if forecast_risk == "HIGH" else "stable"),
    ]
    summary = f"trend={trend}, red_flags={red_flags}, weekly={weekly_grade}, gate={gate_result}, drift={drift_result}, forecast={forecast_risk}."
    out = {
        "timestamp": datetime.now().isoformat(),
        "trend_status": trend,
        "summary": summary,
        "rows": rows,
    }

    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "TREND_STATUS": trend,
            "SUMMARY": summary,
            "TREND_TABLE": "\n".join(f"| {a} | {b} | {c} |" for a, b, c in rows),
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase12-trend] status={trend} json={out_json} markdown={out_md}")
    return 1 if trend == "CRITICAL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
