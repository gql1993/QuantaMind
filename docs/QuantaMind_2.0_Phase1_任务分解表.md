# QuantaMind 2.0 Phase 1 任务分解表

**文档版本：** Draft 0.1  
**编制日期：** 2026-04-07  
**所属阶段：** Phase 1 - 2.0 骨架层  
**关联文档：**

- `docs/QuantaMind_2.0_目录与模块设计稿.md`
- `docs/QuantaMind_2.0_实施路线图.md`

---

## 1. Phase 1 目标

Phase 1 的目标不是迁移业务逻辑，而是把 2.0 的基础工程骨架搭起来，为后续 Phase 2 的 `RunCoordinator`、多智能体协同、Shortcut、Tool Runtime 奠定结构基础。

本阶段完成后，应具备：

1. `quantamind_v2/` 独立包可导入
2. `contracts/` 有最小统一契约
3. `core/runs/` 有最小 Run 生命周期骨架
4. `shortcuts/` 有最小注册表入口
5. `core/gateway/` 有最小 2.0 入口壳

---

## 2. 范围边界

## 2.1 本阶段要做

- 建立目录骨架
- 建立最小 Python 包结构
- 建立 2.0 的核心契约占位文件
- 建立最小 Run 状态模型
- 建立最小 Shortcut 注册表
- 建立最小 Gateway 入口骨架
- 建立 Phase 1 的测试占位结构

## 2.2 本阶段不做

- 不迁移情报员业务逻辑
- 不迁移现有聊天主逻辑
- 不改动当前 V1 `gateway.py`
- 不实现完整客户端页面
- 不实现完整 Tool Runtime
- 不实现完整多智能体协同

---

## 3. 交付物清单

| 交付物 | 内容 | 验收 |
|---|---|---|
| 2.0 包骨架 | `quantamind_v2/` 目录与基础 `__init__.py` | 可导入 |
| 契约骨架 | `contracts/run.py`、`event.py`、`artifact.py` | 字段清晰 |
| Run 核心骨架 | `core/runs/coordinator.py`、`lifecycle.py` | 可定义最小 run |
| Shortcut 骨架 | `shortcuts/registry.py` | 可注册快捷路径 |
| Gateway 壳层骨架 | `core/gateway/app.py` | 可作为 2.0 服务端入口起点 |
| 阶段说明 | 本文档 | 可直接用于拆任务 |

---

## 4. 工作分解结构（WBS）

## 4.1 WBS-1 建立 2.0 目录骨架

### 任务

- 创建 `quantamind_v2/`
- 创建以下子目录：
  - `config/`
  - `contracts/`
  - `core/`
  - `core/gateway/`
  - `core/runs/`
  - `core/coordination/`
  - `core/context_assembler/`
  - `core/approvals/`
  - `core/sessions/`
  - `core/planning/`
  - `runtimes/`
  - `runtimes/tools/`
  - `runtimes/models/`
  - `runtimes/workers/`
  - `runtimes/mcp/`
  - `shortcuts/`
  - `artifacts/`
  - `memory/`
  - `services/`
  - `integrations/`
  - `client/`
  - `client/shared/`
  - `client/web/`
  - `client/desktop/`
  - `migration/`

### 输出

- 2.0 的目录结构在仓库中可见

### 验收标准

- Python 导入路径可识别
- 与 2.0 设计稿中的顶层目录一致

---

## 4.2 WBS-2 建立基础契约

### 任务

- 新建 `contracts/run.py`
- 新建 `contracts/event.py`
- 新建 `contracts/artifact.py`
- 新建 `contracts/approval.py`
- 新建 `contracts/tool.py`
- 新建 `contracts/context.py`

### 约束

- 只定义骨架和关键字段
- 不在本阶段引入过多业务细节

### 建议最小字段

#### `Run`

- `run_id`
- `run_type`
- `origin`
- `parent_run_id`
- `state`
- `stage`
- `status_message`
- `owner_agent`
- `created_at`
- `updated_at`
- `completed_at`

#### `Event`

- `event_id`
- `run_id`
- `event_type`
- `timestamp`
- `payload`

#### `Artifact`

- `artifact_id`
- `run_id`
- `artifact_type`
- `title`
- `summary`
- `created_at`

### 验收标准

- 契约文件命名与 2.0 设计稿一致
- 后续模块不再自己发明同义状态字段

---

## 4.3 WBS-3 建立最小 Run 核心

### 任务

