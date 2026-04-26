# Phase 18 数据库迁移预案草案

## 目标

将当前文件持久化（`coordination_audit.jsonl` + `coordination_policy.json`）平滑迁移到数据库后端，提升查询效率、并发一致性与长期运维能力。

## 现状

- 审计：JSONL 文件，支持恢复、压缩、轮转与归档索引
- 策略：JSON 文件，按 profile 存储冲突策略覆盖
- 健康自检接口：`/api/v2/coordination/persistence/health`

## 目标模型（草案）

### 表 1：`coordination_audit_events`

- `event_id` (pk)
- `created_at` (indexed)
- `profile_id` (indexed)
- `strategy`
- `outcome` (indexed)
- `reason`
- `run_id`
- `conflict_run_id`
- `route_mode`
- `payload_json`

### 表 2：`coordination_conflict_policies`

- `profile_id` (pk)
- `strategy`
- `source`
- `updated_at`

## 迁移步骤（建议）

1. **Schema 就绪**
   - 建表与索引
   - 增加只读探针
2. **Dual-write 阶段**
   - 继续写文件，同时写数据库
   - 对比写入计数与抽样校验
3. **Read cutover**
   - 查询接口优先读数据库
   - 文件作为 fallback
4. **收口**
   - 文件写入降级为归档备份
   - 固化回滚预案

## 当前推进状态（Phase 19-1）

- 已具备 dual-write 基线：
  - 文件主写 + SQLite 次写
  - 支持配置开关启用
  - 读路径保持文件优先，降低切换风险

## 回滚策略

- 任一阶段可切回文件读写
- 保留数据库写入日志与对账报告
- 保留最新归档索引，确保问题定位

## 接口草案

- `GET /api/v2/coordination/persistence/migration-plan`
  - 返回迁移阶段、当前状态与建议动作（当前为 `draft`）
