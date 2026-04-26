# QuantaMind 前后端分离改造详细设计文档

**文档版本：** Draft 0.1  
**编制日期：** 2026-04-26  
**适用范围：** QuantaMind 前端工程化、后端 API 标准化、桌面端复用、后台管理台建设  
**关联文档：** `docs/QuantaMind_前后端分离改造实施计划.md`、`docs/QuantaMind_2.0_目录与模块设计稿.md`

---

## 1. 设计目标

本设计文档用于指导 QuantaMind 从当前“Gateway + 内置 Web/桌面/CLI 客户端”演进为“前后端分离 + 多端复用 + 契约驱动”的架构。

核心目标：

- 后端专注 AI 中台能力：Run、Agent、Tool、Memory、Artifact、Knowledge、Data、Approval
- 前端专注产品体验：角色化工作台、任务中心、产物中心、数据分析、后台管理台
- 桌面端复用 Web 前端，避免重复开发
- API 契约稳定，支持前后端并行开发
- 保留 V1 可运行版本，逐步迁移到 V2 架构

---

## 2. 总体架构

## 2.1 逻辑架构

```text
┌───────────────────────────────────────────────────────────┐
│ 客户端层                                                   │
│ Web Workspace / Admin Console / Electron Desktop / CLI     │
└──────────────────────────────┬────────────────────────────┘
                               │ HTTP / SSE / WebSocket
┌──────────────────────────────▼────────────────────────────┐
│ API 层                                                     │
│ FastAPI Gateway / API Routes / Auth / CORS / Error Handler │
└──────────────────────────────┬────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────┐
│ 控制平面                                                   │
│ Sessions / Runs / Coordination / Context / Approvals       │
└──────────────────────────────┬────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────┐
│ 执行平面                                                   │
│ Agent Runtime / Tool Runtime / Model Runtime / Workers     │
└──────────────────────────────┬────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────┐
│ 数据平面                                                   │
│ Memory / Artifact Store / Knowledge / Warehouse / Audit    │
└───────────────────────────────────────────────────────────┘
```

## 2.2 前后端职责边界

| 领域 | 前端职责 | 后端职责 |
|---|---|---|
| 角色首页 | 卡片布局、角色菜单、快捷入口 | 返回角色配置、任务摘要、指标摘要 |
| AI 工作台 | 会话交互、上下文选择、状态展示 | Chat、Agent 路由、上下文装配、工具调用 |
| 我的任务 | 列表、筛选、详情、操作按钮 | Run 生命周期、状态持久化、取消/重试 |
| 产物中心 | 报告预览、筛选、导出动作 | Artifact 存储、渲染、权限、导出 |
| 数据分析 | 查询表单、图表展示、报告入口 | Text2SQL、Warehouse 查询、数据权限 |
| 审批待办 | 审批列表、详情、处理动作 | 风险策略、审批流、审计记录 |
| 后台管理 | 管理台页面、表格、筛选、配置表单 | 系统状态、Agent 配置、策略、审计 |

原则：

- 前端不直接访问数据库
- 前端不直接执行 shell、设备命令、MES 操作
- 前端不保存真实密钥
- 后端返回前端可消费的稳定数据结构

---

## 3. 目标目录设计

## 3.1 顶层目录

```text
QuantaMind/
├── backend/                  # 后端入口与 API 封装
├── frontend/                 # 独立 Web 前端工程
├── desktop/                  # Electron 桌面壳
├── shared/                   # 契约与生成物
├── quantamind/               # V1 稳定线
├── quantamind_v2/            # V2 内核
├── docs/
├── scripts/
└── tests/
```

## 3.2 后端目录