- 新建 `core/runs/coordinator.py`
- 新建 `core/runs/lifecycle.py`
- 新建 `core/runs/registry.py`

### 设计要求

- `registry.py`
  - 负责 run 的注册与查询
- `lifecycle.py`
  - 负责状态流转规则
- `coordinator.py`
  - 负责创建 run、推进阶段、结束 run

### 本阶段只支持的状态

- `queued`
- `running`
- `completed`
- `failed`
- `cancelled`

### 验收标准

- 能创建一个最小 run 对象
- 能从 `queued -> running -> completed/failed`

---

## 4.4 WBS-4 建立最小 Shortcut 骨架

### 任务

- 新建 `shortcuts/registry.py`
- 预留 `matcher` 和 handler 注册位置

### 本阶段目标

- 只定义注册和查找接口
- 不要求完成业务实现

### 推荐首批快捷路径名称

- `intel_today`
- `system_status`
- `db_status`
- `latest_reports`

### 验收标准

- 可注册一个 shortcut
- 可按名称查到一个 shortcut handler

---

## 4.5 WBS-5 建立最小 Gateway 壳层

### 任务

- 新建 `core/gateway/app.py`
- 预留 2.0 API 装配入口

### 本阶段目标

- 只做壳层，不迁业务
- 为后续挂载 `runs` / `artifacts` / `shortcuts` 路由做准备

### 验收标准

- 存在明确的 2.0 服务入口文件
- 不与 V1 的 `quantamind/server/gateway.py` 混用

---

## 4.6 WBS-6 建立测试占位结构

### 任务

- 建立 `tests/v2/`
- 新增最小测试占位：
  - `test_run_contracts.py`
  - `test_run_lifecycle.py`
  - `test_shortcuts_registry.py`

### 验收标准

- 2.0 测试目录独立存在
- 后续新模块都有明确测试归属

---

## 5. 建议实施顺序

建议按以下顺序执行：

1. WBS-1 建目录骨架
2. WBS-2 建契约骨架
3. WBS-3 建 Run 核心骨架
4. WBS-4 建 Shortcut 骨架
5. WBS-5 建 Gateway 壳层
6. WBS-6 建测试占位

原因：

- 先建结构，再建契约
- 先建契约，再建调度器
- 再由调度器决定后续业务迁移边界

---

## 6. 责任拆分建议

| 角色 | Phase 1 重点责任 |
|---|---|
| 架构师 | 目录边界、契约字段、模块命名、Phase 1 验收定义 |
| 研发工程师 | 落目录、落骨架、实现最小 Run / Shortcut / Gateway |
| 测试工程师 | 补最小骨架测试、确认 V1/V2 不互相污染 |

---

## 7. 风险与控制

| 风险 | 表现 | 控制措施 |
|---|---|---|
| 目录建得过大过空 | 很多目录无意义 | 先保证核心目录存在，后续逐步充实 |
| 契约过早细化 | 后续频繁推翻 | 只保留核心字段，不在本阶段固化业务细节 |
| V1/V2 边界不清 | 研发反复改错目录 | 文档中明确 V1/V2 修改原则 |
| 过早迁移业务 | 骨架阶段变成重构阶段 | 严格限制 Phase 1 不迁业务逻辑 |

---

## 8. Phase 1 完成定义（DoD）

当以下条件全部满足时，认为 Phase 1 完成：

1. `quantamind_v2/` 基础目录已创建
2. `contracts/` 核心文件已存在
3. `core/runs/` 最小骨架已存在
4. `shortcuts/registry.py` 已存在
5. `core/gateway/app.py` 已存在
6. `tests/v2/` 已建立
7. V1 现有运行路径未被破坏

---

## 9. Phase 1 完成后立刻进入的 Phase 2 主题

Phase 1 完成后，下一步不建议先做客户端，而应优先进入：

1. `RunCoordinator` 真正可运行
2. `ShortcutIntentRegistry` 可驱动业务
3. `core/coordination/` 多智能体协同骨架
4. 以“今日情报日报”作为 V2 第一条业务试点链路

---

## 10. 当前推荐动作

如果要立即进入实施，建议下一步直接做：

1. 在仓库中创建 `quantamind_v2/` 最小目录骨架
2. 同步创建 `contracts/`、`core/runs/`、`shortcuts/`、`core/gateway/`
3. 补最小 `__init__.py` 与占位骨架文件

这一步完成后，Phase 1 就从“文档阶段”进入“工程落地阶段”。

