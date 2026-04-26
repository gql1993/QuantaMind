# Phase 8 生产运行度量看板（模板）

生成时间：{{DATE}}  
版本范围：{{VERSION}}  
负责人：{{OWNER}}

---

## 1. 总览结论

- 综合等级：`{{OVERALL_STATUS}}`
- 结论摘要：{{EXEC_SUMMARY}}

## 2. SLO 与错误预算

| 指标 | 当前值 | 目标/阈值 | 结论 |
|---|---|---|---|
{{SLO_TABLE}}

## 3. 容量与排队压力

| 指标 | 当前值 | 阈值 | 结论 |
|---|---|---|---|
{{CAPACITY_TABLE}}

## 4. 风险与动作

{{RISK_ITEMS}}

## 5. 输入与证据

{{EVIDENCE_ITEMS}}
