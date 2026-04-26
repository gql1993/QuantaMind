#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase11_异常根因聚类报告模板.md"


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


def bucket(text: str) -> str:
    s = text.lower()
    if "capacity" in s or "积压" in s or "timeout" in s:
        return "capacity_pressure"
    if "rollback" in s or "回退" in s:
        return "rollback_risk"
    if "drift" in s or "阈值" in s:
        return "policy_drift"
    if "oncall" in s or "告警" in s:
        return "alerting"
    return "other"


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 11 incident root-cause clustering.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--ops-report", default="docs/reports/phase8_ops_metrics_dashboard_latest.json")
    parser.add_argument("--oncall-report", default="docs/reports/phase8_oncall_handbook_latest.json")
    parser.add_argument("--drill-report", default="docs/reports/phase8_fault_drill_scoring_latest.json")
    parser.add_argument("--drift-report", default="docs/reports/phase9_policy_drift_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase11_rootcause_cluster_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase11_rootcause_cluster_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    ops = load_json(args.ops_report)
    oncall = load_json(args.oncall_report)
    drill = load_json(args.drill_report)
    drift = load_json(args.drift_report)

    corpus = []
    corpus.extend((ops.get("assessment") or {}).get("risks", []))
    corpus.extend(oncall.get("reasons", []))
    corpus.extend(drill.get("risks", []))
    corpus.extend(drift.get("suggestions", []))
    if not corpus:
        corpus = ["no risks collected"]

    clusters: dict[str, list[str]] = {}
    for item in corpus:
        key = bucket(str(item))
        clusters.setdefault(key, []).append(str(item))

    rows = []
    for k, items in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True):
        sample = items[0].replace("|", "/")
        rows.append((k, str(len(items)), sample))

    summary = f"clusters={len(clusters)}, samples={len(corpus)}."
    out = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "clusters": {k: v for k, v in clusters.items()},
    }

    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "CLUSTER_COUNT": str(len(clusters)),
            "SUMMARY": summary,
            "CLUSTER_TABLE": "\n".join(f"| {a} | {b} | {c} |" for a, b, c in rows),
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase11-rootcause] clusters={len(clusters)} json={out_json} markdown={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
