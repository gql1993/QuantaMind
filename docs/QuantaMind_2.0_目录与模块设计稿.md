# QuantaMind 2.0 目录与模块设计稿

**文档版本：** Draft 0.1  
**编制日期：** 2026-04-07  
**适用范围：** QuantaMind 2.0 架构演进、`v1-stable` 与 `v2-architecture` 并行开发  
**设计目标：** 在保留当前可运行版本的前提下，吸收 Claude Code 类系统在任务驱动、多智能体协同、上下文装配、工具执行与客户端工作台方面的成熟经验，将量智大脑演进为更稳定、可观测、可扩展的量子科研 AI 工作台。

---

## 1. 设计前提

### 1.1 当前版本（V1）定位

当前 QuantaMind 1.x 已具备以下基础能力：

- `FastAPI Gateway` 作为统一服务端入口
- `Brain + Orchestrator + Hands + Memory + Heartbeat` 的基本架构
- Web 客户端与桌面客户端雏形
- 多角色 Agent 团队
- 情报员、流水线、资料库、数据中台等业务能力
- PostgreSQL / pgvector / state store 等基础持久化能力

但当前版本仍存在以下典型问题：

- 对话入口承担了过多长任务执行压力
- 多智能体更多停留在“多角色单入口”，尚未形成显式协同控制平面
- 长任务缺少统一 Run 模型与 Artifact 视图
- 工具执行缺少统一分级运行时
- 上下文装配仍偏粗粒度
- 用户界面仍偏“聊天框”，而不是“工作台”

### 1.2 2.0 的核心目标

QuantaMind 2.0 不以“重写当前版本”为目标，而以“建立新一代控制平面与工作台壳层”为目标：

1. 从聊天驱动升级为任务驱动
2. 从单编排器升级为显式多智能体协同系统
3. 从临时字符串结果升级为 Artifact-first 产物系统
4. 从页面拼接状态升级为统一 Run Console
5. 从简单工具调用升级为分级 Tool Runtime
6. 从全量上下文喂给模型升级为 Context Assembler

### 1.3 设计原则

1. **V1 可运行优先**：2.0 独立演进，不破坏当前稳定版本。
2. **内核与壳层分离**：运行内核、客户端壳、领域适配器分开设计。
3. **任务一等公民**：所有长任务显式建模为 Run。
4. **协同显式建模**：多智能体协同单列为核心模块。
5. **高频路径走快捷通道**：将确定性强的高频任务从通用推理链中剥离。
6. **失败要可降级**：任何重任务都必须定义 timeout / fallback / retry / cancel 策略。
7. **用户看到过程**：不仅返回结果，还要暴露阶段、工具、产物、审批与日志。

---

## 2. 2.0 顶层目录建议

建议新增独立的 `quantamind_v2/` 目录作为 2.0 主代码区，保留现有 `quantamind/` 作为 1.x 线。

```text
QuantaMind/
├── quantamind/                         # V1 稳定线（现有系统）
├── quantamind_v2/                      # V2 架构演进主目录
│   ├── __init__.py
│   ├── config/
│   ├── contracts/
│   ├── core/
│   ├── agents/
│   ├── runtimes/
│   ├── shortcuts/
│   ├── artifacts/
│   ├── memory/
│   ├── integrations/
│   ├── services/
│   ├── client/
│   └── migration/
├── docs/
│   ├── QuantaMind_2.0_目录与模块设计稿.md
│   └── ...
├── tests/
│   ├── v1/
│   ├── v2/
│   └── integration/
└── services/
```

### 2.1 目录层级说明

- `quantamind/`
  - 保持当前系统稳定运行
  - 仅继续承接 bugfix、可靠性修复、小范围业务迭代

- `quantamind_v2/`
  - 作为 2.0 架构试验与新内核实现区
  - 允许和 V1 同仓并存
  - 逐步承接新 Run、协同、Artifact、客户端工作台能力

