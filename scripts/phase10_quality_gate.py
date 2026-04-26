#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase10_质量门禁评估报告模板.md"


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
    parser = argparse.ArgumentParser(description="Phase 10 quality gate evaluator.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="qa-manager")
    parser.add_argument("--policy", default="docs/phase10_quality_gate_policy.json")
    parser.add_argument("--dep-report", default="docs/reports/phase8_dependency_compat_latest.json")
    parser.add_argument("--wave-report", default="docs/reports/phase8_wave_rollout_backpressure_latest.json")
    parser.add_argument("--drill-report", default="docs/reports/phase8_fault_drill_scoring_latest.json")
    parser.add_argument("--weekly-report", default="docs/reports/phase9_executive_weekly_latest.json")
    parser.add_argument("--bundle-report", default="docs/reports/phase9_daily_ops_bundle_latest.json")
    parser.add_argument("--drift-report", default="docs/reports/phase9_policy_drift_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase10_quality_gate_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase10_quality_gate_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    dep = load_json(args.dep_report)
    wave = load_json(args.wave_report)
    drill = load_json(args.drill_report)
    weekly = load_json(args.weekly_report)
    bundle = load_json(args.bundle_report)
    drift = load_json(args.drift_report)

    dep_result = str((dep.get("assessment") or {}).get("result", "UNKNOWN"))
    wave_decision = str(wave.get("decision", "UNKNOWN"))
    drill_grade = str((drill.get("score") or {}).get("grade", "UNKNOWN"))
    weekly_grade = str(weekly.get("grade", "UNKNOWN"))
    bundle_result = str((bundle.get("summary") or {}).get("result", "UNKNOWN"))
    drift_result = str(drift.get("result", "UNKNOWN"))

    blocks = []
    warns = []
    if dep_result == "BLOCK":
        blocks.append("依赖兼容性结果为 BLOCK")
    if wave_decision == "ROLLBACK":
        blocks.append("发布波次决策为 ROLLBACK")
    if drill_grade == "D":
        blocks.append("故障演练评分为 D")
    if weekly_grade == "D":
        blocks.append("管理周报等级为 D")

    if wave_decision == "HOLD":
        warns.append("发布波次决策为 HOLD")
    if bundle_result == "ATTENTION":
        warns.append("每日巡检批任务为 ATTENTION")
    if drift_result == "ADJUST_REQUIRED":
        warns.append("策略漂移建议 ADJUST_REQUIRED")

    if blocks:
        result = "BLOCK"
    elif warns:
        result = "WARN"
    else:
        result = "PASS"
    summary = f"result={result}, blocks={len(blocks)}, warns={len(warns)}."

    out = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "result": result,
        "summary": summary,
        "blocks": blocks,
        "warns": warns,
        "inputs": {
            "dep_report": args.dep_report,
            "wave_report": args.wave_report,
            "drill_report": args.drill_report,
            "weekly_report": args.weekly_report,
            "bundle_report": args.bundle_report,
            "drift_report": args.drift_report,
        },
    }

    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "GATE_RESULT": result,
            "SUMMARY": summary,
            "BLOCK_ITEMS": "\n".join(f"- {x}" for x in blocks) if blocks else "- 无阻断项",
            "WARN_ITEMS": "\n".join(f"- {x}" for x in warns) if warns else "- 无告警项",
            "EVIDENCE_ITEMS": "\n".join(
                [
                    f"- dependency: `{args.dep_report}`",
                    f"- wave: `{args.wave_report}`",
                    f"- drill: `{args.drill_report}`",
                    f"- weekly: `{args.weekly_report}`",
                    f"- bundle: `{args.bundle_report}`",
                    f"- drift: `{args.drift_report}`",
                ]
            ),
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase10-gate] result={result} json={out_json} markdown={out_md}")
    return 1 if result == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
