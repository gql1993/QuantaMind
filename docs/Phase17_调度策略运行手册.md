# Phase 17 调度策略运行手册

## 1. 适用范围

本手册覆盖 Phase 17 的协同调度能力：

- 17-1：任务优先级 + 预算感知调度
- 17-2：同 profile 并行冲突检测与降级策略
- 17-3：冲突决策审计与导出

## 2. 统一配置项（`AppSettings.coordination`）

可通过 `create_app(settings=...)` 注入：

```json
{
  "coordination": {
    "default_conflict_strategy": "degrade_single_agent",
    "audit_export_limit_max": 1000,
    "audit_retention_max_events": 2000,
    "state_dir": ".quantamind_v2_runtime/coordination"
  }
}
```

字段说明：

- `default_conflict_strategy`
  - 当 `POST /api/v2/coordination/execute` 未显式传 `conflict_strategy` 时生效
  - 可选值：`queue` / `reject` / `degrade_single_agent`
- `audit_export_limit_max`
  - `GET /api/v2/coordination/audit/export` 的导出条数上限
  - 实际导出条数 = `min(request.limit, audit_export_limit_max)`
- `audit_retention_max_events`
  - 内存审计存储保留上限（超过后自动淘汰最早事件）
- `state_dir`
  - 调度审计与策略覆盖的持久化目录
  - 默认包含：
    - `coordination_audit.jsonl`
    - `coordination_policy.json`
- `audit_rotate_max_bytes`
  - 审计文件按大小轮转阈值（字节）
- `audit_rotate_interval_seconds`
  - 审计文件按时间轮转阈值（秒）
- `dual_write_enabled`
  - 是否启用文件 + SQLite 双写
- `database_read_preferred`
  - 是否启用 SQLite 优先读（cutover 预演）
- `database_read_fallback_to_file`
  - SQLite 读失败时是否自动回退文件读
- `database_read_profile_allowlist`
  - 指定优先走 SQLite 读路径的 profile 白名单
- `database_read_rollout_percentage`
  - 对非白名单 profile 执行稳定哈希灰度（0-100）
- `database_path`
  - dual-write 模式下 SQLite 数据库文件路径

## 3. 运行时接口

### 3.1 协同执行

`POST /api/v2/coordination/execute`

请求关键字段：

- `message`
- `profile_id`
- `priority`（`low|normal|high`）
- `budget_seconds`
- `conflict_strategy`（可选，未传则使用默认策略）
  - 若存在 profile 持久化覆盖，优先使用覆盖策略

### 3.2 审计查询

`GET /api/v2/coordination/audit/events`

可选过滤参数：

- `profile_id`
- `strategy`
- `outcome`
- `event_type`
- `limit`

### 3.3 审计导出

`GET /api/v2/coordination/audit/export`

返回 `summary` 中关键字段：

- `requested_limit`
- `effective_limit`
- `configured_export_limit_max`

### 3.4 持久化健康自检

`GET /api/v2/coordination/persistence/health`

返回：

- `audit`：审计持久化健康（status/retained_events/invalid_lines_detected/backup 信息）
- `policy`：策略持久化健康（status/profiles_count/backup 信息）
- 若启用 dual-write cutover：
  - `read_observability.total_reads`
  - `read_observability.database_coverage_ratio`
  - `read_observability.fallback_anomaly_count`
  - `read_observability.profile_hits`

### 3.5 归档索引与迁移草案

- `GET /api/v2/coordination/persistence/archives`
  - 返回归档列表（archive_file/rotated_at/reason/size_bytes/event_lines）
- `GET /api/v2/coordination/persistence/migration-plan`
  - 返回数据库迁移预案接口草案（当前为 `draft`）

### 3.6 统一观测面板

- `GET /api/v2/coordination/persistence/dashboard`
  - `summary`：总体状态、告警数量、归档数量、策略覆盖数量
  - `metrics.audit`：当前大小、阈值占用、最近轮转、坏行计数
  - `metrics.archive`：最新归档与总归档数
  - `metrics.cutover`：灰度覆盖率、回退异常计数、profile 命中统计
  - `alerts`：可执行告警建议
  - `thresholds`：当前生效阈值与建议阈值

### 3.7 dual-write 一致性校验

- `GET /api/v2/coordination/persistence/consistency`
  - 参数：
    - `profile_id`（可选）
    - `window_limit`（审计窗口）
    - `policy_limit`（策略窗口）
  - 输出：
    - `reports.audit.difference_count`
    - `reports.policy.difference_count`
    - `anomalies`（异常样本）

### 3.8 cutover 演练

- `GET /api/v2/coordination/persistence/cutover/drill`
  - 参数：
    - `profile_id`（用于策略读演练）
    - `window_limit`（审计读窗口）
    - `simulate_secondary_failure`（可选，模拟 SQLite 读失败）
  - 关键输出：
    - `reports.audit.selected_backend`
    - `reports.policy.selected_backend`
    - `reports.*.fallback_used`
    - `reports.*.routing_reason`
    - `reports.*.rollout_bucket`
    - `reports.*.observability`

### 3.9 cutover 灰度控制面

- `GET /api/v2/coordination/persistence/cutover/controls`
  - 查看当前运行时灰度配置
- `POST /api/v2/coordination/persistence/cutover/controls`
  - 支持动态更新：
    - `profile_allowlist`
    - `rollout_percentage`
  - 说明：
    - 当前为进程内运行时控制，重启后回到配置文件初始值

## 4. 冲突策略建议

- `degrade_single_agent`：默认推荐；优先保证请求可执行
- `queue`：强调顺序一致性场景（避免并行写冲突）
- `reject`：高风险生产窗口或强门禁场景

## 5. 运维检查清单

- 配置检查：`GET /api/v2/config/summary` 确认 `coordination` 字段
- 策略覆盖检查：
  - `GET /api/v2/coordination/policies/conflict-strategy?profile_id=...`
  - `POST /api/v2/coordination/policies/conflict-strategy`
- 冲突路径验证：分别触发 `reject/queue/degrade_single_agent`
- 审计覆盖验证：检查 `coordination_conflict_decided` 是否包含 `reason/outcome/strategy`
- 导出上限验证：大 `limit` 请求时确认 `effective_limit` 被正确截断
