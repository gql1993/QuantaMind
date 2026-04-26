# Phase 9-3 策略漂移检测与阈值自适应建议机制固化

更新日期：2026-04-10

## 1. 目标

自动识别运营策略与实际运行状态的偏移，并输出阈值调优建议。

## 2. 资产清单

- 机制文档：`docs/Phase9_策略漂移检测与阈值自适应建议.md`
- 策略文件：`docs/phase9_drift_policy.json`
- 模板：`docs/templates/Phase9_策略漂移检测报告模板.md`
- 执行脚本：`scripts/phase9_policy_drift_advisor.py`
- 默认输出：
  - `docs/reports/phase9_policy_drift_latest.json`
  - `docs/reports/phase9_policy_drift_latest.md`

## 3. 执行方式

```bash
python scripts/phase9_policy_drift_advisor.py --version v2-prod-r1 --owner ops-manager
```
