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


def load_json(path: str) -> dict[str, Any]:
    p = ROOT / path
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def run(title: str, cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "title": title,
        "command": cmd,
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-8:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-8:]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 10 DR scenario replay runner.")
    parser.add_argument("--scenario", default="docs/templates/Phase10_DR演练场景模板.json")
    parser.add_argument("--output-json", default="docs/reports/phase10_dr_replay_latest.json")
    args = parser.parse_args()

    scenario = load_json(args.scenario)
    scenario_id = str(scenario.get("scenario_id", "DR-UNKNOWN"))

    tasks = [
        run("rollback_drill", [sys.executable, "scripts/phase7_rollback_drill.py"]),
        run("wave_backpressure", [sys.executable, "scripts/phase8_wave_rollout_backpressure.py"]),
        run("quality_gate", [sys.executable, "scripts/phase10_quality_gate.py"]),
    ]

    rollback = load_json("docs/reports/phase7_rollback_drill_latest.json")
    wave = load_json("docs/reports/phase8_wave_rollout_backpressure_latest.json")
    gate = load_json("docs/reports/phase10_quality_gate_latest.json")

    checks = {
        "rollback_ready": bool(rollback.get("rollback_ready")),
        "wave_decision": str(wave.get("decision", "UNKNOWN")),
        "quality_gate": str(gate.get("result", "UNKNOWN")),
    }
    passed = checks["rollback_ready"] and checks["wave_decision"] != "PROCEED" and checks["quality_gate"] != "PASS"
    out = {
        "timestamp": datetime.now().isoformat(),
        "scenario_id": scenario_id,
        "tasks": tasks,
        "checks": checks,
        "passed": passed,
    }

    out_json = ROOT / args.output_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[phase10-dr-replay] scenario={scenario_id} passed={passed} json={out_json}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
