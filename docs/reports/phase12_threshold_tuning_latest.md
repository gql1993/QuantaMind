# Phase 12 阈值调参提案

生成时间：2026-04-10 19:15:40  
版本范围：v2-prod-r1  
负责人：ops-manager

---

## 1. 提案结论

- 策略动作：`TIGHTEN`
- 提案摘要：action=TIGHTEN, capacity_warn=0.70->0.65, budget_warn=0.70->0.65

## 2. 建议变更

| 参数 | 当前值 | 建议值 | 变更幅度 |
|---|---|---|---|
| capacity.warn_utilization_ratio | 0.70 | 0.65 | -0.05 |
| slo.error_budget_warn_ratio | 0.70 | 0.65 | -0.05 |
