# Phase 8 故障演练自动评分报告

生成时间：2026-04-10 18:03:02  
版本范围：v2-prod-r1  
负责人：ops-manager

---

## 1. 评分结论

- 总分：`4.00`
- 等级：`D`
- 摘要：score=4.00, grade=D, pre_rate=0.0000, canary_rate=0.0000, rollback_ready=False, oncall=P1, ops=RED.

## 2. 分项得分

| 项目 | 权重 | 指标值 | 得分 |
|---|---|---|---|
| pre_cutover_pass_rate | 35 | 0.0000 | 0.00 |
| canary_pass_rate | 25 | 0.0000 | 0.00 |
| rollback_ready | 20 | False | 0.00 |
| oncall_level | 10 | P1 | 2.00 |
| ops_overall_status | 10 | RED | 2.00 |

## 3. 风险与改进建议

- pre-cutover 通过率不足（0/4）。
- canary 通过率不足（0/2）。
- rollback drill 未就绪。
- 当前 on-call 级别偏高（P1）。
- ops 看板状态为 RED。

## 4. 证据输入

- policy: `docs/phase8_drill_scoring_policy.json`
- pre-cutover: `docs/reports/phase7_pre_cutover_drill_latest.json`
- canary: `docs/reports/phase7_canary_rollout_latest.json`
- rollback: `docs/reports/phase7_rollback_drill_latest.json`
- oncall: `docs/reports/phase8_oncall_handbook_latest.json`
- ops: `docs/reports/phase8_ops_metrics_dashboard_latest.json`
