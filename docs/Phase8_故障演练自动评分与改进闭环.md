# Phase 8-5 故障演练自动评分与改进闭环固化

更新日期：2026-04-10

## 1. 目标

把故障演练结果固化为可比较、可追踪的评分体系，并直接产出改进行动台账。

## 2. 资产清单

- 机制文档：`docs/Phase8_故障演练自动评分与改进闭环.md`
- 策略文件：`docs/phase8_drill_scoring_policy.json`
- 模板：
  - `docs/templates/Phase8_故障演练评分报告模板.md`
  - `docs/templates/Phase8_改进行动闭环台账模板.md`
- 执行脚本：`scripts/phase8_fault_drill_scoring.py`
- 默认输出：
  - `docs/reports/phase8_fault_drill_scoring_latest.json`
  - `docs/reports/phase8_fault_drill_scoring_latest.md`
  - `docs/reports/phase8_fault_drill_improvement_ledger_latest.md`

## 3. 输入来源（默认）

- `docs/reports/phase7_pre_cutover_drill_latest.json`
- `docs/reports/phase7_canary_rollout_latest.json`
- `docs/reports/phase7_rollback_drill_latest.json`
- `docs/reports/phase8_oncall_handbook_latest.json`
- `docs/reports/phase8_ops_metrics_dashboard_latest.json`

## 4. 执行方式

```bash
python scripts/phase8_fault_drill_scoring.py --version v2-prod-r1 --owner drill-manager
```

## 5. 输出规则

- 总分 0~100，等级 `A/B/C/D`
- `D` 视为阻断结果，需要立即进入改进闭环
- 台账自动按优先级生成行动项与建议截止日期

## 6. 闭环要求

1. 每次故障演练后必须生成评分报告；
2. 对 `C/D` 结果必须在 SLA 内完成改进并复测；
3. 下次评分需验证上一轮行动项关闭情况。
