#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "templates" / "Phase7_每日演练检查项模板.md"


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def render(template_text: str, mapping: dict[str, str]) -> str:
    output = template_text
    for key, val in mapping.items():
        output = output.replace("{{" + key + "}}", val)
    return output


def weekday_cn(date_obj: datetime) -> str:
    names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return names[date_obj.weekday()]


def build_day_focus(index: int) -> str:
    # 7-day pre-cutover cadence:
    # D-7 baseline, D-6 library canary, D-5 pipeline canary, D-4 approval/task drill,
    # D-3 rollback drill, D-2 observability guard, D-1 final readiness.
    focus_map = {
        0: "D-7：基线与环境连通性检查",
        1: "D-6：资料库链路灰度演练",
        2: "D-5：标准流水线灰度演练",
        3: "D-4：审批/任务联动演练",
        4: "D-3：回退演练与通知链路演练",
        5: "D-2：观测守护阈值检查与告警演练",
        6: "D-1：正式切换前总彩排与签核",
    }
    return focus_map.get(index, "日常演练")


def build_commands(index: int) -> list[str]:
    common = [
        "python scripts/phase7_cutover_readiness.py",
        "python scripts/phase7_observability_guard.py",
    ]
    if index == 0:
        return common + ["python scripts/v1_v2_baseline_regression.py"]
    if index == 1:
        return common + ["python scripts/phase7_canary_rollout_drill.py --stage library"]
    if index == 2:
        return common + ["python scripts/phase7_canary_rollout_drill.py --stage pipeline"]
    if index == 3:
        return common + ["python scripts/phase7_pre_cutover_drill.py"]
    if index == 4:
        return common + ["python scripts/phase7_rollback_drill.py"]
    if index == 5:
        return common + ["python scripts/phase7_observability_guard.py --timeout 8"]
    return common + [
        "python scripts/phase7_canary_rollout_drill.py --stage all",
        "python scripts/phase7_generate_decision_pack.py --version v2-cutover-final --owner release-manager",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Phase7 one-week pre-cutover daily drill checklist.")
    parser.add_argument("--start-date", required=True, help="Start date (D-7), format YYYY-MM-DD")
    parser.add_argument("--version", default="v2-cutover", help="Cutover version label")
    parser.add_argument("--owner", default="release-manager", help="Checklist owner")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "docs" / "reports" / "weekly-drill"),
        help="Output directory for generated daily checklists",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan only, do not write files")
    args = parser.parse_args()

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    start = parse_date(args.start_date)
    out_dir = Path(args.output_dir)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    summary_lines: list[str] = [
        f"# Phase7 一周演练计划（{args.version}）",
        "",
        f"- 起始日期（D-7）：{args.start_date}",
        f"- 负责人：{args.owner}",
        "",
        "## 每日计划",
    ]

    for i in range(7):
        current = start + timedelta(days=i)
        date_text = current.strftime("%Y-%m-%d")
        tag = f"D-{7 - i}" if i < 6 else "D-1"
        focus = build_day_focus(i)
        commands = build_commands(i)
        command_block = "\n".join(f"- `{cmd}`" for cmd in commands)
        filename = f"{date_text}_{tag}_每日演练检查项.md"
        content = render(
            template,
            {
                "DATE": date_text,
                "WEEKDAY": weekday_cn(current),
                "VERSION": args.version,
                "OWNER": args.owner,
                "DAY_TAG": tag,
                "DAY_FOCUS": focus,
                "COMMANDS": command_block,
            },
        )
        target = out_dir / filename
        if not args.dry_run:
            target.write_text(content, encoding="utf-8")
            generated.append(target)
        summary_lines.append(f"- {date_text}（{tag}）：{focus}")

    summary_lines.extend(
        [
            "",
            "## 使用说明",
            "- 每天执行对应命令并更新当天检查项模板。",
            "- 若出现 critical 告警，立即转入回退演练与决策流程。",
        ]
    )
    summary_path = out_dir / f"{args.start_date}_weekly_drill_summary.md"
    if not args.dry_run:
        summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
        generated.append(summary_path)

    print("[phase7-weekly-drill] plan:")
    print("\n".join(summary_lines))
    if args.dry_run:
        print("[phase7-weekly-drill] dry-run mode, no files written")
    else:
        print("[phase7-weekly-drill] generated files:")
        for path in generated:
            print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
