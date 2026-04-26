# QuantaMind 2.0 实施路线图

**文档版本：** Draft 0.1  
**编制日期：** 2026-04-07  
**关联文档：**

- `docs/QuantaMind_2.0_目录与模块设计稿.md`
- `docs/QuantaMind量智大脑详细设计说明书.md`
- `dev/ROADMAP.md`

---

## 1. 路线图目标

本路线图用于将 `QuantaMind 2.0 目录与模块设计稿` 从架构蓝图细化为可执行工程计划，目标是在**不破坏当前 V1 稳定线**的前提下，逐步建立：

1. **任务驱动内核**
2. **显式多智能体协同控制平面**
3. **上下文装配与压缩机制**
4. **分级工具运行时**
5. **Artifact-first 结果体系**
6. **桌面 / Web 工作台壳层**

---

## 2. 开发总原则

## 2.1 双线并行

- `V1`：继续承接线上可用版本、演示、稳定性修复、业务维护
- `V2`：承接新架构验证、目录骨架、模块迁移、客户端工作台

建议分支策略：

- `main` 或 `v1-stable`
- `v2-architecture`
- 视情况补专题分支：
  - `v2-runs`
  - `v2-coordination`
  - `v2-shortcuts`
  - `v2-tool-runtime`
  - `v2-client-workspace`

## 2.2 同仓并行

建议继续采用同仓目录隔离：

```text
quantamind/        # V1
quantamind_v2/     # V2
tests/v1/          # V1 测试
tests/v2/          # V2 测试
```

这样做的好处：

- 共享领域适配器和基础设施
- 保持知识与文档集中
- 便于逐模块迁移
- 降低“完全新仓重建”的成本

## 2.3 发布策略

建议 2.0 的演进采用“三阶段发布”：

1. **内部实验版**
   - 仅开发者可用
   - 不替代 V1

2. **并行试运行版**
   - V1 / V2 同时可访问
   - 可做真实任务对比

3. **切换评估版**
   - 按场景逐步将流量切到 V2
   - 保留回退开关

---

## 3. 里程碑总览

