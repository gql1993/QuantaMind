# Phase 11 发布策略自动学习报告

生成时间：2026-04-10 19:07:11  
版本范围：v2-prod-r1  
负责人：release-manager

---

## 1. 学习结论

- 策略分数：`43.0`
- 建议动作：`TIGHTEN`
- 摘要：score=43.0, action=TIGHTEN, weekly=D, gate=BLOCK, drift=ADJUST_REQUIRED.

## 2. 学习信号

| 信号 | 输入值 | 权重 | 贡献分 |
|---|---|---|---|
| weekly_grade | D | 0.40 | 16.0 |
| quality_gate | BLOCK | 0.30 | 10.5 |
| policy_drift | ADJUST_REQUIRED | 0.30 | 16.5 |

## 3. 建议调整

- 收紧发布门禁，降低并行高风险变更上限。
- 提升 P1/P2 告警触发后的冻结时长。
