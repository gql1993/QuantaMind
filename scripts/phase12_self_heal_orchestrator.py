#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "Phase12_自愈闭环执行报告模板.md"


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


def exec_action(action: str, version: str, owner: str, mode: str) -> dict[str, str]:
    if mode == "recommend":
        return {"action": action, "status": "planned", "note": "recommend mode"}

    if action == "trigger_rollback_drill":
        proc = subprocess.run([sys.executable, "scripts/phase7_rollback_drill.py"], cwd=ROOT, capture_output=True, text=True, check=False)
        return {"action": action, "status": "ok" if proc.returncode == 0 else "failed", "note": "rollback drill executed"}
    if action == "regenerate_oncall_handbook":
        proc = subprocess.run(
            [sys.executable, "scripts/phase8_generate_oncall_handbook.py", "--version", version, "--owner", owner],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return {"action": action, "status": "ok" if proc.returncode == 0 else "failed", "note": "oncall handbook refreshed"}
    if action == "regenerate_ops_dashboard":
        proc = subprocess.run(
            [sys.executable, "scripts/phase8_ops_metrics_dashboard.py", "--version", version, "--owner", owner, "--skip-live-probes"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return {"action": action, "status": "ok" if proc.returncode == 0 else "failed", "note": "ops dashboard refreshed"}
    if action == "hold_wave_rollout":
        return {"action": action, "status": "ok", "note": "rollout held by policy"}
    if action == "open_improvement_ledger":
        return {"action": action, "status": "ok", "note": "use phase8 fault improvement ledger"}
    if action == "freeze_release_window":
        return {"action": action, "status": "ok", "note": "release freeze suggested"}
    return {"action": action, "status": "skipped", "note": "unknown action"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 12 self-heal orchestrator.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="ops-manager")
    parser.add_argument("--policy", default="docs/phase12_self_heal_policy.json")
    parser.add_argument("--oncall-report", default="docs/reports/phase8_oncall_handbook_latest.json")
    parser.add_argument("--mode", choices=["recommend", "execute"], default="recommend")
    parser.add_argument("--output-json", default="docs/reports/phase12_self_heal_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase12_self_heal_latest.md")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")

    policy = load_json(args.policy)
    oncall = load_json(args.oncall_report)
    level = str(oncall.get("current_level", "P3"))
    actions = ((policy.get("actions") or {}).get(level)) or ["monitor_only"]
    executed = [exec_action(action, args.version, args.owner, args.mode) for action in actions]

    summary = f"level={level}, mode={args.mode}, actions={len(executed)}."
    out = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "mode": args.mode,
        "actions": executed,
        "summary": summary,
    }

    table = "\n".join(f"| {x['action']} | {x['status']} | {x['note']} |" for x in executed)
    md = render(
        TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "MODE": args.mode,
            "LEVEL": level,
            "ACTION_COUNT": str(len(executed)),
            "SUMMARY": summary,
            "ACTION_TABLE": table if table else "| - | - | - |",
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(f"[phase12-self-heal] level={level} mode={args.mode} actions={len(executed)} json={out_json} markdown={out_md}")
    return 1 if level == "P1" else 0


if __name__ == "__main__":
    raise SystemExit(main())
