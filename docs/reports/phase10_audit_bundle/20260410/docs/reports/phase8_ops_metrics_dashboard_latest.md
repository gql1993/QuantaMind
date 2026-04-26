# Phase 8 生产运行度量看板（模板）

生成时间：2026-04-10 18:03:02  
版本范围：v2-prod-r1  
负责人：ops-manager

---

## 1. 总览结论

- 综合等级：`RED`
- 结论摘要：overall=RED, availability=0.9950, error_budget_ratio=0.0000, capacity_pressure=0.0000, guard=rollback_now.

## 2. SLO 与错误预算

| 指标 | 当前值 | 目标/阈值 | 结论 |
|---|---|---|---|
| Availability | 0.9950 | >= 0.9950 | yellow |
| Error Budget Consumed Ratio | 0.0000 | warn>=0.70, breach>=1.00 | green |
| Guard Decision | rollback_now | ok（理想） | yellow |

## 3. 容量与排队压力

| 指标 | 当前值 | 阈值 | 结论 |
|---|---|---|---|
| Pending Approvals | 0 | <= 20 | green |
| Timeout Tasks | 0 | <= 5 | green |
| Capacity Pressure | 0.0000 | warn>=0.70, critical>=1.00 | yellow |

## 4. 风险与动作

- 观测守护存在 critical 告警。
- 容量指标出现压力（pending approvals / timeout tasks）。
- 未获取到 failed_run_ratio，当前可用性按目标值占位。
- 容量实时指标不完整，当前结果为部分数据。

## 5. 输入与证据

- policy: `docs/phase8_ops_metrics_policy.json`
- guard report: `docs/reports/phase7_observability_guard_latest.json`
- biweekly report: `docs/reports/phase7_biweekly_stability_review_latest.json`
- live probes: `disabled`