```text
backend/
├── README.md
├── quantamind_api/
│   ├── app.py
│   ├── dependencies.py
│   ├── settings.py
│   ├── routes/
│   │   ├── health.py
│   │   ├── chat.py
│   │   ├── runs.py
│   │   ├── artifacts.py
│   │   ├── knowledge.py
│   │   ├── data.py
│   │   ├── agents.py
│   │   ├── approvals.py
│   │   └── admin/
│   │       ├── system.py
│   │       ├── audit.py
│   │       └── policies.py
│   ├── services/
│   ├── adapters/
│   └── schemas/
└── tests/
```

过渡期可由 `backend/quantamind_api` 调用现有：

- `quantamind.server.gateway`
- `quantamind.server.hands`
- `quantamind.agents.orchestrator`
- `quantamind_v2.core.*`

## 3.3 前端目录

```text
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── src/
│   ├── main.tsx
│   ├── app.tsx
│   ├── routes/
│   │   ├── workspaceRoutes.tsx
│   │   └── adminRoutes.tsx
│   ├── apps/
│   │   ├── workspace/
│   │   └── admin/
│   ├── pages/
│   ├── components/
│   │   ├── layout/
│   │   ├── task/
│   │   ├── artifact/
│   │   ├── agent/
│   │   └── data/
│   ├── api/
│   │   ├── client.ts
│   │   ├── chat.ts
│   │   ├── runs.ts
│   │   ├── artifacts.ts
│   │   ├── agents.ts
│   │   └── admin.ts
│   ├── stores/
│   ├── types/
│   └── styles/
└── tests/
```

## 3.4 共享契约目录

```text
shared/
├── openapi/
│   ├── openapi.yaml
│   └── openapi.json
├── schemas/
│   ├── run.schema.json
│   ├── artifact.schema.json
│   └── event.schema.json
└── generated/
    ├── typescript/
    └── python/
```

---

## 4. API 设计

## 4.1 统一响应结构

非流式接口建议统一返回：

```json
{
  "success": true,
  "data": {},
  "error": null,
  "request_id": "req_20260426_xxx",
  "timestamp": "2026-04-26T14:49:00+08:00"
}
```

错误响应：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RUN_NOT_FOUND",
    "message": "Run 不存在",
    "detail": {}
  },
  "request_id": "req_20260426_xxx",
  "timestamp": "2026-04-26T14:49:00+08:00"
}
```

## 4.2 分页结构

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 128
}
```

## 4.3 API 分组

### Health

```text
GET /api/v1/health
GET /api/v1/admin/system/status
```

### Chat

```text
POST /api/v1/chat
POST /api/v1/chat/stream
WS   /api/v1/chat/ws
```

### Runs

```text
GET    /api/v1/runs
POST   /api/v1/runs
GET    /api/v1/runs/{run_id}
POST   /api/v1/runs/{run_id}/cancel
POST   /api/v1/runs/{run_id}/retry
GET    /api/v1/runs/{run_id}/events
GET    /api/v1/runs/{run_id}/logs
```

### Artifacts

```text
GET  /api/v1/artifacts
GET  /api/v1/artifacts/{artifact_id}
GET  /api/v1/artifacts/{artifact_id}/download
POST /api/v1/artifacts/{artifact_id}/share
```

### Agents

```text
GET /api/v1/agents
GET /api/v1/agents/{agent_id}
GET /api/v1/admin/agents
PUT /api/v1/admin/agents/{agent_id}
```

### Knowledge

```text
GET  /api/v1/knowledge/search
GET  /api/v1/knowledge/{doc_id}
POST /api/v1/knowledge/import
```

### Data

```text
POST /api/v1/data/query
POST /api/v1/data/text2sql
POST /api/v1/data/cross-domain
GET  /api/v1/data/assets
```

### Approvals

```text
GET  /api/v1/approvals
GET  /api/v1/approvals/{approval_id}
POST /api/v1/approvals/{approval_id}/approve
POST /api/v1/approvals/{approval_id}/reject
```

---

## 5. 流式事件设计

AI 工作台和任务详情需要实时展示过程，建议统一事件格式。

