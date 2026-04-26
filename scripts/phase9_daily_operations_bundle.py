#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "templates" / "Phase9_每日巡检批任务报告模板.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def render(template: str, mapping: dict[str, str]) -> str:
    out = template
    for key, val in mapping.items():
        out = out.replace("{{" + key + "}}", val)
    return out


def run_task(title: str, cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "title": title,
        "command": cmd,
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-6:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-6:]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 9 daily operations bundle runner.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="ops-manager")
    parser.add_argument("--v1-base", default="http://127.0.0.1:18789")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790")
    parser.add_argument("--output-json", default="docs/reports/phase9_daily_ops_bundle_latest.json")
    parser.add_argument("--output-markdown", default="docs/reports/phase9_daily_ops_bundle_latest.md")
    args = parser.parse_args()

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE_PATH}")

    tasks = [
        (
            "ops_metrics_dashboard",
            [
                sys.executable,
                "scripts/phase8_ops_metrics_dashboard.py",
                "--version",
                args.version,
                "--owner",
                args.owner,
                "--skip-live-probes",
            ],
        ),
        (
            "oncall_handbook",
            [
                sys.executable,
                "scripts/phase8_generate_oncall_handbook.py",
                "--version",
                args.version,
                "--owner",
                args.owner,
            ],
        ),
        (
            "wave_rollout_backpressure",
            [
                sys.executable,
                "scripts/phase8_wave_rollout_backpressure.py",
                "--version",
                args.version,
                "--owner",
                args.owner,
            ],
        ),
        (
            "fault_drill_scoring",
            [
                sys.executable,
                "scripts/phase8_fault_drill_scoring.py",
                "--version",
                args.version,
                "--owner",
                args.owner,
            ],
        ),
        (
            "release_cadence_arbitration",
            [
                sys.executable,
                "scripts/phase8_release_cadence_arbitration.py",
                "--owner",
                args.owner,
            ],
        ),
    ]

    results = [run_task(title, cmd) for title, cmd in tasks]
    failed = [item for item in results if not item["ok"]]
    result = "PASS" if not failed else "ATTENTION"
    summary = f"total={len(results)} failed={len(failed)}"

    report = {
        "timestamp": utc_now_iso(),
        "inputs": {
            "version": args.version,
            "owner": args.owner,
            "v1_base": args.v1_base,
            "v2_base": args.v2_base,
        },
        "summary": {
            "result": result,
            "total": len(results),
            "failed": len(failed),
        },
        "tasks": results,
    }

    rows = []
    for item in results:
        tail = item["stdout_tail"].replace("|", "/").replace("\n", " ")
        rows.append(f"| {item['title']} | {item['exit_code']} | {'ok' if item['ok'] else 'attention'} | {tail} |")

    actions = ["- 继续保持每日巡检节奏。"]
    if failed:
        actions = [
            f"- 存在 {len(failed)} 个任务返回非 0，需按优先级处理。",
            "- 优先处理 oncall/wave/fault scoring 的阻断项。",
            "- 修复后重跑本批任务并更新归档。",
        ]

    report_md = render(
        TEMPLATE_PATH.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "VERSION": args.version,
            "OWNER": args.owner,
            "RESULT": result,
            "SUMMARY": summary,
            "TASK_TABLE": "\n".join(rows),
            "ACTION_ITEMS": "\n".join(actions),
        },
    )

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(report_md, encoding="utf-8")

    print(f"[phase9-daily-bundle] result={result} failed={len(failed)} json={out_json} markdown={out_md}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
