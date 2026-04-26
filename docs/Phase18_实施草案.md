# Phase 18 实施草案（Draft 0.1）

## 目标

将 Phase 17 的内存调度审计与冲突策略治理推进到持久化层，提升跨进程一致性与运行可恢复性。

## 拆分建议

1. **Phase 18-1 持久化基线**
   - 调度审计持久化（文件型 JSONL）
   - profile 级冲突策略持久化（文件型 JSON）
2. **Phase 18-2 一致性与恢复**
   - 启动恢复与跨实例可见性验证
   - 审计文件轮转与归档
3. **Phase 18-3 运维化**
   - 状态探针与故障自检
   - 迁移到数据库存储（可选）

## 本批第一项（18-1）验收标准

- 调度审计可跨 app 实例读取；
- profile 策略覆盖可跨 app 实例生效；
- `coordination.execute` 在未传 `conflict_strategy` 时可读取持久化覆盖；
- 有端到端测试证明跨实例一致可见。

## 18-2 落地记录（2026-04-12）

- 审计文件裁剪/轮转：
  - `FileBackedCoordinationAuditStore` 启动与写入时触发 compact 检查
  - 非法行或超保留上限触发自动恢复（保留最新有效事件）
  - 恢复前自动生成 `.bak` 备份
- 启动恢复校验：
  - 审计与策略文件在初始化时执行 recovery 校验
  - 破损 JSON/JSONL 自动回收并重建基础文件
- 持久化健康自检接口：
  - `GET /api/v2/coordination/persistence/health`
  - 返回 `audit/policy` 的状态、当前文件大小、最近 compact/backup 信息

## 18-3 落地记录（2026-04-12）

- 审计轮转归档策略：
  - 按大小轮转（`audit_rotate_max_bytes`）
  - 按时间轮转（`audit_rotate_interval_seconds`）
  - 轮转产物进入归档索引 `coordination_audit_archives.json`
- 新增接口：
  - `GET /api/v2/coordination/persistence/archives`
  - `GET /api/v2/coordination/persistence/migration-plan`
- 配置增强：
  - `coordination.audit_rotate_max_bytes`
  - `coordination.audit_rotate_interval_seconds`
- 数据库迁移预案文档：
  - `docs/Phase18_数据库迁移预案草案.md`

## Phase 18 收口（2026-04-12）

- 统一观测面板输出：
  - `GET /api/v2/coordination/persistence/dashboard`
  - 聚合轮转、恢复、归档和策略覆盖关键指标
- 告警阈值建议：
  - 输出 `thresholds`（包含 size/time/retention/export）
  - 输出 `alerts`（健康异常、轮转压力、数据质量）
- 目标达成：
  - 轮转/恢复/归档指标具备统一读取面
  - 提供运维侧可执行建议（recommended_action）
