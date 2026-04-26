# Phase 8 多环境发布波次与容量回压计划

生成时间：2026-04-10 18:03:02  
版本范围：v2-prod-r1  
负责人：ops-manager

---

## 1. 当前决策

- 发布决策：`ROLLBACK`
- 摘要：decision=ROLLBACK, oncall=P1, ops=RED, capacity_pressure=0.0000, blocked_waves=1.; reasons=oncall 级别为 P1 或 ops 总体为 RED

## 2. 波次计划

| 波次 | 环境 | 流量比例 | 门禁条件 | 当前状态 | 备注 |
|---|---|---|---|---|---|
| wave-0 | staging | 0% | oncall<=P2 | blocked | 当前 oncall=P1 |
| wave-1 | prod-canary | 10% | oncall<=P2 | queued | 等待前序波次通过 |
| wave-2 | prod-small | 30% | oncall<=P3 | queued | 等待前序波次通过 |
| wave-3 | prod-medium | 60% | oncall<=P3 | queued | 等待前序波次通过 |
| wave-4 | prod-full | 100% | oncall<=P3 | queued | 等待前序波次通过 |

## 3. 回压动作

- 立即停止发布并回退到上一个稳定波次
- 通知 on-call 与发布负责人
- 保留证据并进入复盘流程

## 4. 证据输入

- policy: `docs/phase8_rollout_backpressure_policy.json`
- ops report: `docs/reports/phase8_ops_metrics_dashboard_latest.json`
- oncall report: `docs/reports/phase8_oncall_handbook_latest.json`
