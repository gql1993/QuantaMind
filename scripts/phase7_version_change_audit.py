#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_TEMPLATE = ROOT / "docs" / "templates" / "Phase7_版本级变更审计模板.md"
TRACE_TEMPLATE = ROOT / "docs" / "templates" / "Phase7_版本责任追踪模板.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def render(template: str, mapping: dict[str, str]) -> str:
    output = template
    for key, val in mapping.items():
        output = output.replace("{{" + key + "}}", val)
    return output


def scan_postmortem_count(directory: Path, start: datetime, end: datetime) -> int:
    if not directory.exists():
        return 0
    count = 0
    for md in directory.glob("*.md"):
        name = md.name
        if len(name) < 8 or not name[:8].isdigit():
            continue
        try:
            d = datetime.strptime(name[:8], "%Y%m%d")
        except Exception:  # noqa: BLE001
            continue
        if start.date() <= d.date() <= end.date():
            count += 1
    return count


def collect_change_items(quarterly: dict[str, Any]) -> list[dict[str, str]]:
    actions = ((quarterly.get("assessment") or {}).get("actions") or []) if quarterly else []
    items: list[dict[str, str]] = []
    for idx, action in enumerate(actions, start=1):
        items.append(
            {
                "id": f"CHG-{idx:03d}",
                "title": str(action),
                "scope": "V2 控制平面",
                "risk": "M",
                "status": "待跟踪",
            }
        )
    if not items:
        items.append(
            {
                "id": "CHG-001",
                "title": "补充本版本核心变更项",
                "scope": "待补充",
                "risk": "M",
                "status": "待补充",
            }
        )
    return items


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    window_end = now
    window_start = now - timedelta(days=args.window_days)

    quarterly = load_json(ROOT / args.quarterly_report)
    biweekly = load_json(ROOT / args.biweekly_report)
    guard = load_json(ROOT / args.guard_report)
    postmortem_count = scan_postmortem_count(ROOT / args.postmortem_dir, window_start, window_end)

    quarterly_result = str((quarterly.get("assessment") or {}).get("audit_result", "UNKNOWN"))
    biweekly_level = str((biweekly.get("assessment") or {}).get("stability_level", "UNKNOWN"))
    guard_decision = str((guard.get("summary") or {}).get("decision", "unknown"))

    risks: list[str] = []
    trace_actions: list[str] = []

    if quarterly_result == "FAIL" or guard_decision == "rollback_now":
        decision = "BLOCK"
        risks.append("存在回退级风险或季度审计失败，不满足版本发布条件。")
        trace_actions.append("冻结本版本推进，完成关键问题清零并复审。")
    elif quarterly_result == "CONDITIONAL_PASS" or biweekly_level == "YELLOW":
        decision = "REVIEW_REQUIRED"
        risks.append("当前存在条件通过项，需要责任人限期闭环。")
        trace_actions.append("针对条件通过项建立责任追踪并在 SLA 内完成复测。")
    else:
        decision = "APPROVE_CANDIDATE"
        trace_actions.append("维持当前变更节奏并持续执行观测。")

    if postmortem_count == 0:
        risks.append("窗口内缺少复盘材料，证据链完整性不足。")
        trace_actions.append("补齐复盘材料并关联到版本审计记录。")

    if not risks:
        risks.append("未发现阻塞发布的高风险问题。")

    summary = (
        f"quarterly={quarterly_result}, biweekly={biweekly_level}, guard={guard_decision}, "
        f"postmortem_count={postmortem_count}, decision={decision}."
    )

    return {
        "timestamp": utc_now_iso(),
        "window": {
            "days": args.window_days,
            "start": window_start.isoformat().replace("+00:00", "Z"),
            "end": window_end.isoformat().replace("+00:00", "Z"),
        },
        "version_id": args.version_id,
        "inputs": {
            "quarterly_report": args.quarterly_report,
            "biweekly_report": args.biweekly_report,
            "guard_report": args.guard_report,
            "postmortem_dir": args.postmortem_dir,
        },
        "metrics": {
            "quarterly_result": quarterly_result,
            "biweekly_level": biweekly_level,
            "guard_decision": guard_decision,
            "postmortem_count": postmortem_count,
        },
        "assessment": {
            "decision": decision,
            "summary": summary,
            "risks": risks,
            "trace_actions": trace_actions,
        },
        "change_items": collect_change_items(quarterly),
    }


