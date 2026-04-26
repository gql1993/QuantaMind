# Phase 20 实施草案（Draft 0.1）

## 目标

在 Phase 19 已具备 dual-write、对账与 cutover 预演基础上，推进数据库优先读的灰度化发布能力，降低一次性切流风险。

## 拆分建议

1. **Phase 20-1 灰度读路由**
   - 支持 `profile` 白名单直接命中数据库优先读
   - 支持按 `profile` 稳定哈希做比例灰度
   - Drill / Health 输出命中原因与路由结果

## 20-1 落地记录（2026-04-12）

- 新增配置：
  - `coordination.database_read_profile_allowlist`
  - `coordination.database_read_rollout_percentage`
- 路由策略：
  - 白名单优先
  - 其余 profile 按稳定哈希 bucket 命中灰度比例
  - 未命中灰度时继续走文件读路径
- 观测增强：
  - `cutover/drill` 输出 `routing_reason`、`allowlist_hit`、`rollout_bucket`
  - 健康报告保留最近读来源与路由原因

## 20-2 落地记录（2026-04-12）

- 新增运行时读观测：
  - profile 命中统计（top profiles / 读来源 / 回退计数）
  - 灰度覆盖率统计（database coverage / gray coverage）
  - 回退异常计数（fallback anomaly count）
- 观测出口增强：
  - `GET /api/v2/coordination/persistence/health` 增加 `read_observability`
  - `GET /api/v2/coordination/persistence/cutover/drill` 返回累计观测快照
  - `GET /api/v2/coordination/persistence/dashboard` 增加 `metrics.cutover`

## 20-3 落地记录（2026-04-12）

- 新增运行时灰度控制接口：
  - `GET /api/v2/coordination/persistence/cutover/controls`
  - `POST /api/v2/coordination/persistence/cutover/controls`
- 支持动态调整：
  - `profile_allowlist`
  - `rollout_percentage`
- 行为要求：
  - 更新后对当前进程立即生效
  - `cutover/drill` 与 `dashboard` 可直接看到最新控制面状态
