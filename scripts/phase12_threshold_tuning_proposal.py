#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase12_阈值调参提案模板.md"


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


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 12 threshold tuning proposal generator.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="ops-manager")
    parser.add_argument("--tuning-policy", default="docs/phase12_threshold_tuning_policy.json")
    parser.add_argument("--strategy-report", default="docs/reports/phase11_strategy_learning_latest.json")
    parser.add_argument("--ops-policy", default="docs/phase8_ops_metrics_policy.json")
    parser.add_argument("--output-json", default="docs/reports/phase12_threshold_tuning_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase12_threshold_tuning_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    tuning = load_json(args.tuning_policy)
    strategy = load_json(args.strategy_report)
    ops_policy = load_json(args.ops_policy)
    action = str(strategy.get("action", "KEEP")).lower()
    if action not in {"tighten", "relax"}:
        action = "keep"

    current_capacity = float((ops_policy.get("capacity") or {}).get("warn_utilization_ratio", 0.7))
    current_budget = float((ops_policy.get("slo") or {}).get("error_budget_warn_ratio", 0.7))

    delta_cfg = (tuning.get("proposals") or {}).get(action, {})
    d_capacity = float(delta_cfg.get("capacity_warn_utilization", 0.0))
    d_budget = float(delta_cfg.get("error_budget_warn_ratio", 0.0))

    proposed_capacity = clamp01(current_capacity + d_capacity)
    proposed_budget = clamp01(current_budget + d_budget)

    summary = (
        f"action={action.upper()}, capacity_warn={current_capacity:.2f}->{proposed_capacity:.2f}, "
        f"budget_warn={current_budget:.2f}->{proposed_budget:.2f}"
    )
    out = {
        "timestamp": datetime.now().isoformat(),
        "action": action.upper(),
        "summary": summary,
        "proposals": [
            {
                "param": "capacity.warn_utilization_ratio",
                "current": current_capacity,
                "proposed": proposed_capacity,
                "delta": proposed_capacity - current_capacity,
            },
            {
                "param": "slo.error_budget_warn_ratio",
                "current": current_budget,
                "proposed": proposed_budget,
                "delta": proposed_budget - current_budget,
            },
        ],
    }

    rows = "\n".join(
        f"| {p['param']} | {p['current']:.2f} | {p['proposed']:.2f} | {p['delta']:+.2f} |" for p in out["proposals"]
    )
    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "ACTION": out["action"],
            "SUMMARY": summary,
            "PROPOSAL_TABLE": rows,
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase12-tuning] action={out['action']} json={out_json} markdown={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
