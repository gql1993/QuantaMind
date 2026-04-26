# Phase 9-1 全链路自动编排与每日巡检批任务固化

更新日期：2026-04-10

## 1. 目标

将 Phase 8 的核心运营脚本串联成每日可执行批任务，形成统一巡检入口。

## 2. 资产清单

- 机制文档：`docs/Phase9_全链路自动编排与每日巡检.md`
- 模板：`docs/templates/Phase9_每日巡检批任务报告模板.md`
- 执行脚本：`scripts/phase9_daily_operations_bundle.py`
- 默认输出：
  - `docs/reports/phase9_daily_ops_bundle_latest.json`
  - `docs/reports/phase9_daily_ops_bundle_latest.md`

## 3. 默认编排任务

1. `phase8_ops_metrics_dashboard.py`
2. `phase8_generate_oncall_handbook.py`
3. `phase8_wave_rollout_backpressure.py`
4. `phase8_fault_drill_scoring.py`
5. `phase8_release_cadence_arbitration.py`

## 4. 执行方式

```bash
python scripts/phase9_daily_operations_bundle.py --version v2-prod-r1 --owner ops-manager
```

## 5. 运行约定

- 每日固定窗口执行；
- 非 0 结果进入“ATTENTION”并触发人工跟进；
- 批任务报告必须纳入归档。