```json
{
  "event_id": "evt_xxx",
  "run_id": "run_xxx",
  "type": "tool_started",
  "stage": "design_analysis",
  "message": "开始执行设计参数分析",
  "payload": {},
  "created_at": "2026-04-26T14:49:00+08:00"
}
```

事件类型建议：

| 类型 | 说明 |
|---|---|
| `run_created` | Run 创建 |
| `stage_started` | 阶段开始 |
| `stage_completed` | 阶段完成 |
| `tool_started` | 工具开始 |
| `tool_completed` | 工具完成 |
| `artifact_created` | 产物生成 |
| `approval_required` | 需要审批 |
| `run_failed` | Run 失败 |
| `run_completed` | Run 完成 |

---

## 6. 前端应用设计

## 6.1 路由设计

```text
/
├── /workspace
│   ├── /home
│   ├── /ai
│   ├── /tasks
│   ├── /tasks/:runId
│   ├── /artifacts
│   ├── /artifacts/:artifactId
│   ├── /knowledge
│   ├── /data
│   ├── /pipeline
│   ├── /approvals
│   └── /dashboard
│
└── /admin
    ├── /overview
    ├── /runs
    ├── /runs/:runId
    ├── /system
    ├── /data-governance
    ├── /agents
    ├── /policies
    ├── /knowledge
    ├── /artifacts
    ├── /ops
    ├── /audit
    └── /settings
```

## 6.2 页面分层

```text
Page
├── Layout
├── Feature Components
├── Query Hooks
├── API Client
└── Types
```

示例：

```text
pages/tasks/TaskDetailPage.tsx
components/task/RunStageProgress.tsx
components/task/RunEventTimeline.tsx
api/runs.ts
types/run.ts
```

## 6.3 状态管理

建议分三类：

| 状态类型 | 工具 | 示例 |
|---|---|---|
| 服务端状态 | TanStack Query | Run 列表、Artifact 详情 |
| 客户端 UI 状态 | Zustand | 当前角色、侧栏折叠、主题 |
| 表单状态 | React Hook Form | 新建任务、审批处理 |

## 6.4 角色化菜单模型

```ts
type RoleKey =
  | "chip_designer"
  | "simulation_engineer"
  | "process_engineer"
  | "measurement_engineer"
  | "data_analyst"
  | "intel_officer"
  | "project_manager";

type MenuItem = {
  key: string;
  label: string;
  path: string;
  visibleRoles: RoleKey[];
  defaultFor?: RoleKey[];
  permission?: string;
};
```

---

## 7. 后端应用设计

## 7.1 FastAPI App 结构

```python
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="QuantaMind API")
    register_middlewares(app)
    register_routes(app)
    register_exception_handlers(app)
    return app
```

## 7.2 中间件

建议引入：

- CORS
- Request ID
- 访问日志
- 错误处理
- 简单鉴权预留

## 7.3 CORS 配置

开发期允许：

```text
http://localhost:5173
http://127.0.0.1:5173
```

生产期应配置明确域名，不使用 `*`。

## 7.4 服务层封装

API route 不直接写业务逻辑，应调用服务层：

```text
routes/runs.py
└── services/run_service.py
    └── quantamind_v2.core.runs
```

这样可以避免路由层继续膨胀。

---

## 8. 桌面端设计

## 8.1 开发模式

Electron 加载：

```text
http://localhost:5173
```

## 8.2 生产模式

Electron 加载：

```text
frontend/dist/index.html
```

## 8.3 Preload 边界

`preload.js` 只暴露必要能力：

- 获取本地配置
- 打开文件选择
- 本地通知
- 安全的 IPC 调用

不允许前端直接调用任意 shell。

---

## 9. 权限设计

## 9.1 权限层级

| 层级 | 说明 |
|---|---|
| P0 | 页面可见 |
| P1 | 可发起任务 |
| P2 | 可执行高风险操作 |
| P3 | 可进入后台治理台 |

## 9.2 前端权限

前端用于：

- 菜单显示
- 按钮显示
- 页面入口保护

