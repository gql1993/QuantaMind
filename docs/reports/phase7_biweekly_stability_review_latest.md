# Phase 7 双周稳定性复评报告（模板）

复评日期：2026-04-10  
观测窗口：2026-03-27 ~ 2026-04-10（14 天）  
版本标识：v2-cutover-r1  
复评负责人：release-manager

---

## 1. 结论

- 稳定性等级：`GREEN`
- 结论摘要：窗口内 guard=unknown（critical=0, warn=0），复盘材料数=3，建议等级=GREEN。

## 2. 指标快照

| 指标 | 当前值 | 阈值/目标 | 结论 |
|---|---|---|---|
| guard decision | unknown | ok/warn/rollback_now | 关注 |
| guard critical_count | 0 | 0 | 正常 |
| guard warn_count | 0 | 0（理想） | 正常 |
| failed run ratio | None | <= 0.2 | 正常 |
| pending approvals | None | <= 20 | 正常 |
| timeout tasks | None | <= 5 | 正常 |
| postmortem artifacts count | 3 | >= 1 | 正常 |

## 3. 风险与异常

- 未发现新增高风险异常。

## 4. 改进行动

- 维持当前灰度节奏，进入下一轮复评。

## 5. 证据与输入

- policy: `docs/phase7_observability_policy.json`
- guard: `docs/reports/phase7_observability_guard_latest.json`
- baseline: `docs/reports/phase6_v1_v2_baseline_latest.json`
- canary: `docs/reports/phase7_canary_rollout_latest.json`
- pre_cutover: `docs/reports/phase7_pre_cutover_drill_latest.json`
- rollback: `docs/reports/phase7_rollback_drill_latest.json`
- postmortem_dir: `docs/reports/postmortem-pack`
- live_probes: `disabled`
