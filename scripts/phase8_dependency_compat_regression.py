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
REPORT_TEMPLATE = ROOT / "docs" / "templates" / "Phase8_兼容性回归报告模板.md"
SIGNOFF_TEMPLATE = ROOT / "docs" / "templates" / "Phase8_兼容性签核记录模板.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: str) -> dict[str, Any]:
    p = ROOT / path
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def render(template: str, mapping: dict[str, str]) -> str:
    out = template
    for key, val in mapping.items():
        out = out.replace("{{" + key + "}}", val)
    return out


def run_check(cmd: list[str], *, title: str) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "title": title,
        "command": cmd,
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-12:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-12:]),
    }


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    change_set = load_json(args.change_set)
    changes = change_set.get("changes") if isinstance(change_set.get("changes"), list) else []
    if not changes:
        changes = [
            {
                "id": "DEP-000",
                "name": "placeholder",
                "from": "-",
                "to": "-",
                "risk": "medium",
                "reason": "待补充依赖变更",
                "compatibility_focus": "待补充",
            }
        ]

    checks: list[dict[str, Any]] = []
    checks.append(
        run_check(
            [sys.executable, "-m", "pytest", "tests/v2", "-q"],
            title="pytest_v2_regression",
        )
    )
    checks.append(
        run_check(
            [
                sys.executable,
                "scripts/v1_v2_baseline_regression.py",
                "--v1-base",
                args.v1_base,
                "--v2-base",
                args.v2_base,
            ],
            title="baseline_v1_v2",
        )
    )
    checks.append(
        run_check(
            [
                sys.executable,
                "scripts/phase8_ops_metrics_dashboard.py",
                "--version",
                args.version,
                "--owner",
                args.owner,
                "--skip-live-probes",
            ],
            title="ops_metrics_dashboard_offline",
        )
    )

    passed = sum(1 for c in checks if c.get("ok"))
    total = len(checks)
    failed = total - passed

    high_risk_count = sum(1 for item in changes if str(item.get("risk", "")).lower() == "high")
    if failed > 0 and high_risk_count > 0:
        compat_result = "BLOCK"
    elif failed > 0:
        compat_result = "CONDITIONAL_PASS"
    else:
        compat_result = "PASS"

    risks: list[str] = []
    actions: list[str] = []
    if failed > 0:
        risks.append(f"存在失败检查项（{failed}/{total}）。")
        actions.append("优先修复失败项并重跑兼容性回归。")
    if high_risk_count > 0:
        risks.append(f"依赖变更中包含高风险项（{high_risk_count}）。")
        actions.append("对高风险依赖执行专项回归并保留证据。")
    if compat_result == "BLOCK":
        actions.append("冻结升级发布，待回归通过后再签核。")
    if not risks:
        risks.append("未发现阻塞性兼容风险。")
    if not actions:
        actions.append("进入签核流程并归档本次报告。")

    summary = f"checks passed={passed}/{total}, high_risk={high_risk_count}, result={compat_result}."
    return {
        "timestamp": utc_now_iso(),
        "inputs": {
            "change_set": args.change_set,
            "v1_base": args.v1_base,
            "v2_base": args.v2_base,
            "version": args.version,
            "owner": args.owner,
        },
        "changes": changes,
        "checks": checks,
        "assessment": {
            "result": compat_result,
            "summary": summary,
            "risks": risks,
            "actions": actions,
        },
    }


def to_report_md(report: dict[str, Any], template: str) -> str:
    changes = report.get("changes") or []
    checks = report.get("checks") or []
    assessment = report.get("assessment") or {}
    inputs = report.get("inputs") or {}
    change_rows = "\n".join(
        f"| {item.get('id')} | {item.get('name')} | {item.get('from')} -> {item.get('to')} | "
        f"{item.get('risk')} | {item.get('reason')} | {item.get('compatibility_focus')} |"
        for item in changes
    )
    check_rows = "\n".join(
        f"| {c.get('title')} | `{' '.join(c.get('command', []))}` | {c.get('exit_code')} | {'pass' if c.get('ok') else 'fail'} |"
        for c in checks
    )
    mapping = {
        "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "VERSION": str(inputs.get("version", "-")),
        "OWNER": str(inputs.get("owner", "-")),
        "COMPAT_RESULT": str(assessment.get("result", "UNKNOWN")),
        "EXEC_SUMMARY": str(assessment.get("summary", "")),
        "CHANGE_TABLE": change_rows,
        "CHECK_TABLE": check_rows,
        "RISK_ITEMS": "\n".join(f"- {item}" for item in assessment.get("risks", [])),
        "EVIDENCE_ITEMS": "\n".join(
            [
                f"- 依赖变更清单：`{inputs.get('change_set')}`",
                "- 回归证据：检查项 stdout/stderr tail 已写入 json 报告",
            ]
        ),
    }
    return render(template, mapping)


def to_signoff_md(template: str, *, version: str, report_path: str) -> str:
    return render(
        template,
        {
            "DATE": datetime.now().strftime("%Y-%m-%d"),
            "VERSION": version,
            "REPORT_PATH": report_path,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 8 dependency upgrade compatibility regression flow.")
    parser.add_argument("--version", default="v2-prod-r1")
    parser.add_argument("--owner", default="release-manager")
    parser.add_argument("--v1-base", default="http://127.0.0.1:18789")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790")
    parser.add_argument("--change-set", default="docs/templates/Phase8_依赖变更清单模板.json")
    parser.add_argument("--output-json", default="docs/reports/phase8_dependency_compat_latest.json")
    parser.add_argument("--output-report", default="docs/reports/phase8_dependency_compat_latest.md")
    parser.add_argument("--output-signoff", default="docs/reports/phase8_dependency_compat_signoff_latest.md")
    args = parser.parse_args()

    if not REPORT_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {REPORT_TEMPLATE}")
    if not SIGNOFF_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {SIGNOFF_TEMPLATE}")

    report = evaluate(args)
    output_json = ROOT / args.output_json
    output_report = ROOT / args.output_report
    output_signoff = ROOT / args.output_signoff
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_signoff.parent.mkdir(parents=True, exist_ok=True)

    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output_report.write_text(to_report_md(report, REPORT_TEMPLATE.read_text(encoding="utf-8")), encoding="utf-8")
    output_signoff.write_text(
        to_signoff_md(
            SIGNOFF_TEMPLATE.read_text(encoding="utf-8"),
            version=args.version,
            report_path=str(output_report).replace("\\", "/"),
        ),
        encoding="utf-8",
    )

    result = str((report.get("assessment") or {}).get("result", "UNKNOWN"))
    print(f"[phase8-dependency-compat] result={result} json={output_json} report={output_report} signoff={output_signoff}")
    return 1 if result == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