## 9.3 后端权限

后端必须做最终校验：

- API 权限
- 数据权限
- 工具权限
- 审批权限

前端隐藏按钮不能替代后端鉴权。

---

## 10. 构建与启动设计

## 10.1 后端启动

```bash
python run_gateway.py
```

后续可新增：

```bash
python -m backend.quantamind_api.app
```

## 10.2 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 10.3 桌面启动

```bash
cd desktop
npm install
npm run start
```

## 10.4 一键开发脚本

后续可在 `scripts/` 中增加：

```text
scripts/dev_backend.ps1
scripts/dev_frontend.ps1
scripts/dev_desktop.ps1
```

---

## 11. 测试设计

## 11.1 后端测试

覆盖：

- API 响应结构
- Run 生命周期
- Artifact 查询
- Agent 列表
- 权限与审批

## 11.2 前端测试

覆盖：

- 路由渲染
- 角色菜单
- API Client
- 关键页面组件

## 11.3 集成测试

覆盖：

- AI 工作台发起任务
- Run 状态更新
- Artifact 生成与展示
- 审批阻断和继续执行

---

## 12. 部署设计

## 12.1 开发部署

```text
Frontend Dev Server :5173
Backend Gateway     :18789
```

前端通过 Vite proxy 调后端。

## 12.2 单机生产部署

```text
FastAPI 提供 API
Nginx 或 FastAPI StaticFiles 提供 frontend/dist
Electron 可加载同一套 dist
```

## 12.3 企业内网部署

建议：

- 前端静态资源独立部署
- 后端 API 独立部署
- API 域名和前端域名通过 CORS 或反向代理打通
- 数据库、对象存储、向量库独立服务化

---

## 13. 兼容策略

| 旧能力 | 兼容方式 | 迁移目标 |
|---|---|---|
| `quantamind/client/web` | 保留旧入口 | 迁移到 `frontend/` |
| `quantamind/client/desktop.py` | 保留一段时间 | Electron 加载新前端 |
| CLI | 长期保留 | 工程调试和自动化入口 |
| 旧 Gateway 路由 | 包装兼容 | 标准 `/api/v1` |
| V1 Agent/Hands | 服务层适配 | V2 Runtime |

---

## 14. 首批落地页面

## 14.1 前台

- 角色化首页
- AI 工作台
- 我的任务
- 任务详情
- 产物中心
- 数据分析工作台
- 审批待办

## 14.2 后台

- 后台总览
- Run 控制台
- Run 详情
- 系统运维
- 智能体管理

---

## 15. 首批落地 API

- `GET /api/v1/health`
- `POST /api/v1/chat`
- `GET /api/v1/runs`
- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/artifacts`
- `GET /api/v1/artifacts/{artifact_id}`
- `GET /api/v1/agents`
- `GET /api/v1/admin/system/status`

---

## 16. 开发协作约定

建议采用：

- API 先行：后端先给 OpenAPI 或 Mock
- 页面先行：前端先按 Mock 实现页面骨架
- 契约评审：每个核心对象先评审数据结构
- 小步提交：目录迁移和功能开发分开提交
- 不在同一提交中混合大规模移动和逻辑改造

---

## 17. 后续演进

前后端分离完成后，可继续推进：

- 多租户和组织权限
- 统一认证登录
- WebSocket/SSE 事件总线
- OpenAPI 自动生成 TypeScript SDK
- 桌面端离线缓存
- 后台策略灰度发布
- Run 拓扑可视化
- Artifact Viewer 插件化

---

## 18. 结论

QuantaMind 的前后端分离不应简单理解为“把页面挪出去”，而应是：

- 后端沉淀为 AI 中台能力层
- 前端升级为角色化科研工作台和平台管理台
- 桌面端复用同一套前端体验
- API 契约成为前后端协作核心

推荐先采用单仓库分目录模式，待 V2 架构、API 契约和部署方式稳定后，再评估是否拆分为独立仓库。