- `tests/v1` 与 `tests/v2`
  - 对两代系统分开验证，便于对比

---

## 3. 2.0 总体分层

2.0 建议采用“壳层 - 控制平面 - 执行平面 - 数据平面”四层结构。

```text
┌─────────────────────────────────────────────────────────┐
│ 壳层（Shell）                                           │
│ Desktop Workspace / Web Console / CLI / Embedded Panel │
├─────────────────────────────────────────────────────────┤
│ 控制平面（Control Plane）                               │
│ RunCoordinator / ContextAssembler / Coordination /      │
│ ApprovalRouter / ShortcutRegistry / SessionFacade       │
├─────────────────────────────────────────────────────────┤
│ 执行平面（Execution Plane）                             │
│ Tool Runtime / Model Runtime / MCP Runtime / Workers    │
├─────────────────────────────────────────────────────────┤
│ 数据平面（Data Plane）                                  │
│ Memory / Artifact Store / State Store / Event Log       │
│ Library / Knowledge / Warehouse / Reports               │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 2.0 核心目录与模块设计

## 4.1 `quantamind_v2/config/`

职责：

- 2.0 独立配置模型
- V1 / V2 配置兼容层
- 环境变量、用户配置、项目配置的合并
- feature flags、实验开关、运行预算配置

建议文件：

```text
config/
├── settings.py               # 总配置入口
├── feature_flags.py          # V2 Feature Flag
├── providers.py              # 模型 / 外部服务提供商配置
├── runtime_limits.py         # timeout / retry / budget 配置
└── compatibility.py          # 兼容 V1 配置读取
```

---

## 4.2 `quantamind_v2/contracts/`

职责：

- 所有跨模块的稳定契约
- Run / Event / Artifact / Approval / Tool / Context 的统一数据模型

建议文件：

```text
contracts/
├── run.py
├── event.py
├── artifact.py
├── approval.py
├── tool.py
├── context.py
└── client_api.py
```

这是 2.0 的基础，避免再次出现状态字段散落在：

- `chat_jobs`
- `pipelines`
- `tasks`
- `reports`

等多个结构中各自演化。

---

## 4.3 `quantamind_v2/core/`

这是 2.0 的核心控制平面。

```text
core/
├── gateway/
├── runs/
├── coordination/
├── context_assembler/
├── approvals/
├── sessions/
└── planning/
```

### A. `core/gateway/`

职责：

- 所有客户端入口
- 统一 API / WebSocket / SSE / daemon 入口
- 只做入站协议与响应组织，不承载长任务业务逻辑

建议文件：

```text
core/gateway/
├── app.py
├── routes_chat.py
├── routes_runs.py
├── routes_artifacts.py
├── routes_admin.py
└── transport.py
```

### B. `core/runs/`

职责：

- 统一 Run 模型
- 统一所有异步任务状态
- 所有长任务都注册为 `Run`

建议文件：

```text
core/runs/
├── coordinator.py           # RunCoordinator
├── lifecycle.py             # 状态流转
├── registry.py              # Run 注册表
├── persistence.py           # Run 状态持久化
├── events.py                # Run 事件生成
└── queries.py               # Run 查询接口
```

建议统一的 Run 类型：

- `chat_run`
- `digest_run`
- `pipeline_run`
- `import_run`
- `simulation_run`
- `calibration_run`
- `data_sync_run`
- `repair_run`

### C. `core/coordination/`

这是 2.0 必须新增的一等核心模块，也是你刚才特别指出的“多智能体协同模块”。

职责：

- 多智能体协同计划与调度
- 子智能体分派
- 父子 Run 关系
- 并行 / 串行 / 汇总策略

建议文件：

```text
core/coordination/
├── router.py                # 任务分流：单智能体 / 快捷路径 / 多智能体协同
├── planner.py               # 生成协同计划
├── delegation.py            # 派发子任务给子智能体
├── topology.py              # 父子 / 并行 / 串行 / merge 图
├── merger.py                # 汇总各子智能体结果
├── policies.py              # 协同约束、工具权限、预算继承
└── supervisor.py            # 协同监督 / 失败恢复 / 重试
```

这部分参考 Claude Code 的：

- `forkedAgent.ts`
- `task framework`
- `swarm / teammate`

但实现方式必须按 QuantaMind 自己的业务场景重写。

### D. `core/context_assembler/`

职责：

- 动态装配上下文
- 控制上下文预算
- 区分不同任务需要的上下文层

建议文件：

```text
core/context_assembler/
├── assembler.py
├── budgets.py
├── layers.py
├── sources.py
├── summarizer.py
└── cache_keys.py
```

建议上下文层：

- `system context`
- `agent identity context`
- `project memory context`
- `recent conversation context`
- `artifact context`
- `data snapshot context`
- `tool-result context`
- `policy / approval context`

### E. `core/approvals/`

职责：

- 统一审批模型
- 不同风险等级走不同审批 UI 和执行策略

建议文件：

```text
core/approvals/
├── router.py
├── policies.py
├── prompts.py
├── decisions.py
└── audit.py
```

建议审批类别：

- shell / process
- external delivery
- file mutation
- database mutation
- device command
- MES operation

### F. `core/sessions/`

职责：

- 会话与 Run 解耦
- 会话只作为用户交互容器
- Run 才是执行核心

建议文件：

```text
core/sessions/
├── manager.py
├── storage.py
└── transcript.py
```

### G. `core/planning/`

职责：

- 通用任务规划
- 对快捷路径与协同路径做优先级判断

建议文件：

```text
core/planning/
├── intent.py
├── plan_builder.py
└── heuristics.py
```

---

## 4.4 `quantamind_v2/agents/`

职责：

- 2.0 智能体定义
- 智能体身份、可用工具、可见上下文、可触发 shortcut、可参与的协同模式

建议结构：

```text
agents/
├── registry.py
├── base.py
├── profiles/
│   ├── intel_officer.py
│   ├── theorist.py
│   ├── process_engineer.py
│   ├── data_analyst.py
│   └── ...
└── policies.py
```

建议从“角色定义”升级为“能力画像”：

- 角色
- 允许工具
- 默认上下文层
- 允许快捷路径
- 协同参与方式
- 输出 artifact 类型

---

## 4.5 `quantamind_v2/runtimes/`

职责：

- 统一执行平面
- 把模型执行、工具执行、MCP 执行、子进程 / worker 执行解耦

建议结构：

```text
runtimes/
├── tools/
├── models/
├── workers/
├── mcp/
└── budgets/
```

### A. `runtimes/tools/`

建议文件：

```text
runtimes/tools/
├── executor.py              # ToolExecutor
├── registry.py
├── classes.py               # query / mutation / long_running / delivery
├── isolation.py             # thread / subprocess / worker
├── retries.py
├── cancellation.py
└── progress.py
```

这是对当前 `hands.py` 的升级版，不取代所有 `hands_*` 适配器，而是统一它们的运行方式。

### B. `runtimes/models/`

建议文件：

```text
runtimes/models/
├── router.py
├── providers.py
├── client_openai_compat.py
├── client_ollama.py
├── policies.py
└── timeouts.py
```

### C. `runtimes/workers/`

建议文件：

```text
runtimes/workers/
├── task_worker.py
├── long_jobs.py
├── shell_jobs.py
└── scheduler.py
```

### D. `runtimes/mcp/`

职责：

- 为 2.0 预留远程工具总线
- 外部工具、实验服务、知识服务、设备服务可统一纳入 MCP Host / Client 模型

建议文件：

```text
runtimes/mcp/
├── host.py
├── client.py
├── registry.py
└── adapters.py
```

---

## 4.6 `quantamind_v2/shortcuts/`

职责：

- 高频、确定性、稳定性优先的指令绕过通用推理链
- 这是从 Claude Code command / shortcut 思想借鉴来的重要模块

建议结构：

```text
shortcuts/
├── registry.py
├── matcher.py
├── policies.py
├── handlers/
│   ├── intel_today.py
│   ├── system_status.py
│   ├── db_status.py
│   ├── latest_reports.py
│   ├── latest_runs.py
│   └── yield_summary.py
```

典型快捷路径：

- 发送今天情报
- 查看今日日报
- 检查 gateway 状态
- 查看数据库状态
- 最近任务
- 最近流水线
- 最近良率

---

## 4.7 `quantamind_v2/artifacts/`

职责：

- 将所有关键结果做成一等产物
- 对话只是产物入口，不是产物本体

建议结构：

```text
artifacts/
├── store.py
├── schema.py
├── renderers/
│   ├── report_renderer.py
│   ├── digest_renderer.py
│   ├── pipeline_renderer.py
│   ├── chart_renderer.py
│   └── summary_renderer.py
├── exporters/
└── viewers/
```

Artifact 类型建议：

- `intel_report`
- `track_report`
- `pipeline_report`
- `simulation_report`
- `measurement_report`
- `db_diagnosis`
- `approval_record`
- `library_ingest_report`

---

## 4.8 `quantamind_v2/memory/`

职责：

- 2.0 记忆与知识层
- 与 Artifact、Run、Project、Knowledge、Vector 检索打通

建议结构：

```text
memory/
├── project_memory.py
├── run_memory.py
├── artifact_memory.py
├── knowledge/
├── vector/
└── sync.py
```

这里建议不要直接推翻当前 `memory.py / knowledge_base.py / state_store.py`，而是先加一层 2.0 适配壳。

---

## 4.9 `quantamind_v2/integrations/`

职责：

- 保留量智大脑独有的量子科研领域适配器
- 这是 QuantaMind 与 Claude Code 的根本差异所在

建议结构：

```text
integrations/
├── qeda/
├── mes/
├── measurement/
├── warehouse/
├── knowledge/
├── feishu/
└── filesystem/
```

其中：

- `qeda/`：设计与版图
- `mes/`：制造与设备
- `measurement/`：ARTIQ / Pulse / 校准
- `warehouse/`：数据中台 / SQL / ETL
- `feishu/`：外部推送

---

## 4.10 `quantamind_v2/services/`

职责：

- 面向业务能力的服务层
- 不直接暴露给客户端，而是被 Run / Shortcut / Coordination 调用

建议结构：

```text
services/
├── intel_service.py
├── pipeline_service.py
├── library_service.py
├── simulation_service.py
├── calibration_service.py
├── system_service.py
└── reporting_service.py
```

---

## 4.11 `quantamind_v2/client/`

2.0 客户端建议采用“壳层”设计，而不是继续把前端当成简单页面集合。

```text
client/
├── shared/
├── web/
├── desktop/
├── cli/
└── embedded/
```

### A. `client/shared/`

职责：

- 前端共享状态模型
- Run 状态渲染逻辑
- Approval / Artifact / Shortcut 的通用组件契约

### B. `client/web/`

定位：

- 看板、审批、资料浏览、运行监控、轻量操作

### C. `client/desktop/`

定位：

- 2.0 主力工作台
- 适合承载多面板、多任务、审批、artifact 浏览、拖拽导入、本地工具入口

### D. `client/cli/`

定位：

- 工程师调试与自动化入口

### E. `client/embedded/`

定位：

- Q-EDA / 实验软件内嵌面板

---

## 5. 多智能体协同模块设计（重点）

这是 2.0 必须单列的一级模块。

## 5.1 当前问题

当前 V1 里虽然有多个 Agent，但协同更多是：

- 一个 orchestrator
- 路由到一个 agent
- agent 在工具循环中完成任务

这还不是真正的多智能体协同系统。

## 5.2 2.0 目标

2.0 中的多智能体协同应具备：

1. 父任务 / 子任务关系
2. 并行与串行执行拓扑
3. 子智能体独立上下文装配
4. 子智能体独立权限边界
5. 子任务 artifact 独立保存
6. 聚合器负责汇总结果
7. UI 可视化展示协同图

## 5.3 协同角色

建议角色分层：

- `Coordinator`
- `Planner`
- `SpecialistAgent`
- `Executor`
- `Merger`

示例：

- 今日情报日报
  - Coordinator：识别快捷路径或标准协同路径
  - ScoutAgent：获取实时/缓存论文
  - DigestAgent：生成日报内容
  - DeliveryAgent：飞书发送
  - Merger：向用户汇总结果

- 芯片研发闭环任务
  - Planner：拆成设计 / 仿真 / 测控 / 数据分析子任务
  - 多个 SpecialistAgent 并行执行
  - Merger 汇总为一份研发建议

---

## 6. Claude Code 借鉴对照（面向 2.0）

| Claude Code 参考点 | 2.0 吸收方式 | 在 2.0 中落入位置 |
|---|---|---|
| `QueryEngine / query.ts` | 借鉴统一运行主循环 | `core/runs/`, `core/gateway/` |
| `Tool.ts` | 借鉴工具抽象 | `runtimes/tools/` |
| `queryContext.ts` | 借鉴上下文装配 | `core/context_assembler/` |
| `forkedAgent.ts` | 借鉴子智能体 / 子运行 | `core/coordination/` |
| `task framework` | 借鉴后台任务建模 | `core/runs/` |
| `commands.ts` | 借鉴快捷路径注册表 | `shortcuts/` |
| `permissions/*` | 借鉴审批路由 | `core/approvals/` |
| `tools/*/UI.tsx` | 借鉴 Artifact-first 展示 | `artifacts/renderers/`, `client/shared/` |
| `components/tasks/*` | 借鉴后台任务中心 | `client/web/`, `client/desktop/` |
| `services/compact/*` | 借鉴 compaction | `core/context_assembler/`, `memory/` |

---

## 7. 与 V1 的迁移建议

## 7.1 可直接保留的模块

- 各类 `hands_*` 平台适配器
- 当前 PostgreSQL / pgvector / state_store 体系
- 项目资料库与知识基础设施
- 心跳与情报业务知识本身

## 7.2 建议包一层适配再迁移

- `gateway.py`
- `orchestrator.py`
- `brain.py`
- `chat_jobs / pipelines / tasks`
- 前端状态展示

## 7.3 不建议直接照搬 V1 逻辑到 2.0 的部分

- 聊天直接承载长任务
- 所有同步工具直接在统一链路里运行
- 业务状态字段散落在多个 dict
- 情报员重任务完全依赖通用推理链

---

## 8. 推荐实施顺序

### 阶段 A：2.0 内核骨架

- `contracts/`
- `core/runs/`
- `core/coordination/`
- `shortcuts/`

### 阶段 B：执行与上下文

- `runtimes/tools/`
- `runtimes/models/`
- `core/context_assembler/`
- `core/approvals/`

### 阶段 C：产物与客户端

- `artifacts/`
- `client/shared/`
- `client/web/` Run Console
- `client/desktop/` 工作台壳

### 阶段 D：领域深化

- Q-EDA / MES / 测控 / 数据中台 的 2.0 适配壳
- 多智能体闭环场景
- 统一 artifact viewer

---

## 9. 结语

QuantaMind 2.0 不应只是“更复杂的聊天系统”，而应成为：

**一个以 Run 为核心、以多智能体协同为中枢、以 Shortcut 为高频入口、以 Artifact 为结果载体、以 Desktop/Web 工作台为表现层的量子科研 AI 操作系统。**

这也是本设计稿的总目标。

