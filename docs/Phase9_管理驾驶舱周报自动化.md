# Phase 9-2 管理驾驶舱周报自动化

更新日期：2026-04-10

## 1. 目标

自动汇总运营核心状态，形成管理层可直接阅读的周报与行动建议。

## 2. 资产清单

- 机制文档：`docs/Phase9_管理驾驶舱周报自动化.md`
- 策略文件：`docs/phase9_executive_weekly_policy.json`
- 模板：`docs/templates/Phase9_管理驾驶舱周报模板.md`
- 执行脚本：`scripts/phase9_generate_executive_weekly_report.py`
- 默认输出：
  - `docs/reports/phase9_executive_weekly_latest.json`
  - `docs/reports/phase9_executive_weekly_latest.md`

## 3. 汇总输入（默认）

- `phase8_ops_metrics_dashboard_latest.json`
- `phase8_oncall_handbook_latest.json`
- `phase8_wave_rollout_backpressure_latest.json`
- `phase8_fault_drill_scoring_latest.json`
- `phase9_daily_ops_bundle_latest.json`

## 4. 执行方式

```bash
python scripts/phase9_generate_executive_weekly_report.py --version v2-prod-r1 --owner release-manager
```

## 5. 输出规则

- 评分：0~100
- 等级：`A/B/C/D`
- 结果为 `D` 时视为管理层关注事项，需补充专项改进计划。
