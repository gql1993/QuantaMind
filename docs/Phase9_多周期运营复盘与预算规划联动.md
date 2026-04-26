# Phase 9-4 多周期运营复盘与预算规划联动机制固化

更新日期：2026-04-10

## 1. 目标

把运营复盘结果转化为下周期资源配置建议，形成“状态 -> 预算 -> 动作”的闭环。

## 2. 资产清单

- 机制文档：`docs/Phase9_多周期运营复盘与预算规划联动.md`
- 策略文件：`docs/phase9_budget_linkage_policy.json`
- 模板：`docs/templates/Phase9_多周期运营复盘与预算联动报告模板.md`
- 执行脚本：`scripts/phase9_ops_retro_budget_linkage.py`
- 默认输出：
  - `docs/reports/phase9_ops_budget_linkage_latest.json`
  - `docs/reports/phase9_ops_budget_linkage_latest.md`

## 3. 执行方式

```bash
python scripts/phase9_ops_retro_budget_linkage.py --version v2-prod-r1 --owner release-manager
```