def to_audit_markdown(report: dict[str, Any], template: str, owner: str) -> str:
    changes = report.get("change_items") or []
    change_rows = "\n".join(
        f"| {item['id']} | {item['title']} | {item['scope']} | {item['risk']} | {item['status']} |" for item in changes
    )
    evidence = report.get("inputs") or {}
    evidence_items = [
        f"- quarterly report: `{evidence.get('quarterly_report')}`",
        f"- biweekly report: `{evidence.get('biweekly_report')}`",
        f"- observability guard: `{evidence.get('guard_report')}`",
        f"- postmortem dir: `{evidence.get('postmortem_dir')}`",
    ]
    window = report.get("window") or {}
    start = parse_iso(window.get("start"))
    end = parse_iso(window.get("end"))
    window_text = (
        f"{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}（{window.get('days')} 天）"
        if start and end
        else f"{window.get('days', '-') } 天"
    )
    mapping = {
        "DATE": datetime.now().strftime("%Y-%m-%d"),
        "VERSION_ID": str(report.get("version_id", "-")),
        "OWNER": owner,
        "WINDOW": window_text,
        "AUDIT_DECISION": str((report.get("assessment") or {}).get("decision", "UNKNOWN")),
        "EXEC_SUMMARY": str((report.get("assessment") or {}).get("summary", "")),
        "CHANGE_ITEMS": change_rows,
        "EVIDENCE_ITEMS": "\n".join(evidence_items),
    }
    return render(template, mapping)


def to_trace_markdown(report: dict[str, Any], template: str, roles: dict[str, str]) -> str:
    responsibility_rows = "\n".join(
        [
            f"| 发布负责人 | {roles['release']} | 变更窗口控制、发布决策 | 待确认 |",
            f"| 技术负责人 | {roles['tech']} | 技术风险评估、修复推进 | 待确认 |",
            f"| 测试负责人 | {roles['qa']} | 回归验证、质量门禁 | 待确认 |",
            f"| 运维负责人 | {roles['ops']} | 观测告警、回退保障 | 待确认 |",
        ]
    )
    actions = ((report.get("assessment") or {}).get("trace_actions") or []) + ((report.get("assessment") or {}).get("risks") or [])
    trace_rows = []
    for idx, action in enumerate(actions, start=1):
        trace_rows.append(
            f"| TRC-{idx:03d} | AUD-{idx:03d} | {action} | {roles['release']} | [YYYY-MM-DD] | 待开始 |"
        )
    if not trace_rows:
        trace_rows.append("| TRC-001 | AUD-001 | 待补充版本追踪动作 | release-manager | [YYYY-MM-DD] | 待开始 |")
    mapping = {
        "DATE": datetime.now().strftime("%Y-%m-%d"),
        "VERSION_ID": str(report.get("version_id", "-")),
        "RESPONSIBILITY_TABLE": responsibility_rows,
        "TRACE_ITEMS": "\n".join(trace_rows),
    }
    return render(template, mapping)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 version-level change audit and accountability tracking.")
    parser.add_argument("--version-id", default="v2-cutover-r1", help="Version ID to audit")
    parser.add_argument("--owner", default="release-manager", help="Audit owner")
    parser.add_argument("--window-days", type=int, default=30, help="Observation window in days")
    parser.add_argument("--quarterly-report", default="docs/reports/phase7_quarterly_regression_audit_latest.json")
    parser.add_argument("--biweekly-report", default="docs/reports/phase7_biweekly_stability_review_latest.json")
    parser.add_argument("--guard-report", default="docs/reports/phase7_observability_guard_latest.json")
    parser.add_argument("--postmortem-dir", default="docs/reports/postmortem-pack")
    parser.add_argument("--release-owner", default="release-manager")
    parser.add_argument("--tech-owner", default="tech-lead")
    parser.add_argument("--qa-owner", default="qa-lead")
    parser.add_argument("--ops-owner", default="ops-lead")
    parser.add_argument("--output-json", default="docs/reports/phase7_version_change_audit_latest.json")
    parser.add_argument("--output-audit", default="docs/reports/phase7_version_change_audit_latest.md")
    parser.add_argument("--output-trace", default="docs/reports/phase7_version_accountability_trace_latest.md")
    args = parser.parse_args()

    if not AUDIT_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {AUDIT_TEMPLATE}")
    if not TRACE_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TRACE_TEMPLATE}")

    report = evaluate(args)
    audit_md = to_audit_markdown(report, AUDIT_TEMPLATE.read_text(encoding="utf-8"), owner=args.owner)
    trace_md = to_trace_markdown(
        report,
        TRACE_TEMPLATE.read_text(encoding="utf-8"),
        roles={
            "release": args.release_owner,
            "tech": args.tech_owner,
            "qa": args.qa_owner,
            "ops": args.ops_owner,
        },
    )

    output_json = ROOT / args.output_json
    output_audit = ROOT / args.output_audit
    output_trace = ROOT / args.output_trace
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_audit.parent.mkdir(parents=True, exist_ok=True)
    output_trace.parent.mkdir(parents=True, exist_ok=True)

    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output_audit.write_text(audit_md, encoding="utf-8")
    output_trace.write_text(trace_md, encoding="utf-8")

    decision = str((report.get("assessment") or {}).get("decision", "UNKNOWN"))
    print(f"[phase7-version-audit] decision={decision} json={output_json} audit={output_audit} trace={output_trace}")
    return 1 if decision == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
