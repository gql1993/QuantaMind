# QuantaMind 前后端分离改造实施计划

**文档版本：** Draft 0.1  
**编制日期：** 2026-04-26  
**适用范围：** QuantaMind 当前可运行版本、`quantamind_v2/` 架构演进、Web / Desktop / CLI 客户端改造  
**目标：** 在不破坏现有 Gateway、桌面客户端和 CLI 可用性的前提下，逐步完成前后端职责分离、API 契约固化、前端工程独立化和桌面端复用。

---

## 1. 改造背景

当前 QuantaMind 已具备：

- `FastAPI Gateway` 统一服务端入口
- `Brain + Orchestrator + Hands + Memory + Heartbeat + Skills` 后端能力
- Web 客户端、桌面客户端、CLI 客户端雏形
- `quantamind_v2/` 中的 Run、Artifact、Shortcut、Gateway 等 2.0 架构骨架

当前主要问题：

- Web 页面仍偏后端静态页面和简单客户端壳层
- 前端状态、任务状态、产物展示、后台管理缺少独立工程化组织
- API 契约尚未完全稳定，前后端容易互相耦合
- Desktop 与 Web UI 后续若各自演进，会产生重复开发
- 运营、数据、系统、智能体、审计等后台能力需要更清晰的管理台承载

---

## 2. 改造目标

### 2.1 总体目标

将 QuantaMind 演进为：

```text
单仓库 Monorepo
├── 后端：FastAPI + Agent/Run/Tool/Data/Artifact 能力
├── 前端：React/Vite/TypeScript 工作台与管理台
├── 桌面端：Electron 壳层复用前端构建产物
└── 契约层：OpenAPI / Schema / TypeScript 类型
```

### 2.2 业务目标

- 支持前台角色化工作台：芯片设计、仿真、制造、测控、数据、情报、项目经理
- 支持后台管理台：运行管理、系统运维、数据治理、智能体管理、策略审批、安全审计
- 支持 Run / Artifact / Agent / Knowledge / Data / Approval 等核心对象产品化
- 支持 Web、Desktop、CLI 多端统一接入同一套后端 API

### 2.3 技术目标

- 前端工程独立构建、独立路由、独立状态管理
- 后端 API 标准化、文档化、可测试
- 桌面端不再维护一套独立 UI，而是加载前端构建产物
- 建立前后端联调、构建、测试和部署约定

---

## 3. 改造原则

1. **单仓库优先**：当前仍处于快速演进期，先在同一 GitHub 仓库内分目录，不拆多仓。
2. **后端能力不下沉到前端**：工具调用、数据写入、权限审批、Agent 调度均留在后端。
3. **契约先行**：新增页面先明确 API、数据结构、错误码和流式消息格式。
4. **V1 可运行优先**：不一次性删除 `quantamind/client/web` 和 `quantamind/client/desktop.py`，采用并行迁移。
5. **桌面端复用 Web**：Electron 只做壳层、权限桥接和本地能力代理。
6. **后台和前台共用前端工程**：用路由和权限区分 `/workspace` 与 `/admin`。

---

## 4. 目标目录结构

建议最终形成：

```text
QuantaMind/
├── backend/
│   ├── README.md
│   ├── quantamind_api/
│   │   ├── app.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── adapters/
│   │   └── dependencies.py
│   └── tests/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── apps/
│   │   │   ├── workspace/
│   │   │   └── admin/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api/
│   │   ├── stores/
│   │   ├── routes/
│   │   └── types/
│   └── tests/
│
├── desktop/
│   ├── main.js
│   ├── preload.js
│   └── package.json
│
├── shared/
│   ├── openapi/
│   ├── schemas/
│   └── generated/
│
├── quantamind/              # V1 稳定线，逐步迁移
├── quantamind_v2/           # V2 核心能力，逐步作为后端内核
├── docs/
├── scripts/
└── tests/
```

过渡期允许：

- `quantamind/` 保持现有服务端和客户端可运行
- `frontend/` 新建后逐步替代 `quantamind/client/web`
- `backend/` 先作为薄封装，逐步吸收 `quantamind/server`

---

## 5. 阶段计划

## 阶段 0：基线整理

**目标：** 保证当前仓库干净、可运行、可回退。

任务：

