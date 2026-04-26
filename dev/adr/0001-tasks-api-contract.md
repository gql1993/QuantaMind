# ADR 0001：任务列表 API 契约（阶段 0）

**状态**：已接受  
**日期**：2026-03  
**角色**：架构师智能体  

## 背景

产品原型与详细设计要求客户端具备「任务」页：全部/我发起的/待我审批/已完成 Tab，列表与详情。Gateway 需提供任务列表与详情接口，与 §11 接口规范一致。

## 决策

- **路径**：`GET /api/v1/tasks`、`GET /api/v1/tasks/{task_id}`。
- **列表**：响应体 `{ "tasks": [ TaskInfo, ... ] }`；查询参数 `filter` 可选：`all`（默认）、`pending_approval`、`completed`，与原型 Tab 对应。
- **单任务**：响应体为单个 `TaskInfo`；404 表示任务不存在。
- **TaskInfo 字段**（与 `quantamind/shared/api.py` 一致）：task_id, status, result, error, title, task_type, created_at, session_id, needs_approval。
- **存储**：阶段 0 使用内存字典；生产由 Hands/Heartbeat 持久化后改为统一任务存储与 Gateway 只读查询。

## 后果

- 客户端任务页可仅依赖上述两个 GET 接口实现列表与详情。
- 后续审批、任务创建/更新由独立端点（阶段 3）补充，本 ADR 不涉及。
