# Phase 8-4 多环境发布波次与容量回压机制固化

更新日期：2026-04-10

## 1. 目标

将发布推进策略从“人工判断”固化为“波次门禁 + 容量回压”机制：

- 多环境波次计划（staging -> canary -> 小流量 -> 中流量 -> 全量）
- 基于 on-call 级别与容量压力的自动决策（`PROCEED / HOLD / ROLLBACK`）
- 输出执行计划与执行记录模板

## 2. 资产清单

- 机制文档：`docs/Phase8_多环境发布波次与容量回压机制.md`
- 策略文件：`docs/phase8_rollout_backpressure_policy.json`
- 模板：
  - `docs/templates/Phase8_发布波次与回压计划模板.md`
  - `docs/templates/Phase8_发布波次执行记录模板.md`
- 执行脚本：`scripts/phase8_wave_rollout_backpressure.py`
- 默认输出：
  - `docs/reports/phase8_wave_rollout_backpressure_latest.json`
  - `docs/reports/phase8_wave_rollout_backpressure_latest.md`
  - `docs/reports/phase8_wave_rollout_execution_latest.md`

## 3. 输入来源（默认）

- 运行看板：`docs/reports/phase8_ops_metrics_dashboard_latest.json`
- on-call 手册：`docs/reports/phase8_oncall_handbook_latest.json`

## 4. 执行方式

```bash
python scripts/phase8_wave_rollout_backpressure.py --version v2-prod-r1 --owner release-manager
```

## 5. 决策规则

- `ROLLBACK`：on-call 为 `P1` 或 ops 总体 `RED`
- `HOLD`：on-call 为 `P2` 或 ops 总体 `YELLOW`，或波次门禁不通过
- `PROCEED`：门禁通过且当前态势稳定

## 6. 闭环要求

1. 每个发布窗口开始前生成波次计划；
2. 波次推进时同步维护执行记录；
3. `HOLD/ROLLBACK` 结论必须关联 on-call 与复盘证据。
