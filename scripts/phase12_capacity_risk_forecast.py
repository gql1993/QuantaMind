#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase12_预测性容量与风险窗口报告模板.md"


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
    parser = argparse.ArgumentParser(description="Phase 12 capacity and risk-window forecast.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--policy", default="docs/phase12_forecast_policy.json")
    parser.add_argument("--ops-report", default="docs/reports/phase8_ops_metrics_dashboard_latest.json")
    parser.add_argument("--oncall-report", default="docs/reports/phase8_oncall_handbook_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase12_capacity_forecast_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase12_capacity_forecast_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    cfg = load_json(args.policy)
    ops = load_json(args.ops_report)
    oncall = load_json(args.oncall_report)

    pressure = float((ops.get("metrics") or {}).get("capacity_pressure", 1.0))
    oncall_level = str(oncall.get("current_level", "P3"))
    high_min = float(((cfg.get("risk_windows") or {}).get("high_capacity_pressure_min", 0.8)))
    medium_min = float(((cfg.get("risk_windows") or {}).get("medium_capacity_pressure_min", 0.6)))
    horizon = int(cfg.get("forecast_horizon_hours", 24))

    if pressure >= high_min or oncall_level == "P1":
        risk = "HIGH"
    elif pressure >= medium_min or oncall_level == "P2":
        risk = "MEDIUM"
    else:
        risk = "LOW"

    summary = f"pressure={pressure:.4f}, oncall={oncall_level}, horizon={horizon}h, risk={risk}."
    rows = [
        ("capacity_pressure", f"{pressure:.4f}", f"high>={high_min:.2f}/medium>={medium_min:.2f}", risk),
        ("oncall_level", oncall_level, "P1/P2 为高风险信号", risk),
    ]
    out = {
        "timestamp": datetime.now().isoformat(),
        "risk_level": risk,
        "horizon_hours": horizon,
        "summary": summary,
        "rows": rows,
    }

    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "RISK_LEVEL": risk,
            "HORIZON": str(horizon),
            "SUMMARY": summary,
            "FORECAST_TABLE": "\n".join(f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows),
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase12-forecast] risk={risk} json={out_json} markdown={out_md}")
    return 1 if risk == "HIGH" else 0


if __name__ == "__main__":
    raise SystemExit(main())
