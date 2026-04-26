# Phase 8 生产告警分层与 On-Call 响应手册

生成时间：{{DATE}}  
版本范围：{{VERSION}}  
值班负责人：{{OWNER}}

---

## 1. 当前态势

- 当前告警等级：`{{CURRENT_LEVEL}}`
- 结论摘要：{{EXEC_SUMMARY}}

## 2. 告警分层规则

| 级别 | 含义 | 触发条件（示例） | SLA |
|---|---|---|---|
{{LEVEL_TABLE}}

## 3. 升级与通知路径

| 级别 | 通知角色 | 通知通道 |
|---|---|---|
{{ESCALATION_TABLE}}

## 4. 响应动作手册

{{RUNBOOK_ITEMS}}

## 5. 交接与复盘要求

- 交接前更新：告警状态、处置动作、剩余风险；
- P1/P2 必须补充复盘记录并关联归档清单；
- 交接模板见：`docs/templates/Phase8_OnCall交接模板.md`。
