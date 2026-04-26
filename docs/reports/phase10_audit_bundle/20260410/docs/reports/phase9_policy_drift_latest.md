# Phase 9 策略漂移检测与阈值自适应建议报告

生成时间：2026-04-10 18:06:24  
版本范围：v2-prod-r1  
负责人：ops-manager

---

## 1. 漂移结论

- 结论：`ADJUST_REQUIRED`
- 摘要：alerts=2, capacity_delta=-0.5000, score_drop=35.5, oncall=P1.

## 2. 漂移观测

| 指标 | 当前值 | 基准值 | 偏移 | 结论 |
|---|---|---|---|---|
| capacity_pressure | 0.0000 | 0.5000 | -0.5000 | stable |
| weekly_score | 34.5 | 70.0 | 35.5 | drift |
| oncall_level | P1 | P3 | P3->P1 | drift |

## 3. 阈值自适应建议

- 建议将错误预算预警阈值下调 0.05，提前触发干预。
- 建议提升 on-call 值班密度并提前预热回退预案。
