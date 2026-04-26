# Phase 8 生产告警分层与 On-Call 响应手册

生成时间：2026-04-10 18:03:02  
版本范围：v2-prod-r1  
值班负责人：ops-manager

---

## 1. 当前态势

- 当前告警等级：`P1`
- 结论摘要：current_level=P1; reasons=ops dashboard 为 RED; observability guard 判定 rollback_now; dependency compatibility 为 BLOCK

## 2. 告警分层规则

| 级别 | 含义 | 触发条件（示例） | SLA |
|---|---|---|---|
| P1 | 核心可用性风险，需立即处置 | ops_dashboard.overall_status == RED; observability_guard.summary.decision == rollback_now; dependency_compat.assessment.result == BLOCK | 15 min |
| P2 | 重要能力退化，需限时恢复 | ops_dashboard.overall_status == YELLOW; observability_guard.summary.decision == warn; dependency_compat.assessment.result == CONDITIONAL_PASS | 60 min |
| P3 | 低风险提示，纳入常规跟踪 | 指标轻微波动但未超阈值; 临时告警自动恢复 | 240 min |

## 3. 升级与通知路径

| 级别 | 通知角色 | 通知通道 |
|---|---|---|
| P1 | oncall, release-manager, tech-lead, ops-lead | war-room + phone |
| P2 | oncall, tech-lead, qa-lead | group-chat + ticket |
| P3 | oncall | ticket |

## 4. 响应动作手册

- 0~5 分钟：确认告警源与影响面，拉起 war-room。
- 5~15 分钟：执行止损动作（限流/降级/回退评估）。
- 15 分钟后：持续同步进展并准备复盘证据。

## 5. 交接与复盘要求

- 交接前更新：告警状态、处置动作、剩余风险；
- P1/P2 必须补充复盘记录并关联归档清单；
- 交接模板见：`docs/templates/Phase8_OnCall交接模板.md`。
