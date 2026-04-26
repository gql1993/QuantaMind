# Phase 7 发布决策记录（模板）

文档日期：{{DATE}}  
版本标识：{{VERSION}}  
责任人：{{OWNER}}

---

## 1. 决策结论

- 发布结论：`[Go / No-Go]`
- 决策时间：`[YYYY-MM-DD HH:MM]`
- 决策说明：`[一句话说明]`

## 2. 证据清单

- 基线报告：`docs/reports/phase6_v1_v2_baseline_latest.json`
- 灰度报告：`docs/reports/phase7_canary_rollout_latest.json`
- 联动演练：`docs/reports/phase7_pre_cutover_drill_latest.json`
- 回退预检：`docs/reports/phase7_rollback_drill_latest.json`
- 观测守护：`docs/reports/phase7_observability_guard_latest.json`

## 3. 发布窗口与范围

- 发布时间窗：`[开始 ~ 结束]`
- 发布范围：`[资料库/流水线/审批/任务等]`
- 灰度比例：`[如 10% -> 30% -> 100%]`
- 观察时长：`[每阶段分钟数]`

## 4. 风险与控制

| 风险项 | 当前状态 | 控制措施 | 负责人 |
|---|---|---|---|
| [风险示例] | [可控/不可控] | [措施] | [人] |

## 5. 回退策略确认

- 回退触发条件：`[引用观测规则]`
- 回退执行负责人：`[人]`
- 回退通知名单：`[群组/人员]`
- 预估回退耗时：`[分钟]`

## 6. 审批签字

- 架构负责人：`[签字/时间]`
- 研发负责人：`[签字/时间]`
- 测试负责人：`[签字/时间]`
- 发布负责人：`[签字/时间]`
