# Phase 9 管理驾驶舱周报

周报日期：2026-04-10  
版本范围：v2-prod-r1  
负责人：release-manager

---

## 1. 周度结论

- 综合得分：`34.5`
- 等级：`D`
- 摘要：score=34.5, grade=D, ops=RED, oncall=P1, wave=ROLLBACK, drill=D, bundle=ATTENTION.

## 2. 关键状态快照

| 维度 | 当前状态 | 说明 |
|---|---|---|
| Ops Dashboard | RED | 来源 phase8_ops_metrics_dashboard |
| Oncall Level | P1 | 来源 phase8_oncall_handbook |
| Wave Decision | ROLLBACK | 来源 phase8_wave_rollout_backpressure |
| Drill Grade | D | 来源 phase8_fault_drill_scoring |
| Daily Bundle | ATTENTION | 来源 phase9_daily_ops_bundle |

## 3. 风险与决策建议

- 生产运行总览为 RED。
- on-call 等级偏高（P1）。
- 发布波次决策为 ROLLBACK。
- 故障演练评分等级为 D。
- 每日批任务存在 attention。

## 4. 下周重点动作

- 优先恢复可用性并清理容量积压。
- 降低告警级别并完成值班交接闭环。
- 修复阻断项后重新评估发布窗口。
- 按改进台账推进并完成复测。
- 排查失败任务并补齐证据归档。