- 固化当前 `main` 分支作为改造基线
- 确认 `.gitignore` 已排除本地环境、运行缓存、安装包、大文件
- 补充 README 中的开发环境和 GitHub 上传说明
- 建立改造分支，如 `feature/frontend-backend-split`

交付物：

- 干净 Git 工作区
- 改造分支
- 当前 API 和页面清单

验收标准：

- `python run_gateway.py` 仍可启动
- Web / Desktop / CLI 原入口仍可用
- 仓库无超大安装包、密钥、运行缓存

---

## 阶段 1：API 契约梳理

**目标：** 先定义前端需要调用的后端能力边界。

任务：

- 梳理现有 Gateway 路由
- 将 API 分为前台 API 和后台 API
- 统一响应结构
- 统一错误码
- 统一分页、筛选、排序规范
- 输出 OpenAPI 文档

建议 API 分组：

```text
/api/v1/health
/api/v1/sessions
/api/v1/chat
/api/v1/runs
/api/v1/artifacts
/api/v1/knowledge
/api/v1/data
/api/v1/agents
/api/v1/approvals
/api/v1/admin/system
/api/v1/admin/audit
```

交付物：

- `docs/QuantaMind_API_契约说明.md`
- OpenAPI JSON/YAML
- 前端 API SDK 初稿

验收标准：

- 前端能基于契约并行开发 Mock 页面
- 后端接口返回结构一致
- 每个 P0 页面至少有对应 API 契约

---

## 阶段 2：新建前端工程

**目标：** 建立独立前端工程，先跑通最小页面和 API 调用。

建议技术栈：

- Vite
- React
- TypeScript
- Ant Design 或 shadcn/ui
- TanStack Query
- Zustand
- React Router

任务：

- 新建 `frontend/`
- 配置 `package.json`
- 配置开发代理到 `http://localhost:18789`
- 建立基础布局：顶栏、侧栏、内容区
- 建立 `/workspace` 和 `/admin` 路由
- 接入 `/health`
- 接入 `/api/v1/chat` 或现有 chat API

交付物：

- `frontend/` 工程
- 基础布局
- API Client 封装
- `.env.example`

验收标准：

- `npm install` 成功
- `npm run dev` 成功
- 前端可展示后端健康状态
- 前端可调用一次 Chat / Health API

---

## 阶段 3：前台工作台 P0 页面

**目标：** 完成前台角色化工作台的最小闭环。

P0 页面：

- 角色化首页
- AI 工作台
- 我的任务列表
- 任务详情页
- 产物中心
- 数据分析工作台
- 审批待办

任务：

- 建立角色配置模型
- 建立菜单和权限配置
- 接入 Run 列表与详情
- 接入 Artifact 列表与详情
- 接入 Chat / Task 创建流程
- 用 Mock 补齐未完成 API

交付物：

- 前台 P0 页面
- 角色化菜单配置
- 前台路由表

验收标准：

- 芯片设计、测控、数据分析、项目经理至少 4 类角色首页可展示
- 用户可从 AI 工作台发起任务
- 用户可查看任务详情和产物

---

## 阶段 4：后台管理台 P0 页面

**目标：** 建立平台治理入口。

P0 页面：

- 后台总览
- Run 控制台
- Run 详情页
- 系统运维页
- 智能体管理页

任务：

- 建立 `/admin` 路由和后台布局
- 接入 Run 管理 API
- 接入系统状态 API
- 接入 Agent 目录和工具权限数据
- 建立后台表格、筛选、详情抽屉组件

交付物：

- 后台 P0 页面
- 后台路由表
- 后台权限点清单

验收标准：

- 可查看全局 Run 列表
- 可查看单个 Run 的阶段、日志、产物、审批
- 可查看系统健康与 Agent 目录

---

## 阶段 5：桌面端适配

**目标：** 桌面端复用 Web 前端，避免两套 UI。

任务：

- Electron 加载 `frontend` 构建产物
- 保留 `preload.js` 作为安全桥接层
- 桌面端默认连接本地 Gateway
- 支持开发模式加载 `http://localhost:5173`
- 支持生产模式加载本地 `dist`

交付物：

- 桌面端加载新前端
- 桌面端配置说明

验收标准：

- `npm run dev` 下 Electron 可加载前端
- 打包后可离线打开桌面工作台
- 桌面端与 Web 端页面能力一致