| 阶段 | 名称 | 目标 | 主要产物 | 建议周期 |
|------|------|------|----------|---------|
| Phase 0 | 基线冻结与分支就绪 | 锁定 V1，建立 V2 开发线 | 分支、目录、基线文档 | 1-2 天 |
| Phase 1 | 2.0 骨架层 | 建立 `quantamind_v2/` 空间与核心契约 | contracts/core/runs 骨架 | 3-5 天 |
| Phase 2 | 任务与协同控制平面 | 建立 Run 与多智能体协同 | runs + coordination + shortcuts | 1-2 周 |
| Phase 3 | 执行平面升级 | 工具/模型/MCP/worker 分级 | runtimes/* | 1-2 周 |
| Phase 4 | Artifact 与上下文层 | 建立结果载体与上下文装配 | artifacts + context_assembler + memory bridge | 1-2 周 |
| Phase 5 | 2.0 客户端工作台 | Run Console、Approval Center、Artifact Viewer | client/web + client/desktop | 2-3 周 |
| Phase 6 | 领域迁移与对比验证 | 将情报、流水线、资料库等迁入 V2 | 领域服务与对比报告 | 2-4 周 |
| Phase 7 | 切换准备 | 评估 V2 是否可替代 V1 | 发布策略、回退策略、切换清单 | 1 周 |

---

## 4. Phase 0：基线冻结与分支就绪

## 4.1 目标

- 明确 `V1` 为当前稳定可运行版本
- 建立 `V2` 独立开发线
- 固化对比基线，防止 V2 改造过程中“失去参照物”

## 4.2 实施项

1. 建立并固定 `v1-stable`
2. 建立 `v2-architecture`
3. 记录当前 V1 能力基线：
   - 聊天
   - 情报员
   - 流水线
   - 资料库
   - 数据库与 pgvector
4. 明确 V2 初期端口、配置与数据隔离方式

## 4.3 交付物

- 分支策略说明
- V1 基线检查清单
- V2 开发约定文档

## 4.4 验收标准

- 能明确区分“V1 维护修改”和“V2 架构变更”
- 后续任何 2.0 任务都不需要依赖直接修改 V1 目录

---

## 5. Phase 1：2.0 骨架层

## 5.1 目标

把 2.0 的目录、契约、入口和最小骨架搭起来，但**不急于迁移业务逻辑**。

## 5.2 推荐先落目录

```text
quantamind_v2/
├── __init__.py
├── contracts/
├── core/
│   ├── gateway/
│   ├── runs/
│   ├── coordination/
│   ├── context_assembler/
│   ├── approvals/
│   ├── sessions/
│   └── planning/
├── runtimes/
│   ├── tools/
│   ├── models/
│   ├── workers/
│   └── mcp/
├── shortcuts/
├── artifacts/
├── memory/
├── services/
├── integrations/
└── client/
```

## 5.3 必须先有的基础文件

- `contracts/run.py`
- `contracts/event.py`
- `contracts/artifact.py`
- `core/runs/coordinator.py`
- `core/runs/lifecycle.py`
- `core/gateway/app.py`
- `shortcuts/registry.py`

## 5.4 交付物

- `quantamind_v2/` 目录骨架
- 统一数据契约草稿
- 2.0 最小入口

## 5.5 验收标准

- 2.0 可作为独立 Python 包导入
- 新目录结构清晰，不再把控制逻辑散落在单个 `gateway.py`

---

## 6. Phase 2：任务与协同控制平面

这是 2.0 的第一核心阶段。

## 6.1 目标

建立：

- `RunCoordinator`
- `Run Registry`
- `Run Lifecycle`
- `Multi-Agent Coordination`
- `ShortcutIntentRegistry`

## 6.2 优先能力

### A. Run 模型统一

统一 V1 当前分裂状态：

- `chat_jobs`
- `pipelines`
- `tasks`
- `intel reports`
- `library ingest jobs`

建议统一字段：

- `run_id`
- `run_type`
- `origin`
- `parent_run_id`
- `state`
- `stage`
- `status_message`
- `owner_agent`
- `artifacts`
- `events`
- `created_at`
- `updated_at`
- `completed_at`

### B. 多智能体协同

建议先支持三种基本协同模式：

1. `single_agent`
2. `shortcut`
3. `multi_agent_plan`

### C. Shortcut 机制

优先把 V1 中已证明有价值的捷径固化：

- 今日情报日报
- 查看今日日报
- 查看最近报告
- 检查系统状态
- 查看数据库状态

## 6.3 优先实现顺序

1. `core/runs/`
2. `shortcuts/`
3. `core/coordination/router.py`
4. `core/coordination/planner.py`
5. `core/coordination/merger.py`

## 6.4 最先迁移的业务场景

建议用这两个场景作为 2.0 第一批试点：

### 场景 1：情报员日报

原因：

- 路径清晰
- 当前痛点明显
- 快捷路径价值高
- 易于验证 Artifact 化

### 场景 2：系统状态/数据库状态查询

原因：

- 高频
- 确定性强
- 可作为 Run + Shortcut 的稳定样板

## 6.5 验收标准

- V2 中能创建统一 `run`
- 快捷路径能返回结构化 Run 状态
- 多智能体协同骨架能表达父子任务关系

---

## 7. Phase 3：执行平面升级

## 7.1 目标

把执行从“统一函数调用”升级为“分级运行时”。

## 7.2 核心模块

- `runtimes/tools/executor.py`
- `runtimes/tools/isolation.py`
- `runtimes/tools/classes.py`
- `runtimes/workers/task_worker.py`
- `runtimes/models/*`
- `runtimes/mcp/*`

## 7.3 工具分类建议

| 类型 | 示例 | 默认执行方式 | 是否需审批 |
|------|------|-------------|-----------|
| `query` | 状态查询、数据库读 | 线程/协程 | 否 |
| `mutation` | 配置修改、资料写入 | 线程/子进程 | 可选 |
| `long_running` | 情报抓取、流水线、仿真 | worker | 否/可选 |
| `external_delivery` | 飞书发送、外部同步 | worker | 建议有策略 |
| `device_command` | SECS/GEM / 设备控制 | 子进程/worker | 是 |

## 7.4 本阶段重点

1. 解决同步工具阻塞事件循环问题
2. 解决长任务拖死 gateway 问题
3. 建立可取消、可重试、可预算执行模型
4. 给后续 MCP 外接能力留口

## 7.5 验收标准

- 长任务不会拖死主服务
- 工具执行可追踪阶段
- 每类工具有默认运行策略

---

## 8. Phase 4：Artifact 与上下文层

## 8.1 目标

把“结果是聊天文本”升级为“结果是 Artifact，聊天只是入口”。

## 8.2 Artifact 层要先承接的产物

1. `intel_report`
2. `pipeline_report`
3. `system_diagnosis`
4. `db_health_report`
5. `library_ingest_report`

## 8.3 Context Assembler 首先服务的场景

1. 情报员
2. 数据分析师
3. 工艺工程师
4. 理论物理学家

## 8.4 推荐实现点

- 按 Agent 装上下文
- 按任务类型装上下文
- 按 Run 阶段裁剪上下文
- 做压缩和 cache key

## 8.5 验收标准

- 至少 2 个重任务以 Artifact 为主输出
- 至少 2 类 Agent 用上动态上下文装配

---

## 9. Phase 5：2.0 客户端工作台

## 9.1 目标

从“聊天页 + 零散页面”升级为“工作台”。

## 9.2 Web 客户端优先建设内容

- Run Console
- Background Task Center
- Artifact Viewer
- Approval Center
- Shortcut Launcher

## 9.3 Desktop 客户端优先建设内容

- 多面板工作台壳
- 本地拖拽导入
- 通知与后台任务
- 本地工具入口

## 9.4 推荐信息架构

### 左栏

- 会话
- 快捷命令
- 后台任务

### 中栏

- 聊天 / 任务说明

### 右栏

- 当前 Run 状态
- 当前阶段
- 当前工具
- 当前审批

### 下方/副面板

- Artifact 预览
- 日志
- 步骤轨迹

## 9.5 验收标准

- 用户可以不依赖聊天也能追踪任务
- 用户能看到阶段、审批、artifact

---

## 10. Phase 6：领域迁移与对比验证

## 10.1 目标

把 V2 真正拉到能和 V1 做功能与稳定性对比。

## 10.2 优先迁移场景

1. 情报员日报链路
2. 系统状态 / 数据库状态
3. 资料库导入
4. 一条标准流水线
5. 一条多智能体协同任务

## 10.3 对比指标

| 指标 | V1 | V2 | 目标 |
|------|----|----|------|
| 长任务稳定性 | 容易拖住聊天/服务 | 明显改善 | V2 更稳 |
| 状态可观测性 | 低 | 高 | V2 可视化 |
| 上下文效率 | 低 | 中/高 | V2 更省 |
| 高风险执行控制 | 弱 | 强 | V2 有审批 |
| 结果复用性 | 低 | 高 | V2 Artifact 化 |

## 10.4 验收标准

- 至少 3 个核心场景可在 V2 跑通
- V2 至少在 2 个场景明显优于 V1

---

## 11. Phase 7：切换准备

## 11.1 目标

决定是否将 V2 提升为主线。

## 11.2 判断标准

只有当以下条件满足，才建议进入切换评估：

1. 情报链路稳定
2. 长任务不拖死主服务
3. Run Console 可用
4. 审批机制可用
5. 至少一个多智能体闭环场景稳定
6. 回退到 V1 简单明确

## 11.3 切换方式建议

### 方案 A：按功能切换

- 情报员先走 V2
- 流水线暂留 V1
- 资料库导入后迁 V2

### 方案 B：按客户端切换

- Web 保守
- Desktop 优先接 V2

### 方案 C：按用户切换

- 开发/内部用户先用 V2
- 对外演示仍用 V1

---

## 12. 风险与对策

| 风险 | 表现 | 对策 |
|------|------|------|
| V2 范围过大 | 一次性重构失控 | 严格按阶段推进 |
| V1 被误伤 | 当前可运行版本失稳 | V1/V2 目录隔离 |
| 客户端壳层先行过重 | 过早做 UI 重工程 | 先做内核，再做壳层 |
| 多智能体协同过早复杂化 | 计划大于实现 | 第一阶段只支持 3 种协同模式 |
| Artifact 设计不统一 | 结果继续散落 | 先统一 artifact schema |
| 工具运行时迁移过快 | 回归风险大 | 先迁高频重任务，再迁全部工具 |

---

## 13. 推荐的当前下一步

如果按本路线图继续推进，建议接下来的实际工作顺序是：

1. 在仓库中创建 `quantamind_v2/` 目录骨架
2. 落 `contracts/` 与 `core/runs/` 最小实现
3. 落 `shortcuts/` 注册表
4. 把“今日情报快捷路径”作为 V2 第一条试点链路迁入
5. 建最小 `Run Console` 原型

这 5 步完成后，2.0 就会从“设计稿”进入“可运行实验线”。

### 13.1 当前推进状态（2026-04-07）

已完成（内核）：

1. `quantamind_v2/` 目录骨架与 contracts/core/runs/shortcuts 基础模块
2. `RunCoordinator` + lifecycle + events + snapshot persistence（内存实现）
3. `coordination` 最小闭环（router/planner/delegation/supervisor/merger）
4. `shortcut` 到 `artifact` 的统一写入链路
5. `coordination/execute` 的 merged 结果自动 Artifact 化
6. `artifact` API（list/get/view/run-scoped）与类型化渲染（含 `coordination_report`）
7. 最小 Run Console 后端接口：
   - `GET /api/v2/console/runs`
   - `GET /api/v2/runs/{run_id}/events`
   - `GET /api/v2/runs/{run_id}/snapshot`
   - `GET /api/v2/shortcuts`
8. Phase 3 worker 最小内核：
   - `runtimes/workers/task_worker.py`
   - 支持提交、取消、重试、预算超时、结果查询与等待
   - 可与 `RunCoordinator` 同步 run 阶段与状态（running/completed/failed/cancelled）
9. Phase 3 ToolRuntime ↔ Worker 联动：
   - `ToolRuntimeExecutor` 在 `WORKER` 隔离模式下支持 task worker
   - 支持 `run_id`、`budget_seconds`、`max_retries`、`background` 参数
   - 同步返回 `task_id` 与 `task_state`，支持后台提交场景
10. Gateway 最小 Task API（面向 Background Task Center）：
   - `GET /api/v2/tasks`
   - `GET /api/v2/tasks/{task_id}`
   - `POST /api/v2/tasks/{task_id}/cancel`
   - `POST /api/v2/tasks/{task_id}/retry`
   - `POST /api/v2/tasks/shortcuts/{shortcut_name}`（后台 shortcut 执行）
11. Phase 3 Run events 标准化：
   - 新增 `tool_started` / `tool_completed` / `tool_failed` 事件
   - `ToolRuntimeExecutor` 可将工具执行轨迹写入 `RunCoordinator` 事件流
12. Phase 5 Web Run Console 最小原型（接入现有 V2 API）：
   - 页面入口：`quantamind/client/web` 增加 `Run Console` 导航
   - 对接 `GET /api/v2/console/runs`（列表 + 状态筛选）
   - 对接 `GET /api/v2/runs/{run_id}/events` 与 `GET /api/v2/runs/{run_id}/snapshot`
   - 对接 `GET /api/v2/runs/{run_id}/artifacts` 与 `GET /api/v2/artifacts/{artifact_id}/view`
   - 集成 `Shortcut Launcher`，支持 `POST /api/v2/tasks/shortcuts/{shortcut_name}` 后台执行
13. Phase 5 Approval Center 最小闭环（后端 + 前端占位页）：
   - 后端新增审批接口：
     - `GET /api/v2/approvals`
     - `POST /api/v2/approvals`
     - `GET /api/v2/approvals/{approval_id}`
     - `POST /api/v2/approvals/{approval_id}/approve`
     - `POST /api/v2/approvals/{approval_id}/reject`
   - 审批动作可回写 run 阶段与事件（`approval_requested/approved/rejected`）
   - Web 壳新增「审批中心」占位页，支持创建审批、筛选列表、通过/拒绝与关联 Run 跳转
14. Phase 5 Background Task Center 前端页（最小可用）：
   - Web 壳新增「后台任务中心」页面（V2）
   - 对接 `GET /api/v2/tasks` 列表 + 状态筛选
   - 支持 `POST /api/v2/tasks/{task_id}/cancel` 和 `POST /api/v2/tasks/{task_id}/retry`
   - 展示任务详情（error/result/attempt/budget/time）
   - 支持 run/task 联动：从任务详情一键跳转关联 `Run Console`
15. Phase 5 Artifact Viewer 专用页（最小可用）：
   - Web 壳新增「Artifact Viewer」页面（V2）
   - 对接 `GET /api/v2/artifacts`（支持 run_id 检索）
   - 提供 artifact_type 与关键词过滤
   - 对接 `GET /api/v2/artifacts/{artifact_id}` + `GET /api/v2/artifacts/{artifact_id}/view`
   - 按 `artifact_type` 输出差异化摘要（`coordination_report`、`intel_report`、诊断类、generic）
   - 与 `Run Console` 双向联动（artifact -> run / run -> artifact viewer）
16. Phase 6 资料库导入链路迁入 V2（第一批）：
   - 后端新增：
     - `POST /api/v2/library/upload`
     - `GET /api/v2/library/files`
     - `GET /api/v2/library/files/{file_id}`
     - `GET /api/v2/library/stats`
   - 上传后自动创建 `import_run` + `library_ingest:*` task
   - ingest 完成自动写入 `library_ingest_report` artifact 并挂接 run
   - 新增测试 `tests/v2/test_gateway_library.py`
   - 已输出对比报告：`docs/Phase6_资料库导入_V1_V2_链路对比报告.md`
17. Phase 6 标准流水线迁入 V2（第一批）：
   - 后端新增：
     - `GET /api/v2/pipelines/templates`
     - `POST /api/v2/pipelines/execute`
   - 默认模板 `standard_daily_ops`（`system_status` -> `db_status` -> `intel_today`）
   - 执行过程产出 `pipeline_run` + background task + child runs + `pipeline_report` artifact
   - 新增测试 `tests/v2/test_gateway_pipeline.py`
   - 已输出稳定性对比报告：`docs/Phase6_标准流水线_V1_V2_稳定性对比报告.md`
18. Phase 6 V1/V2 对比基线与回归脚本：
   - 新增基线探测脚本：`scripts/v1_v2_baseline_regression.py`
   - 新增回归总入口脚本：`scripts/run_phase6_regression.py`
   - 新增说明文档：`docs/Phase6_V1_V2_对比基线与回归脚本.md`
   - 基线报告默认输出：`docs/reports/phase6_v1_v2_baseline_latest.json`
19. Phase 7 切换评估与回退演练（第一批）：
   - 新增切换就绪检查脚本：`scripts/phase7_cutover_readiness.py`
   - 新增回退演练脚本：`scripts/phase7_rollback_drill.py`
   - 新增清单文档：`docs/Phase7_切换评估与回退演练清单.md`
   - 默认报告输出：
     - `docs/reports/phase7_cutover_readiness_latest.json`
     - `docs/reports/phase7_rollback_drill_latest.json`
20. Phase 7 切换前联动演练脚本（审批/任务/回退）：
   - 新增脚本：`scripts/phase7_pre_cutover_drill.py`
   - 演练链路：approval create/approve -> background task submit/wait -> rollback precheck
   - 默认输出：`docs/reports/phase7_pre_cutover_drill_latest.json`
   - 已写入文档：`docs/Phase7_切换评估与回退演练清单.md`
21. Phase 7 按场景灰度切换演练（先资料库 / 后流水线）：
   - 新增脚本：`scripts/phase7_canary_rollout_drill.py`
   - 灰度策略：library-first -> pipeline-second
   - 阶段失败自动停止推进并建议回退预案
   - 默认输出：`docs/reports/phase7_canary_rollout_latest.json`
   - 阶段子报告：
     - `docs/reports/phase7_canary_library_baseline.json`
     - `docs/reports/phase7_canary_pipeline_pre_cutover.json`
     - `docs/reports/phase7_canary_pipeline_rollback.json`
22. Phase 7 切换后观测指标与回退触发条件固化：
   - 新增观测守护脚本：`scripts/phase7_observability_guard.py`
   - 新增策略文件：`docs/phase7_observability_policy.json`
   - 新增规则文档：`docs/Phase7_观测指标与回退触发条件.md`
   - 默认输出：`docs/reports/phase7_observability_guard_latest.json`
23. Phase 7 切换评审材料模板（发布/回退决策记录）固化：
   - 新增模板总览文档：`docs/Phase7_切换评审材料模板.md`
   - 新增模板文件：
     - `docs/templates/Phase7_发布决策记录模板.md`
     - `docs/templates/Phase7_回退决策记录模板.md`
     - `docs/templates/Phase7_切换评审会议纪要模板.md`
   - 新增自动生成脚本：`scripts/phase7_generate_decision_pack.py`
   - 默认输出目录：`docs/reports/decision-pack/`
24. Phase 7 正式切换窗口方案与值班预案固化：
   - 新增方案文档：`docs/Phase7_正式切换窗口与值班预案.md`
   - 新增模板：`docs/templates/Phase7_正式切换窗口与值班预案模板.md`
   - 新增生成脚本：`scripts/phase7_generate_cutover_plan.py`
   - 默认输出目录：`docs/reports/cutover-plan/`
25. Phase 7 正式切换前一周演练节奏（每日检查项）固化：
   - 新增节奏文档：`docs/Phase7_切换前一周演练节奏.md`
   - 新增每日模板：`docs/templates/Phase7_每日演练检查项模板.md`
   - 新增生成脚本：`scripts/phase7_generate_weekly_drill_plan.py`
   - 默认输出目录：`docs/reports/weekly-drill/`
26. Phase 7 切换完成后复盘模板（问题分级与改进跟踪）固化：
   - 新增机制文档：`docs/Phase7_切换后复盘与改进跟踪.md`
   - 新增模板：
     - `docs/templates/Phase7_切换后复盘报告模板.md`
     - `docs/templates/Phase7_问题分级与改进跟踪模板.md`
     - `docs/templates/Phase7_复盘行动项台账模板.md`
   - 新增生成脚本：`scripts/phase7_generate_postmortem_pack.py`
   - 默认输出目录：`docs/reports/postmortem-pack/`
27. Phase 7 双周稳定性复评机制（持续观测）固化：
   - 新增机制文档：`docs/Phase7_双周稳定性复评机制.md`
   - 新增复评模板：`docs/templates/Phase7_双周稳定性复评模板.md`
   - 新增生成脚本：`scripts/phase7_biweekly_stability_review.py`
   - 默认输出：
     - `docs/reports/phase7_biweekly_stability_review_latest.json`
     - `docs/reports/phase7_biweekly_stability_review_latest.md`
28. Phase 7 季度回归审计机制（报告签核闭环）固化：
   - 新增机制文档：`docs/Phase7_季度回归审计机制.md`
   - 新增模板：
     - `docs/templates/Phase7_季度回归审计报告模板.md`
     - `docs/templates/Phase7_季度回归审计签核记录模板.md`
   - 新增生成脚本：`scripts/phase7_quarterly_regression_audit.py`
   - 默认输出：
     - `docs/reports/phase7_quarterly_regression_audit_latest.json`
     - `docs/reports/phase7_quarterly_regression_audit_latest.md`
     - `docs/reports/phase7_quarterly_regression_signoff_latest.md`
29. Phase 7 版本级变更审计与责任追踪机制固化：
   - 新增机制文档：`docs/Phase7_版本级变更审计与责任追踪机制.md`
   - 新增模板：
     - `docs/templates/Phase7_版本级变更审计模板.md`
     - `docs/templates/Phase7_版本责任追踪模板.md`
   - 新增生成脚本：`scripts/phase7_version_change_audit.py`
   - 默认输出：
     - `docs/reports/phase7_version_change_audit_latest.json`
     - `docs/reports/phase7_version_change_audit_latest.md`
     - `docs/reports/phase7_version_accountability_trace_latest.md`
30. Phase 7 演练与发布材料归档规范（目录与命名）固化：
   - 新增规范文档：`docs/Phase7_演练与发布材料归档规范.md`
   - 新增归档索引模板：`docs/templates/Phase7_归档索引模板.md`
   - 新增自动归档脚本：`scripts/phase7_archive_materials.py`
   - 默认归档目录：`docs/archive/phase7/<archive_id>/`
31. Phase 8-1 生产运行度量看板（SLO/错误预算/容量）固化：
   - 新增机制文档：`docs/Phase8_生产运行度量看板固化.md`
   - 新增模板：`docs/templates/Phase8_生产运行度量看板模板.md`
   - 新增策略文件：`docs/phase8_ops_metrics_policy.json`
   - 新增生成脚本：`scripts/phase8_ops_metrics_dashboard.py`
   - 新增 Canvas 视图：`docs/Phase8_生产运行度量看板.canvas.tsx`
   - 默认输出：
     - `docs/reports/phase8_ops_metrics_dashboard_latest.json`
     - `docs/reports/phase8_ops_metrics_dashboard_latest.md`
32. Phase 8-2 跨版本依赖升级与兼容性回归流程固化：
   - 新增流程文档：`docs/Phase8_跨版本依赖升级与兼容性回归流程.md`
   - 新增模板：
     - `docs/templates/Phase8_依赖变更清单模板.json`
     - `docs/templates/Phase8_兼容性回归报告模板.md`
     - `docs/templates/Phase8_兼容性签核记录模板.md`
   - 新增执行脚本：`scripts/phase8_dependency_compat_regression.py`
   - 默认输出：
     - `docs/reports/phase8_dependency_compat_latest.json`
     - `docs/reports/phase8_dependency_compat_latest.md`
     - `docs/reports/phase8_dependency_compat_signoff_latest.md`
33. Phase 8-3 生产告警分层与 on-call 响应手册固化：
   - 新增机制文档：`docs/Phase8_生产告警分层与OnCall响应手册.md`
   - 新增策略文件：`docs/phase8_alert_policy.json`
   - 新增模板：
     - `docs/templates/Phase8_OnCall响应手册模板.md`
     - `docs/templates/Phase8_OnCall交接模板.md`
   - 新增生成脚本：`scripts/phase8_generate_oncall_handbook.py`
   - 默认输出：
     - `docs/reports/phase8_oncall_handbook_latest.json`
     - `docs/reports/phase8_oncall_handbook_latest.md`
     - `docs/reports/phase8_oncall_handoff_latest.md`
34. Phase 8-4 多环境发布波次与容量回压机制固化：
   - 新增机制文档：`docs/Phase8_多环境发布波次与容量回压机制.md`
   - 新增策略文件：`docs/phase8_rollout_backpressure_policy.json`
   - 新增模板：
     - `docs/templates/Phase8_发布波次与回压计划模板.md`
     - `docs/templates/Phase8_发布波次执行记录模板.md`
   - 新增执行脚本：`scripts/phase8_wave_rollout_backpressure.py`
   - 默认输出：
     - `docs/reports/phase8_wave_rollout_backpressure_latest.json`
     - `docs/reports/phase8_wave_rollout_backpressure_latest.md`
     - `docs/reports/phase8_wave_rollout_execution_latest.md`
35. Phase 8-5 故障演练自动评分与改进闭环固化：
   - 新增机制文档：`docs/Phase8_故障演练自动评分与改进闭环.md`
   - 新增策略文件：`docs/phase8_drill_scoring_policy.json`
   - 新增模板：
     - `docs/templates/Phase8_故障演练评分报告模板.md`
     - `docs/templates/Phase8_改进行动闭环台账模板.md`
   - 新增执行脚本：`scripts/phase8_fault_drill_scoring.py`
   - 默认输出：
     - `docs/reports/phase8_fault_drill_scoring_latest.json`
     - `docs/reports/phase8_fault_drill_scoring_latest.md`
     - `docs/reports/phase8_fault_drill_improvement_ledger_latest.md`
36. Phase 8-6 跨团队发布节奏协同与冲突仲裁机制固化：
   - 新增机制文档：`docs/Phase8_跨团队发布节奏协同与冲突仲裁机制.md`
   - 新增策略文件：`docs/phase8_team_release_policy.json`
   - 新增模板：
     - `docs/templates/Phase8_跨团队发布申请模板.json`
     - `docs/templates/Phase8_跨团队发布协调纪要模板.md`
   - 新增执行脚本：`scripts/phase8_release_cadence_arbitration.py`
   - 默认输出：
     - `docs/reports/phase8_release_cadence_arbitration_latest.json`
     - `docs/reports/phase8_release_cadence_arbitration_latest.md`
37. Phase 9-1 全链路自动编排与每日巡检批任务固化：
   - 新增机制文档：`docs/Phase9_全链路自动编排与每日巡检.md`
   - 新增模板：`docs/templates/Phase9_每日巡检批任务报告模板.md`
   - 新增执行脚本：`scripts/phase9_daily_operations_bundle.py`
   - 默认输出：
     - `docs/reports/phase9_daily_ops_bundle_latest.json`
     - `docs/reports/phase9_daily_ops_bundle_latest.md`
38. Phase 9-2 管理驾驶舱周报自动化：
   - 新增机制文档：`docs/Phase9_管理驾驶舱周报自动化.md`
   - 新增策略文件：`docs/phase9_executive_weekly_policy.json`
   - 新增模板：`docs/templates/Phase9_管理驾驶舱周报模板.md`
   - 新增执行脚本：`scripts/phase9_generate_executive_weekly_report.py`
   - 默认输出：
     - `docs/reports/phase9_executive_weekly_latest.json`
     - `docs/reports/phase9_executive_weekly_latest.md`
39. Phase 9-3 策略漂移检测与阈值自适应建议机制固化：
   - 新增机制文档：`docs/Phase9_策略漂移检测与阈值自适应建议.md`
   - 新增策略文件：`docs/phase9_drift_policy.json`
   - 新增模板：`docs/templates/Phase9_策略漂移检测报告模板.md`
   - 新增执行脚本：`scripts/phase9_policy_drift_advisor.py`
   - 默认输出：
     - `docs/reports/phase9_policy_drift_latest.json`
     - `docs/reports/phase9_policy_drift_latest.md`
40. Phase 9-4 多周期运营复盘与预算规划联动机制固化：
   - 新增机制文档：`docs/Phase9_多周期运营复盘与预算规划联动.md`
   - 新增策略文件：`docs/phase9_budget_linkage_policy.json`
   - 新增模板：`docs/templates/Phase9_多周期运营复盘与预算联动报告模板.md`
   - 新增执行脚本：`scripts/phase9_ops_retro_budget_linkage.py`
   - 默认输出：
     - `docs/reports/phase9_ops_budget_linkage_latest.json`
     - `docs/reports/phase9_ops_budget_linkage_latest.md`
41. Phase 10-1 质量门禁规则即代码固化：
   - 新增机制文档：`docs/Phase10_治理规则即代码与审计导出.md`
   - 新增策略文件：`docs/phase10_quality_gate_policy.json`
   - 新增模板：`docs/templates/Phase10_质量门禁评估报告模板.md`
   - 新增执行脚本：`scripts/phase10_quality_gate.py`
   - 默认输出：
     - `docs/reports/phase10_quality_gate_latest.json`
     - `docs/reports/phase10_quality_gate_latest.md`
42. Phase 10-2 产物链路索引与可追溯清单固化：
   - 新增模板：`docs/templates/Phase10_产物索引报告模板.md`
   - 新增执行脚本：`scripts/phase10_artifact_lineage_index.py`
   - 默认输出：
     - `docs/reports/phase10_artifact_index_latest.json`
     - `docs/reports/phase10_artifact_index_latest.md`
43. Phase 10-3 DR 演练场景自动回放固化：
   - 新增场景模板：`docs/templates/Phase10_DR演练场景模板.json`
   - 新增执行脚本：`scripts/phase10_dr_scenario_replay.py`
   - 默认输出：
     - `docs/reports/phase10_dr_replay_latest.json`
44. Phase 10-4 审计包一键导出固化：
   - 新增导出模板：`docs/templates/Phase10_审计导出清单模板.json`
   - 新增执行脚本：`scripts/phase10_export_audit_bundle.py`
   - 默认输出目录：
     - `docs/reports/phase10_audit_bundle/<bundle_id>/`
45. Phase 11-1 发布策略自动学习固化：
   - 新增机制文档：`docs/Phase11_发布策略学习与收益评估.md`
   - 新增策略文件：`docs/phase11_strategy_learning_policy.json`
   - 新增模板：`docs/templates/Phase11_发布策略学习报告模板.md`
   - 新增执行脚本：`scripts/phase11_release_strategy_learning.py`
   - 默认输出：
     - `docs/reports/phase11_strategy_learning_latest.json`
     - `docs/reports/phase11_strategy_learning_latest.md`
46. Phase 11-2 异常根因聚类固化：
   - 新增模板：`docs/templates/Phase11_异常根因聚类报告模板.md`
   - 新增执行脚本：`scripts/phase11_incident_rootcause_cluster.py`
   - 默认输出：
     - `docs/reports/phase11_rootcause_cluster_latest.json`
     - `docs/reports/phase11_rootcause_cluster_latest.md`
47. Phase 11-3 变更收益评估固化：
   - 新增模板：`docs/templates/Phase11_变更收益评估报告模板.md`
   - 新增执行脚本：`scripts/phase11_change_benefit_evaluator.py`
   - 默认输出：
     - `docs/reports/phase11_change_benefit_latest.json`
     - `docs/reports/phase11_change_benefit_latest.md`
48. Phase 12-1 自愈闭环执行编排固化：
   - 新增机制文档：`docs/Phase12_自愈与阈值自动调优.md`
   - 新增策略文件：`docs/phase12_self_heal_policy.json`
   - 新增模板：`docs/templates/Phase12_自愈闭环执行报告模板.md`
   - 新增执行脚本：`scripts/phase12_self_heal_orchestrator.py`
   - 默认输出：
     - `docs/reports/phase12_self_heal_latest.json`
     - `docs/reports/phase12_self_heal_latest.md`
49. Phase 12-2 阈值自动调参提案固化：
   - 新增机制文档：`docs/Phase12_自愈与阈值自动调优.md`
   - 新增策略文件：`docs/phase12_threshold_tuning_policy.json`
   - 新增模板：`docs/templates/Phase12_阈值调参提案模板.md`
   - 新增执行脚本：`scripts/phase12_threshold_tuning_proposal.py`
   - 默认输出：
     - `docs/reports/phase12_threshold_tuning_latest.json`
     - `docs/reports/phase12_threshold_tuning_latest.md`
50. Phase 12-3 预测性容量与风险窗口建议固化：
   - 新增机制文档：`docs/Phase12_预测与统一趋势驾驶舱.md`
   - 新增策略文件：`docs/phase12_forecast_policy.json`
   - 新增模板：`docs/templates/Phase12_预测性容量与风险窗口报告模板.md`
   - 新增执行脚本：`scripts/phase12_capacity_risk_forecast.py`
   - 默认输出：
     - `docs/reports/phase12_capacity_forecast_latest.json`
     - `docs/reports/phase12_capacity_forecast_latest.md`
51. Phase 12-4 统一运营驾驶舱趋势视图固化：
   - 新增机制文档：`docs/Phase12_预测与统一趋势驾驶舱.md`
   - 新增模板：`docs/templates/Phase12_统一运营驾驶舱趋势报告模板.md`
   - 新增执行脚本：`scripts/phase12_unified_dashboard_trend.py`
   - 新增 Canvas：`docs/Phase12_统一运营驾驶舱趋势.canvas.tsx`
   - 默认输出：
     - `docs/reports/phase12_unified_dashboard_trend_latest.json`
     - `docs/reports/phase12_unified_dashboard_trend_latest.md`
52. Phase 13-1 模型运行时最小闭环（providers/router/timeout）：
   - 新增模块：
     - `quantamind_v2/runtimes/models/providers.py`
     - `quantamind_v2/runtimes/models/policies.py`
     - `quantamind_v2/runtimes/models/timeouts.py`
     - `quantamind_v2/runtimes/models/router.py`
     - `quantamind_v2/runtimes/models/client_openai_compat.py`
     - `quantamind_v2/runtimes/models/client_ollama.py`
   - 网关新增接口：
     - `GET /api/v2/models/providers`
     - `POST /api/v2/models/infer`
   - 新增测试：
     - `tests/v2/test_model_runtime.py`
     - `tests/v2/test_gateway_models.py`
53. Phase 13-2 MCP 运行时最小闭环（host/client/registry）：
   - 新增模块：
     - `quantamind_v2/runtimes/mcp/registry.py`
     - `quantamind_v2/runtimes/mcp/client.py`
     - `quantamind_v2/runtimes/mcp/adapters.py`
     - `quantamind_v2/runtimes/mcp/host.py`
   - 网关新增接口：
     - `GET /api/v2/mcp/tools`
     - `POST /api/v2/mcp/invoke`
   - 新增测试：
     - `tests/v2/test_mcp_runtime.py`
     - `tests/v2/test_gateway_mcp.py`
54. Phase 13-3 memory 适配层（project/run/artifact）：
   - 新增模块：
     - `quantamind_v2/memory/project_memory.py`
     - `quantamind_v2/memory/run_memory.py`
     - `quantamind_v2/memory/artifact_memory.py`
     - `quantamind_v2/memory/sync.py`
   - 网关新增接口：
     - `POST /api/v2/memory/projects/{project_id}/notes`
     - `GET /api/v2/memory/projects/{project_id}`
     - `POST /api/v2/memory/sync/runs/{run_id}`
     - `GET /api/v2/memory/runs/{run_id}`
     - `POST /api/v2/memory/sync/artifacts/{artifact_id}`
     - `GET /api/v2/memory/artifacts/{artifact_id}`
     - `GET /api/v2/memory/artifacts?run_id=...`
   - 新增测试：
     - `tests/v2/test_memory_sync.py`
     - `tests/v2/test_gateway_memory.py`
55. Phase 13-4 `core/planning` 最小闭环（intent/plan_builder/heuristics）：
   - 新增模块：
     - `quantamind_v2/core/planning/intent.py`
     - `quantamind_v2/core/planning/heuristics.py`
     - `quantamind_v2/core/planning/plan_builder.py`
   - 协同规划接入：
     - `quantamind_v2/core/coordination/planner.py` 改为复用 `PlanBuilder`
   - 网关新增接口：
     - `POST /api/v2/planning/preview`
   - 新增测试：
     - `tests/v2/test_planning.py`
     - `tests/v2/test_gateway_planning_integrations.py`
56. Phase 13-5 `integrations` 首批适配壳（filesystem/knowledge）：
   - 新增模块：
     - `quantamind_v2/integrations/filesystem/adapter.py`
     - `quantamind_v2/integrations/knowledge/adapter.py`
   - 网关新增接口：
     - `GET /api/v2/integrations/filesystem/list`
     - `GET /api/v2/integrations/filesystem/read`
     - `POST /api/v2/integrations/knowledge/index`
     - `GET /api/v2/integrations/knowledge/search`
   - 新增测试：
     - `tests/v2/test_gateway_planning_integrations.py`
57. Phase 14-1 配置统一层（config）：
   - 新增模块：
     - `quantamind_v2/config/feature_flags.py`
     - `quantamind_v2/config/runtime_limits.py`
     - `quantamind_v2/config/providers.py`
     - `quantamind_v2/config/settings.py`
     - `quantamind_v2/config/compatibility.py`
     - `quantamind_v2/config/__init__.py`
   - 网关接入：
     - `create_app(settings=...)` 支持注入配置
     - `GET /api/v2/config/summary` 提供只读配置摘要
   - 规划文档：
     - `docs/Phase14_实施草案.md`
   - 新增测试：
     - `tests/v2/test_config_settings.py`
     - `tests/v2/test_gateway_config.py`
58. Phase 14-2 `agents` 能力画像首版（registry/base/policies）：
   - 新增模块：
     - `quantamind_v2/agents/base.py`
     - `quantamind_v2/agents/registry.py`
     - `quantamind_v2/agents/policies.py`
     - `quantamind_v2/agents/__init__.py`
   - 规划链路接入：
     - `quantamind_v2/core/planning/plan_builder.py` 引入 agent selection
     - `quantamind_v2/core/coordination/planner.py` 支持注入 plan_builder
   - 网关新增接口：
     - `GET /api/v2/agents/profiles`
   - 新增测试：
     - `tests/v2/test_agents.py`
     - `tests/v2/test_gateway_agents.py`
59. Phase 14-3 `client/shared` 共享状态契约（run/task/artifact）：
   - 新增模块：
     - `quantamind_v2/client/shared/models.py`
     - `quantamind_v2/client/shared/normalizers.py`
   - 网关新增接口：
     - `GET /api/v2/client/shared/state`
   - Desktop 壳接入：
     - `quantamind_v2/client/desktop/shell.py` 优先读取 shared state
   - 新增测试：
     - `tests/v2/test_client_shared.py`
     - `tests/v2/test_gateway_client_shared.py`
60. Phase 14-4 拆分 `core/gateway` 路由模块（routes_*）：
   - 新增模块：
     - `quantamind_v2/core/gateway/deps.py`
     - `quantamind_v2/core/gateway/schemas.py`
     - `quantamind_v2/core/gateway/routes_core.py`
     - `quantamind_v2/core/gateway/routes_runs_artifacts.py`
     - `quantamind_v2/core/gateway/routes_runtime.py`
     - `quantamind_v2/core/gateway/routes_memory_planning_integrations.py`
     - `quantamind_v2/core/gateway/routes_workflows.py`
   - 入口重构：
     - `quantamind_v2/core/gateway/app.py` 收敛为依赖装配 + router include
   - 兼容性目标：
     - 保持现有 `api/v2/*` 路径与响应结构不变（回归测试覆盖）
61. Phase 15-1 客户端工作区布局管理（Web/Desktop 共享）：
   - 新增模块：
     - `quantamind_v2/client/shared/workspace.py`
     - `quantamind_v2/core/gateway/routes_client_workspace.py`
   - 网关新增接口：
     - `GET /api/v2/client/workspace/layouts`
     - `GET /api/v2/client/workspace/layouts/{layout_id}`
     - `POST /api/v2/client/workspace/layouts`
     - `POST /api/v2/client/workspace/layouts/{layout_id}/activate`
     - `GET /api/v2/client/workspace/active-layout`
     - `GET /api/v2/client/workspace/snapshot`
   - 规划文档：
     - `docs/Phase15_实施草案.md`
   - 新增测试：
     - `tests/v2/test_client_workspace_layouts.py`
     - `tests/v2/test_gateway_client_workspace.py`
62. Phase 15-2 Desktop 交互深化（active layout 渲染与 panel 刷新策略）：
   - Desktop 壳升级：
     - `quantamind_v2/client/desktop/models.py` 新增 active layout 字段
     - `quantamind_v2/client/desktop/shell.py` 支持 active layout 渲染与 panel 级刷新策略
   - 兼容性策略：
     - 优先读取 `workspace snapshot`，失败时回退旧接口链路
   - 新增测试：
     - `tests/v2/test_desktop_workspace_shell.py`
63. Phase 15-3 Web/Desktop 偏好同步（布局与快捷项）：
   - 新增模块：
     - `quantamind_v2/client/shared/preferences.py`
   - 网关新增接口：
     - `GET /api/v2/client/preferences/{profile_id}`
     - `POST /api/v2/client/preferences/{profile_id}/shortcuts`
     - `POST /api/v2/client/preferences/{profile_id}/sync-layouts`
   - 工作区接口增强：
     - `activate/active-layout/snapshot` 支持 `profile_id` 维度
   - 新增测试：
     - `tests/v2/test_client_preferences.py`
     - `tests/v2/test_gateway_client_workspace.py`（新增偏好同步用例）
64. Phase 15-4 工作台恢复点（run/task/artifact 定位上下文）：
   - 新增模块：
     - `quantamind_v2/client/shared/recovery.py`
   - 网关新增接口：
     - `POST /api/v2/client/workspace/recovery-points`
     - `GET /api/v2/client/workspace/recovery-points`
     - `GET /api/v2/client/workspace/recovery-points/latest`
     - `POST /api/v2/client/workspace/recovery-points/{point_id}/activate`
   - 工作区快照增强：
     - `GET /api/v2/client/workspace/snapshot` 返回 `latest_recovery_point`
   - 新增测试：
     - `tests/v2/test_client_workspace_recovery.py`
     - `tests/v2/test_gateway_client_workspace.py`（新增恢复点流程用例）
65. Phase 16-1 多端会话 Presence 与 Lease（session 协同首版）：
   - 新增模块：
     - `quantamind_v2/core/sessions/manager.py`
     - `quantamind_v2/core/sessions/storage.py`
     - `quantamind_v2/core/sessions/transcript.py`
   - 网关新增接口：
     - `GET /api/v2/sessions`
     - `POST /api/v2/sessions/leases`
     - `GET /api/v2/sessions/{session_id}`
     - `POST /api/v2/sessions/{session_id}/heartbeat`
     - `POST /api/v2/sessions/{session_id}/release`
     - `GET /api/v2/sessions/{session_id}/events`
   - 网关接入：
     - `quantamind_v2/core/gateway/routes_sessions.py`
     - `quantamind_v2/core/gateway/app.py` 挂载 sessions router
   - 规划文档：
     - `docs/Phase16_实施草案.md`
   - 新增测试：
     - `tests/v2/test_sessions_presence.py`
     - `tests/v2/test_gateway_sessions.py`
66. Phase 16-2 会话级事件轨迹增强与多端操作审计：
   - 会话事件模型增强：
     - `quantamind_v2/core/sessions/transcript.py` 增加 `event_id/actor/operation/target/source/severity/tags`
     - 支持按 `event_type/source/operation` 过滤查询与全局审计检索
   - 网关新增审计接口：
     - `GET /api/v2/sessions/audit/events`
     - `GET /api/v2/sessions/audit/export`
   - 工作台操作审计接入：
     - `routes_client_workspace.py` 在 layout/shortcuts/recovery 关键操作写入 `source=workspace` 审计事件
   - 新增测试：
     - `tests/v2/test_gateway_sessions.py`（审计查询/导出）
     - `tests/v2/test_gateway_client_workspace.py`（workspace 审计链路）
67. Phase 16-3 工作台与会话联动（snapshot 暴露 active sessions）：
   - 工作区快照增强：
     - `GET /api/v2/client/workspace/snapshot` 新增 `session_presence`
     - 包含 `active_total/by_client_type/expiring_soon_count/items`
   - 目标：
     - 支持 Web/Desktop 在同一 profile 下识别在线协同端与即将到期会话
   - 新增测试：
     - `tests/v2/test_gateway_client_workspace.py`（session presence 断言）
68. Phase 16-4 多端并发策略（同 profile 冲突约束）：
   - 会话并发策略：
     - `core/sessions/manager.py` 引入 `access_mode=reader|writer`
     - 同 profile 强制单 writer；冲突返回 `SessionConflictError`
     - 支持 `allow_handover` 抢占并自动释放旧 writer
   - 网关行为：
     - `POST /api/v2/sessions/leases` 支持 `access_mode/allow_handover`
     - writer 冲突返回 `409`
   - 审计增强：
     - 新增 `session.open.conflict` 与 `session.open.handover` 事件
   - 新增测试：
     - `tests/v2/test_sessions_presence.py`
     - `tests/v2/test_gateway_sessions.py`
69. Phase 16 收口（会话并发约束落到工作台写操作）：
   - 工作台写操作接入 writer lock：
     - `POST /api/v2/client/workspace/layouts/{layout_id}/activate`
     - `POST /api/v2/client/preferences/{profile_id}/shortcuts`
     - `POST /api/v2/client/preferences/{profile_id}/sync-layouts`
     - `POST /api/v2/client/workspace/recovery-points`
     - `POST /api/v2/client/workspace/recovery-points/{point_id}/activate`
   - 规则：
     - 若 profile 下存在活跃 writer，会话写操作必须携带且匹配该 writer `session_id`
     - 不满足条件返回 `409`
   - 审计增强：
     - 新增 `workspace_write_conflict` 事件（`operation=workspace.write.conflict`）
   - 新增测试：
     - `tests/v2/test_gateway_client_workspace.py`
70. Phase 17-1 协同调度策略深化（任务优先级 + 预算感知）：
   - 规划输入增强：
     - `POST /api/v2/planning/preview` 支持 `priority`、`budget_seconds`
   - 规划信号增强：
     - `core/planning/heuristics.py` 增加 `requested_priority/effective_priority/budget_risk/budget_seconds`
     - `core/planning/plan_builder.py` 增加 `scheduling` 输出（含 `queue_hint` 与 `strategy`）
   - 调度链路接入：
     - `core/coordination/planner.py` 支持透传优先级与预算参数
   - 新增测试：
     - `tests/v2/test_planning.py`
     - `tests/v2/test_gateway_planning_integrations.py`
71. Phase 17-2 调度冲突治理（同 profile 并行协同冲突检测 + 降级策略）：
   - 新增模块：
     - `quantamind_v2/core/coordination/scheduling.py`
   - 协同执行增强：
     - `POST /api/v2/coordination/execute` 支持 `profile_id/conflict_strategy`
     - 冲突策略：
       - `queue`：排队（返回 queued run）
       - `reject`：拒绝（`409`）
       - `degrade_single_agent`：自动降级为 single-agent
   - 调度链路接入：
     - `core/coordination/supervisor.py` 支持 `forced_mode`
   - 新增测试：
     - `tests/v2/test_coordination.py`
     - `tests/v2/test_gateway_coordination.py`
72. Phase 17-3 调度可观测性增强（冲突决策审计与导出）：
   - 新增模块：
     - `quantamind_v2/core/coordination/audit.py`
   - 审计沉淀：
     - `POST /api/v2/coordination/execute` 在冲突检测与策略命中路径统一写入结构化调度审计
     - 字段覆盖 `detected/conflict_run_id/strategy/outcome/reason/route_mode`
   - 新增接口：
     - `GET /api/v2/coordination/audit/events`
     - `GET /api/v2/coordination/audit/export`
   - 新增测试：
     - `tests/v2/test_coordination.py`
     - `tests/v2/test_gateway_coordination.py`
73. Phase 17 收口（调度策略参数统一配置 + 运行手册）：
   - 配置统一：
     - `quantamind_v2/config/coordination.py` 新增 `CoordinationPolicySettings`
     - `AppSettings` 新增 `coordination` 段
   - 配置生效点：
     - 默认冲突策略：`default_conflict_strategy`
     - 导出上限：`audit_export_limit_max`
     - 审计保留：`audit_retention_max_events`
   - 手册：
     - `docs/Phase17_调度策略运行手册.md`
   - 新增测试：
     - `tests/v2/test_config_settings.py`
     - `tests/v2/test_gateway_config.py`
     - `tests/v2/test_gateway_coordination.py`
74. Phase 18-1 持久化与跨进程一致性（调度审计/策略覆盖）：
   - 新增模块：
     - `quantamind_v2/core/coordination/persistence.py`
   - 持久化能力：
     - 审计持久化：`coordination_audit.jsonl`
     - 策略持久化：`coordination_policy.json`
   - 网关增强：
     - `POST /api/v2/coordination/execute` 未传 `conflict_strategy` 时优先读取 profile 持久化覆盖
     - 新增接口：
       - `GET /api/v2/coordination/policies/conflict-strategy`
       - `POST /api/v2/coordination/policies/conflict-strategy`
   - 配置增强：
     - `AppSettings.coordination.state_dir`
   - 新增测试：
     - `tests/v2/test_coordination_persistence.py`
     - `tests/v2/test_gateway_coordination.py`
75. Phase 18-2 一致性与恢复（轮转/裁剪 + 启动恢复 + 健康自检）：
   - 存储恢复增强：
     - `FileBackedCoordinationAuditStore` 支持启动/写入 compact 与坏行恢复
     - `FileBackedCoordinationPolicyStore` 支持破损 JSON 启动恢复
   - 轮转/裁剪策略：
     - 超保留上限自动裁剪为最新窗口
     - 恢复前生成 `.bak` 备份
   - 新增接口：
     - `GET /api/v2/coordination/persistence/health`
   - 新增测试：
     - `tests/v2/test_coordination_persistence.py`
     - `tests/v2/test_gateway_coordination.py`
76. Phase 18-3 归档与迁移草案（大小/时间轮转 + 归档索引 + DB 预案）：
   - 轮转策略：
     - `audit_rotate_max_bytes`（按大小）
     - `audit_rotate_interval_seconds`（按时间）
   - 归档索引：
     - `coordination_audit_archives.json`
     - 新增接口：`GET /api/v2/coordination/persistence/archives`
   - 数据库迁移预案：
     - 新增接口：`GET /api/v2/coordination/persistence/migration-plan`
     - 新增文档：`docs/Phase18_数据库迁移预案草案.md`
   - 新增测试：
     - `tests/v2/test_coordination_persistence.py`
     - `tests/v2/test_gateway_coordination.py`
     - `tests/v2/test_config_settings.py`
     - `tests/v2/test_gateway_config.py`
77. Phase 18 收口（统一观测面板 + 告警阈值建议）：
   - 新增接口：
     - `GET /api/v2/coordination/persistence/dashboard`
   - 统一指标：
     - 轮转（size/time）与恢复（status/invalid lines）指标
     - 归档（latest/total）指标
     - 策略覆盖（profiles_count）指标
   - 告警建议：
     - 输出 `alerts` 与 `thresholds`
   - 新增测试：
     - `tests/v2/test_gateway_coordination.py`
78. Phase 19-1 数据库 dual-write 基线（文件主写 + SQLite 次写）：
   - 新增模块能力：
     - `SQLiteCoordinationAuditStore`
     - `SQLiteCoordinationPolicyStore`
     - `DualWriteCoordinationAuditStore`
     - `DualWriteCoordinationPolicyStore`
   - 配置增强：
     - `coordination.dual_write_enabled`
     - `coordination.database_path`
   - 装配策略：
     - `create_app` 在开关开启时启用 dual-write
     - 读路径保持文件优先，写路径同步写 SQLite
   - 新增测试：
     - `tests/v2/test_coordination_persistence.py`
     - `tests/v2/test_gateway_coordination.py`
     - `tests/v2/test_config_settings.py`
     - `tests/v2/test_gateway_config.py`
   - 规划文档：
     - `docs/Phase19_实施草案.md`
79. Phase 19-2 对账与一致性校验接口（文件 vs SQLite）：
   - 新增对账能力：
     - 审计窗口对账（差异统计 + 异常样本）
     - 策略覆盖对账（profile 维度差异统计）
   - 新增接口：
     - `GET /api/v2/coordination/persistence/consistency`
   - 观测增强：
     - `GET /api/v2/coordination/persistence/dashboard` 在 dual-write 模式附带 `consistency`
   - 新增测试：
     - `tests/v2/test_coordination_persistence.py`
     - `tests/v2/test_gateway_coordination.py`
80. Phase 19-3 cutover 预演（数据库优先读 + 回退策略 + 演练接口）：
   - 新增配置：
     - `coordination.database_read_preferred`
     - `coordination.database_read_fallback_to_file`
   - 读路径升级：
     - dual-write 模式下支持 SQLite 优先读
     - 读失败按策略回退文件读
   - 新增接口：
     - `GET /api/v2/coordination/persistence/cutover/drill`
   - 新增测试：
     - `tests/v2/test_coordination_persistence.py`
     - `tests/v2/test_gateway_coordination.py`
     - `tests/v2/test_config_settings.py`
     - `tests/v2/test_gateway_config.py`
81. Phase 20-1 数据库优先读灰度（白名单 + 比例策略）：
   - 新增配置：
     - `coordination.database_read_profile_allowlist`
     - `coordination.database_read_rollout_percentage`
   - 路由策略：
     - 白名单优先命中 SQLite 读路径
     - 其余 profile 按稳定哈希 bucket 执行比例灰度
   - 观测增强：
     - `cutover/drill` 输出 `routing_reason` / `allowlist_hit` / `rollout_bucket`
   - 新增测试：
     - `tests/v2/test_coordination_persistence.py`
     - `tests/v2/test_gateway_coordination.py`
     - `tests/v2/test_config_settings.py`
     - `tests/v2/test_gateway_config.py`
   - 规划文档：
     - `docs/Phase20_实施草案.md`
82. Phase 20-2 灰度观测补强（profile 命中统计 + 覆盖率面板 + 回退异常计数）：
   - 新增运行时统计：
     - `read_observability.profile_hits`
     - `read_observability.database_coverage_ratio`
     - `read_observability.fallback_anomaly_count`
   - 观测出口增强：
     - `GET /api/v2/coordination/persistence/health`
     - `GET /api/v2/coordination/persistence/cutover/drill`
     - `GET /api/v2/coordination/persistence/dashboard`
   - 新增测试：
     - `tests/v2/test_coordination_persistence.py`
     - `tests/v2/test_gateway_coordination.py`
83. Phase 20-3 灰度控制面（运行时白名单 / 比例动态调整）：
   - 新增接口：
     - `GET /api/v2/coordination/persistence/cutover/controls`
     - `POST /api/v2/coordination/persistence/cutover/controls`
   - 支持动态调整：
     - `profile_allowlist`
     - `rollout_percentage`
   - 新增测试：
     - `tests/v2/test_coordination_persistence.py`
     - `tests/v2/test_gateway_coordination.py`
   - 规划文档：
     - `docs/Phase20_实施草案.md`

下一批优先项（建议按顺序）：

1. （Phase 20-4）灰度持久化：控制面配置跨进程保存与重启恢复

---

## 14. 结语

本路线图不是一次性“重写 QuantaMind”，而是一套面向成熟化演进的工程计划：

- 用 `V1` 保住当前业务能力
- 用 `V2` 建立下一代控制平面
- 通过阶段化试点把高风险问题逐步拆解

最终目标不是做一个“更复杂的聊天框”，而是做一个真正可协同、可审批、可追踪、可恢复、可复用的量子科研 AI 工作台。

