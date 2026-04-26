# Phase 7：正式切换窗口与值班预案

更新日期：2026-04-09

## 1. 目的

将切换执行从“临时协调”固化为标准 runbook，确保：

- 切换动作有时间窗与负责人
- 值班交接有统一模板
- 回退触发可快速执行

## 2. 固化资产

- 方案模板：
  - `docs/templates/Phase7_正式切换窗口与值班预案模板.md`
- 生成脚本：
  - `scripts/phase7_generate_cutover_plan.py`
- 生成结果默认目录：
  - `docs/reports/cutover-plan/`

## 3. 生成方式

```bash
python scripts/phase7_generate_cutover_plan.py \
  --date 2026-04-10 \
  --version v2-cutover-r1 \
  --window-start 20:00 \
  --window-end 23:00 \
  --commander release-manager \
  --dev-oncall dev-oncall \
  --qa-oncall qa-oncall \
  --ops-oncall ops-oncall
```

## 4. 执行前置

建议在窗口开始前 30 分钟依次执行：

1. `phase7_cutover_readiness.py`
2. `phase7_canary_rollout_drill.py`
3. `phase7_observability_guard.py`

若任一关键检查失败，进入回退或延期流程。

## 5. 关联文档

- `docs/Phase7_切换评估与回退演练清单.md`
- `docs/Phase7_观测指标与回退触发条件.md`
- `docs/Phase7_切换评审材料模板.md`