---

## 阶段 6：旧客户端迁移与收口

**目标：** 逐步替换旧 Web 静态页和桌面 Python 客户端。

任务：

- 标记旧入口为兼容入口
- 将 `quantamind/client/web` 中可复用逻辑迁移到 `frontend`
- 将旧页面路由重定向到新前端
- 保留 CLI 作为工程调试入口
- 清理不再维护的重复 UI

交付物：

- 迁移说明
- 兼容入口说明
- 删除或冻结清单

验收标准：

- 新前端覆盖主要使用场景
- 旧入口不影响新入口运行
- 文档中明确推荐入口

---

## 6. API 改造任务清单

| 模块 | 优先级 | 后端任务 | 前端依赖 |
|---|---|---|---|
| Health | P0 | 标准健康检查 | 登录后状态、后台总览 |
| Chat | P0 | 统一对话接口、流式输出 | AI 工作台 |
| Runs | P0 | Run 列表、详情、取消、重试 | 我的任务、Run 控制台 |
| Artifacts | P0 | 产物列表、详情、导出 | 产物中心 |
| Agents | P0 | Agent 目录、能力画像 | Agent 面板、智能体管理 |
| System Admin | P0 | 服务状态、工具状态 | 后台系统运维 |
| Knowledge | P1 | 检索、详情、引用 | 知识中心 |
| Data | P1 | 自然语言查数、跨域分析 | 数据分析 |
| Approvals | P1 | 待办、详情、处理 | 审批待办 |
| Audit | P2 | 操作记录、数据访问审计 | 安全审计 |

---

## 7. 前端改造任务清单

| 模块 | 优先级 | 任务 |
|---|---|---|
| 工程初始化 | P0 | Vite + React + TypeScript |
| 基础布局 | P0 | 顶栏、侧栏、内容区、面包屑 |
| API Client | P0 | 请求封装、错误处理、认证预留 |
| 路由 | P0 | `/workspace`、`/admin` |
| 角色菜单 | P0 | 角色化菜单与默认首页 |
| AI 工作台 | P0 | 会话区、Agent 面板、上下文面板 |
| 任务中心 | P0 | Run 列表、详情、阶段进度 |
| 产物中心 | P0 | Artifact 列表、详情 |
| 后台 Run 控制台 | P0 | 筛选、表格、详情抽屉 |
| 数据分析 | P1 | 查数、图表、报告生成 |
| 知识中心 | P1 | 检索、详情、引用 |
| 审批待办 | P1 | 列表、详情、处理 |

---

## 8. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| API 契约未稳定 | 前后端返工 | 先做 OpenAPI 和 Mock |
| 一次性迁移范围过大 | 破坏现有可运行版本 | V1 兼容入口保留 |
| 桌面端和 Web 重复开发 | 成本增加 | Electron 复用 Web 构建产物 |
| 权限边界不清 | 后台能力误暴露 | 菜单权限和 API 权限分层 |
| 流式输出复杂 | AI 工作台体验受影响 | 先支持 SSE/WebSocket 其中一种 |
| 大文件误入仓库 | 推送失败 | 强化 `.gitignore` 和上传自查 |

---

## 9. 推荐里程碑

### M1：前后端分离骨架

- `frontend/` 工程创建
- 后端 CORS 和 `/health` 可调用
- `/workspace` 和 `/admin` 基础布局可访问

### M2：任务驱动闭环

- AI 工作台可发起任务
- 我的任务可查看 Run
- 任务详情可查看阶段和产物

### M3：角色化前台

- 4 类角色首页可用
- 研发链路设计页、测控页可用
- 产物中心可用

### M4：后台治理入口

- Run 控制台可用
- 系统运维页可用
- 智能体管理页可用

### M5：桌面端复用

- Electron 加载新前端
- Web / Desktop 使用同一套 UI

---

## 10. 实施建议

第一轮不要追求完整后台和完整角色体系，建议先做：

1. `frontend/` 工程骨架
2. 前台 4 个页面：角色首页、AI 工作台、我的任务、任务详情
3. 后台 2 个页面：Run 控制台、系统状态
4. API 5 组：Health、Chat、Runs、Artifacts、Agents

完成后再逐步扩展数据分析、知识中心、审批、安全审计和运营管理。
