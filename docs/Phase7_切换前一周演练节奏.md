# Phase 7：正式切换前一周演练节奏（每日检查项）

更新日期：2026-04-09

## 1. 目标

把切换前一周（D-7 ~ D-1）演练节奏固化为每日可执行检查项，避免临时协调导致漏检。

## 2. 固化资产

- 每日模板：`docs/templates/Phase7_每日演练检查项模板.md`
- 生成脚本：`scripts/phase7_generate_weekly_drill_plan.py`
- 默认生成目录：`docs/reports/weekly-drill/`

## 3. 节奏建议（D-7 -> D-1）

1. D-7：基线与环境连通性检查
2. D-6：资料库链路灰度演练
3. D-5：标准流水线灰度演练
4. D-4：审批/任务联动演练
5. D-3：回退演练与通知链路演练
6. D-2：观测守护阈值检查与告警演练
7. D-1：正式切换前总彩排与签核

## 4. 生成方式

```bash
python scripts/phase7_generate_weekly_drill_plan.py --start-date 2026-04-12 --version v2-cutover-r1 --owner release-manager
```

可先 dry-run 预览：

```bash
python scripts/phase7_generate_weekly_drill_plan.py --start-date 2026-04-12 --dry-run
```

## 5. 日常执行建议

- 每日演练结束后，必须回填当日结论与风险动作。
- 若出现 `rollback_now`，当日流程立即转入回退并暂停后续灰度计划。
- 每日检查结果作为切换评审会议输入材料的一部分。
