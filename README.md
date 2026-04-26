# QuantaMind

**QuantaMind** 是量子科技自主科研人工智能中台（与 EDA-Q-main 为独立项目）。表现方式为**客户端**：用户通过 QuantaMind 客户端与背后的 AI 中台（Gateway + Brain + Hands + Memory + Heartbeat + Skills）交互。

本仓库为独立项目，位于 `E:\work\QuantaMind`。架构说明见 [QuantaMind 架构设计方案](docs/QuantaMind_AI中台_基于OpenClaw架构设计方案.md)。

当前仓库同时保留旧版 Gateway/客户端，并新增了前后端分离改造基线：

- `backend/`：分离式 FastAPI API 边界
- `frontend/`：React + Vite 前台/后台工作台
- `desktop/`：Electron 桌面壳，已可加载新前端构建产物
- `docker-compose.yml`：分离式部署骨架

## 快速开始

### 1. 安装依赖

```bash
cd E:\work\QuantaMind
pip install -r requirements.txt
```

可选：安装 [Ollama](https://ollama.com/) 并拉取模型，供本地 LLM 推理（零 API 成本）：

```bash
ollama pull qwen2.5:7b
```

### 2. 启动旧版服务端（Gateway）

```bash
python run_gateway.py
# 或
python -m quantamind.server.gateway
```

默认监听 `http://0.0.0.0:18789`。

### 3. 使用旧版客户端

- **桌面客户端（推荐）**：双击运行桌面软件窗口  
  `python run_desktop_client.py` 或 `python -m quantamind.client.desktop`  
  窗口内输入消息与 AI 对话，支持流式回复。
- **Web 客户端**：浏览器访问 `http://localhost:18789/` 或 `http://localhost:18789/client`。
- **CLI 客户端**：另开终端执行  
  `python run_cli.py` 或 `python -m quantamind.client.cli`，按提示输入消息与 AI 对话。

### 4. 启动分离式前后端工作台

```powershell
.\start_separated_dev.bat
```

默认会打开两个窗口：

- Backend: `http://127.0.0.1:18789`
- Frontend: `http://127.0.0.1:5173`

也可以分别启动：

```powershell
python -m backend.quantamind_api.app
npm --prefix frontend run dev
```

### 5. 启动新前端桌面壳

```powershell
npm --prefix frontend run build
npm --prefix desktop start
```

开发时也可让 Electron 直接连接 Vite：

```powershell
set QUANTAMIND_DESKTOP_FRONTEND_URL=http://127.0.0.1:5173
npm --prefix desktop start
```

## 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `QUANTAMIND_ROOT` | 数据根目录（记忆、技能） | `~/.quantamind` |
| `QUANTAMIND_GATEWAY_HOST` | Gateway 绑定地址 | `0.0.0.0` |
| `QUANTAMIND_GATEWAY_PORT` | Gateway 端口 | `18789` |
| `QUANTAMIND_LLM_PROVIDER` | LLM 提供商 | `ollama` |
| `QUANTAMIND_LLM_MODEL` | 模型名 | `qwen2.5:7b` |
| `QUANTAMIND_LLM_API_BASE` | Ollama API 地址 | `http://localhost:11434` |
| `QUANTAMIND_HEARTBEAT_INTERVAL` | 心跳间隔（分钟） | `30` |
| `VITE_API_BASE_URL` | 分离式前端 API Base，留空时走 Vite 代理 | 空 |
| `QUANTAMIND_DESKTOP_FRONTEND_URL` | Electron 开发模式前端 URL | 空 |

同名旧变量 `AETHERQ_*` 仍可作为回退读取；数据目录若仅存在 `~/.aetherq` 且无 `~/.quantamind`，启动时会继续使用前者。

## 目录结构

```
E:\work\QuantaMind\
├── README.md
├── requirements.txt
├── run_gateway.py          # 启动服务端
├── run_desktop_client.py   # 启动桌面客户端（软件窗口）
├── run_cli.py
├── start_separated_dev.bat # 启动分离式后端 + 前端
├── backend/                # 分离式 FastAPI API
├── frontend/               # React + Vite 工作台
├── desktop/                # Electron 桌面壳
├── docker-compose.yml      # 分离式部署骨架
├── docs/
│   └── QuantaMind_AI中台_基于OpenClaw架构设计方案.md
└── quantamind/                # Python 包
    ├── __init__.py
    ├── config.py
    ├── shared/
    ├── server/
    ├── agents/
    ├── client/
    └── skills/
```

## API 摘要

### 旧版 Gateway

- `GET /health` — 健康检查  
- `POST /api/v1/sessions` — 创建会话  
- `POST /api/v1/chat` — 对话（支持 stream）  
- `WS /ws` — WebSocket 对话  
- `GET /api/v1/heartbeat` — 心跳状态  
- `GET /api/v1/skills` — 技能列表  
- `GET /api/v1/tools` — 工具列表  
- `GET /`、`GET /client` — QuantaMind Web 客户端

### 分离式 API

- `GET /api/v1/health` — 分离式 API 健康检查
- `POST /api/v1/chat/stream` — AI 工作台 SSE 流式对话
- `GET /api/v1/runs`、`GET /api/v1/runs/{id}` — Run 列表与详情
- `POST /api/v1/runs`、`POST /api/v1/runs/{id}/cancel`、`POST /api/v1/runs/{id}/retry` — Run 操作
- `GET /api/v1/artifacts`、`GET /api/v1/artifacts/{id}` — 产物列表与详情
- `GET/POST /api/v1/artifacts/{id}/preview|export|share|archive` — 产物操作
- `GET /api/v1/agents` — 智能体目录
- `GET /api/v1/permissions/me` — 当前用户权限与动态菜单
- `GET /api/v1/data/*` — 数据中心演示 API
- `GET /api/v1/knowledge/*` — 知识库/记忆中心演示 API
- `GET /api/v1/admin/*` — 后台系统、Run、智能体治理、审批/审计 API

## 部署与验证

### 本地验证

```powershell
python -m pytest tests/test_separated_api.py
npm --prefix frontend run lint
npm --prefix frontend run build
```

### Docker Compose

```powershell
docker compose up --build
```

- Frontend: `http://127.0.0.1:8080`
- Backend: `http://127.0.0.1:18789/api/v1/health`

### CI

GitHub Actions 工作流位于 `.github/workflows/ci.yml`，覆盖：

- 分离式 API smoke tests
- 前端 lint/build
- Electron 主进程脚本语法检查

更多说明：

- [分离式开发启动说明](docs/Separated_Dev_Startup.md)
- [分离式部署说明](docs/Separated_Deployment.md)
- [CI 说明](docs/CI.md)

## GitHub 上传说明

本仓库已按“源码优先”方式整理上传，默认**不包含**以下本地或大体积内容：

- 本地环境与密钥文件，如 `.quantamind.local.env`
- Python / Node 运行缓存，如 `__pycache__/`、`.pytest_cache/`、`node_modules/`
- 本地运行时目录，如 `.quantamind_v2_runtime/`、`tmp/`
- 本地服务安装产物，如 `services/` 下的安装包、数据库运行目录
- 超大第三方安装介质，如 `docs/SQLEXPR_x64_CHS/`
- 外部代码副本，如 `claude-code-main/`

### 上传后如何恢复本地环境

1. 克隆仓库：

```bash
git clone https://github.com/gql1993/QuantaMind.git
cd QuantaMind
```

2. 安装 Python 依赖：

```bash
pip install -r requirements.txt
```

3. 如需本地配置，复制示例环境文件：

```bash
copy .quantamind.local.env.example .quantamind.local.env
```

4. 如需桌面端依赖，在 `desktop/` 目录单独安装：

```bash
cd desktop
npm install
```

5. 如需 MinIO / PostgreSQL / pgvector 等本地服务，请按你的本机环境重新安装，不依赖仓库内的安装包副本。

### 上传仓库时的建议

- 只提交源码、文档、脚本、配置示例和必要的测试
- 不要提交真实密钥、Webhook、Token、账号密码
- 不要提交 `node_modules`、数据库目录、安装包、构建产物
- 如果后续需要保留超大模型、数据集或安装介质，建议改用 Git LFS 或单独的制品存储

### 首次上传前建议自查

- `.env` / `.local.env` 是否已排除
- 是否误包含大于 50MB 的二进制文件
- 是否误包含本机运行日志、数据库、缓存目录
- 是否误包含第三方代码镜像或解压后的安装目录

## 后续规划

- Phase 2：MoE 路由、更多 Agent（材料/工艺/测控）、Q-EDA/MES 工具对接、量电融合数据中心对接。  
- Phase 3：领域大模型、Heartbeat 自主科研循环、芯片迭代闭环。

详见 [QuantaMind 架构设计方案](docs/QuantaMind_AI中台_基于OpenClaw架构设计方案.md)。
