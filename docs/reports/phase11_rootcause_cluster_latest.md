# Phase 11 异常根因聚类报告

生成时间：2026-04-10 19:07:11  
版本范围：v2-prod-r1

---

## 1. 聚类概览

- 聚类数：`5`
- 摘要：clusters=5, samples=14.

## 2. 聚类结果

| 聚类 | 命中数 | 样例 |
|---|---|---|
| other | 8 | 未获取到 failed_run_ratio，当前可用性按目标值占位。 |
| rollback_risk | 3 | observability guard 判定 rollback_now |
| alerting | 1 | 观测守护存在 critical 告警。 |
| capacity_pressure | 1 | 容量指标出现压力（pending approvals / timeout tasks）。 |
| policy_drift | 1 | 建议将错误预算预警阈值下调 0.05，提前触发干预。 |
