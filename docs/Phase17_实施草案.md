# Phase 17 实施草案（Draft 0.1）

## 目标

在 Phase 16 会话协同与并发约束基础上，推进协同调度策略深化，让多智能体任务执行具备更明确的优先级与预算治理能力。

## Phase 17 拆分建议

1. **Phase 17-1 任务优先级与预算感知调度**
   - 为协同任务引入优先级等级（例如：`low/normal/high`）
   - 在调度决策中显式考虑预算上限与超时风险
2. **Phase 17-2 调度冲突治理**
   - 同 profile 的并行协同任务建立冲突检测与降级策略
   - 高风险任务触发审批或人工确认门禁
3. **Phase 17-3 调度可观测性增强**
   - 输出结构化调度决策摘要（为何选该 agent / 为何降级）
   - 增加调度级审计与诊断导出接口

## 本批第一项（17-1）验收标准

- 规划输入可携带任务优先级；
- 调度输出包含预算与风险摘要；
- 网关能返回可读的调度策略信号；
- 有针对优先级和预算分支的单元测试覆盖。

## 17-1 落地记录（2026-04-12）

- `POST /api/v2/planning/preview` 支持输入：
  - `priority`（`low|normal|high`）
  - `budget_seconds`
- `core/planning/heuristics.py` 新增预算风险与优先级折算信号：
  - `requested_priority`
  - `effective_priority`
  - `budget_risk`
  - `budget_seconds`
- `core/planning/plan_builder.py` 新增 `scheduling` 输出：
  - `priority/requested_priority/budget_seconds/budget_risk`
  - `queue_hint`
  - `strategy`
- 测试覆盖：
  - `tests/v2/test_planning.py`
  - `tests/v2/test_gateway_planning_integrations.py`

## 17-2 落地记录（2026-04-12）

- 新增模块：`core/coordination/scheduling.py`
  - 冲突策略：`queue/reject/degrade_single_agent`
  - 冲突检测：同 profile 下活跃 `coordination root run`
  - 策略决策输出结构化 `CoordinationConflictDecision`
- 协同执行接口增强：`POST /api/v2/coordination/execute`
  - 新增输入：`profile_id/conflict_strategy/priority/budget_seconds`
  - 冲突行为：
    - `reject`：返回 `409`
    - `queue`：返回 queued run（不立即执行）
    - `degrade_single_agent`：强制降级为 single-agent 执行
- `core/coordination/supervisor.py` 支持 `forced_mode`，可在冲突时强制走 `single_agent`
- 测试覆盖：
  - `tests/v2/test_coordination.py`
  - `tests/v2/test_gateway_coordination.py`

## 17-3 落地记录（2026-04-12）

- 新增调度审计存储：
  - `core/coordination/audit.py`
  - 结构化字段包含 `detected/conflict_run_id/strategy/outcome/reason/route_mode`
- 协同执行接口审计沉淀：
  - `POST /api/v2/coordination/execute` 在 `reject/queue/degrade/normal/failed` 路径均写入审计
  - 审计事件 ID 统一为 `caev-*`
- 新增审计查询与导出接口：
  - `GET /api/v2/coordination/audit/events`
  - `GET /api/v2/coordination/audit/export`
  - 支持按 `profile_id/strategy/outcome/event_type` 过滤
- 测试覆盖：
  - `tests/v2/test_coordination.py`（store 过滤）
  - `tests/v2/test_gateway_coordination.py`（events/export 端到端）

## Phase 17 收口（2026-04-12）

- 策略参数统一收敛到 `AppSettings.coordination`：
  - `default_conflict_strategy`
  - `audit_export_limit_max`
  - `audit_retention_max_events`
- 网关已改为按配置执行：
  - 未传 `conflict_strategy` 时使用默认策略
  - 审计导出按 `audit_export_limit_max` 截断
  - 审计存储按 `audit_retention_max_events` 保留
- 运行手册已补充：
  - `docs/Phase17_调度策略运行手册.md`
