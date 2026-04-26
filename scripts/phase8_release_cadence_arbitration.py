#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEMO_TEMPLATE = ROOT / "docs" / "templates" / "Phase8_跨团队发布协调纪要模板.md"


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


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


def overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)


def sanitize_item(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    out.pop("_start", None)
    out.pop("_end", None)
    out.pop("_invalid", None)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 8 cross-team release cadence arbitration.")
    parser.add_argument("--owner", default="release-manager")
    parser.add_argument("--policy", default="docs/phase8_team_release_policy.json")
    parser.add_argument("--requests", default="docs/templates/Phase8_跨团队发布申请模板.json")
    parser.add_argument("--oncall-report", default="docs/reports/phase8_oncall_handbook_latest.json")
    parser.add_argument("--output-json", default="docs/reports/phase8_release_cadence_arbitration_latest.json")
    parser.add_argument("--output-memo", default="docs/reports/phase8_release_cadence_arbitration_latest.md")
    args = parser.parse_args()

    if not MEMO_TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {MEMO_TEMPLATE}")

    policy = load_json(args.policy)
    req_data = load_json(args.requests)
    oncall = load_json(args.oncall_report)
    oncall_level = str(oncall.get("current_level", "P3"))

    priority = policy.get("priority_order") or []
    risk_levels = policy.get("risk_levels") or {"high": 3, "medium": 2, "low": 1}
    max_parallel_high = int(policy.get("max_parallel_high_risk", 1))
    requests = req_data.get("requests") if isinstance(req_data.get("requests"), list) else []
    window_id = str(req_data.get("window_id", "unknown-window"))

    parsed = []
    for item in requests:
        try:
            parsed.append(
                {
                    **item,
                    "_start": parse_ts(str(item.get("start"))),
                    "_end": parse_ts(str(item.get("end"))),
                }
            )
        except Exception:  # noqa: BLE001
            parsed.append({**item, "_invalid": True})

    # Sort by team priority then risk desc then start time.
    def sort_key(item: dict[str, Any]) -> tuple[int, int, datetime]:
        team = str(item.get("team", ""))
        risk = str(item.get("risk", "low")).lower()
        p_idx = priority.index(team) if team in priority else len(priority)
        risk_rank = -int(risk_levels.get(risk, 1))
        start = item.get("_start") if isinstance(item.get("_start"), datetime) else datetime.max
        return (p_idx, risk_rank, start)

    parsed.sort(key=sort_key)
    approved: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    conflicts: list[str] = []

    for item in parsed:
        if item.get("_invalid"):
            item["decision"] = "defer"
            item["note"] = "时间格式无效"
            rejected.append(item)
            conflicts.append(f"{item.get('change_id')} 时间格式无效")
            continue

        start = item["_start"]
        end = item["_end"]
        risk = str(item.get("risk", "low")).lower()

        # On-call pressure gate.
        if oncall_level in {"P1", "P2"} and risk in {"high", "medium"}:
            item["decision"] = "defer"
            item["note"] = f"oncall={oncall_level}，中高风险发布需延期"
            rejected.append(item)
            conflicts.append(f"{item.get('change_id')} 与 on-call 级别冲突")
            continue

        # Parallel high-risk gate.
        if risk == "high":
            high_parallel = 0
            for keep in approved:
                if str(keep.get("risk", "")).lower() == "high" and overlap(start, end, keep["_start"], keep["_end"]):
                    high_parallel += 1
            if high_parallel >= max_parallel_high:
                item["decision"] = "defer"
                item["note"] = "高风险并行发布超出上限"
                rejected.append(item)
                conflicts.append(f"{item.get('change_id')} 高风险并行冲突")
                continue

        # Time window overlap gate: keep higher priority already approved.
        blocked = None
        for keep in approved:
            if overlap(start, end, keep["_start"], keep["_end"]):
                blocked = keep
                break
        if blocked:
            item["decision"] = "defer"
            item["note"] = f"与 {blocked.get('change_id')} 时间窗冲突"
            rejected.append(item)
            conflicts.append(f"{item.get('change_id')} 与 {blocked.get('change_id')} 时间冲突")
            continue

        item["decision"] = "approve"
        item["note"] = "可进入当前窗口"
        approved.append(item)

    if oncall_level == "P1":
        decision = "HOLD_ALL"
    elif len(approved) == 0 and len(rejected) > 0:
        decision = "REPLAN_REQUIRED"
    elif len(rejected) > 0:
        decision = "PARTIAL_APPROVED"
    else:
        decision = "APPROVED"

    summary = (
        f"window={window_id}, oncall={oncall_level}, approved={len(approved)}, "
        f"deferred={len(rejected)}, decision={decision}."
    )

    actions: list[str] = []
    if decision in {"HOLD_ALL", "REPLAN_REQUIRED"}:
        actions.append("组织跨团队重排期会议，重新提交申请窗口。")
    if rejected:
        actions.append("对延期项生成 follow-up 计划并更新 owner。")
    if not actions:
        actions.append("按当前窗口推进，并在发布后复盘节奏命中率。")

    result_rows = approved + rejected
    table_rows = []
    for item in result_rows:
        start = item.get("start", "-")
        end = item.get("end", "-")
        table_rows.append(
            f"| {item.get('team', '-')} | {item.get('change_id', '-')} | {item.get('risk', '-')} | "
            f"{start} ~ {end} | {item.get('decision', '-')} | {item.get('note', '-')} |"
        )

    memo_text = render(
        MEMO_TEMPLATE.read_text(encoding="utf-8"),
        {
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "WINDOW_ID": window_id,
            "OWNER": args.owner,
            "DECISION": decision,
            "SUMMARY": summary,
            "REQUEST_TABLE": "\n".join(table_rows) if table_rows else "| - | - | - | - | - | - |",
            "CONFLICT_ITEMS": "\n".join(f"- {c}" for c in conflicts) if conflicts else "- 无冲突",
            "ACTION_ITEMS": "\n".join(f"- {a}" for a in actions),
        },
    )

    output = {
        "timestamp": datetime.now().isoformat(),
        "window_id": window_id,
        "decision": decision,
        "summary": summary,
        "oncall_level": oncall_level,
        "approved": [sanitize_item(item) for item in approved],
        "deferred": [sanitize_item(item) for item in rejected],
        "conflicts": conflicts,
        "actions": actions,
        "inputs": {
            "policy": args.policy,
            "requests": args.requests,
            "oncall_report": args.oncall_report,
        },
    }

    output_json = ROOT / args.output_json
    output_memo = ROOT / args.output_memo
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_memo.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    output_memo.write_text(memo_text, encoding="utf-8")

    print(f"[phase8-cadence-arb] decision={decision} json={output_json} memo={output_memo}")
    return 1 if decision in {"HOLD_ALL", "REPLAN_REQUIRED"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
