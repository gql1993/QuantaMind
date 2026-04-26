# Phase 16 实施草案（Draft 0.1）

## 目标

在 Phase 15 工作台能力基础上，推进多端协同会话能力，让 Web/Desktop/CLI 的“谁在操作、会话是否在线、是否可恢复接管”变成显式可观测状态。

## Phase 16 拆分

1. **Phase 16-1 多端会话 Presence 与 Lease**
   - 建立 session lease 管理（open/heartbeat/release/expiry）
   - 支持 profile 维度查询当前活跃会话
2. **Phase 16-2 会话级事件轨迹**
   - 记录 session open/heartbeat/release 事件
   - 支持会话事件查询与审计
3. **Phase 16-3 工作台与会话联动**
   - workspace snapshot 返回当前活跃 session 指标
   - 多端接管时自动创建 recovery point
4. **Phase 16-4 多端并发策略**
   - 同 profile 多端并发写冲突策略
   - 安全模式下的单写多读约束

## Phase 16 收口（2026-04-12）

- 会话并发层已支持 `reader|writer` 模式，且同 profile 单 writer 冲突约束生效；
- gateway 已支持 writer 冲突返回 `409` 与可选 handover；
- workspace snapshot 已暴露会话 presence 指标；
- workspace 关键写操作（layout activate / shortcuts update / layout sync / recovery create&activate）
  已接入 writer lock 校验：若 profile 存在活跃 writer，仅该 writer 会话可写入；
- 审计链路已覆盖：
  - `session.open.conflict`
  - `session.open.handover`
  - `workspace.write.conflict`

> 结论：Phase 16 的会话协同能力具备“可观测 + 可约束 + 可追溯”最小闭环，可进入 Phase 17 协同调度策略深化。

## 本批第一项（16-1）验收标准

- `core/sessions` 具备最小 manager/storage/transcript 模块；
- gateway 提供 `sessions` lease 管理接口；
- 能在测试中验证 open -> heartbeat -> release 闭环。
