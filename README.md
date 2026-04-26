# QuantaMind

**QuantaMind** 是量子科技自主科研人工智能中台（与 EDA-Q-main 为独立项目）。表现方式为**客户端**：用户通过 QuantaMind 客户端与背后的 AI 中台（Gateway + Brain + Hands + Memory + Heartbeat + Skills）交互。

本仓库为独立项目，位于 `E:\work\QuantaMind`。架构说明见 [QuantaMind 架构设计方案](docs/QuantaMind_AI中台_基于OpenClaw架构设计方案.md)。

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

### 2. 启动服务端（Gateway）

```bash
python run_gateway.py
# 或
python -m quantamind.server.gateway
```

默认监听 `http://0.0.0.0:18789`。

### 3. 使用客户端

- **桌面客户端（推荐）**：双击运行桌面软件窗口  
  `python run_desktop_client.py` 或 `python -m quantamind.client.desktop`  
  窗口内输入消息与 AI 对话，支持流式回复。
- **Web 客户端**：浏览器访问 `http://localhost:18789/` 或 `http://localhost:18789/client`。
- **CLI 客户端**：另开终端执行  
  `python run_cli.py` 或 `python -m quantamind.client.cli`，按提示输入消息与 AI 对话。

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

同名旧变量 `AETHERQ_*` 仍可作为回退读取；数据目录若仅存在 `~/.aetherq` 且无 `~/.quantamind`，启动时会继续使用前者。

## 目录结构

```
E:\work\QuantaMind\
├── README.md
├── requirements.txt
├── run_gateway.py          # 启动服务端
├── run_desktop_client.py   # 启动桌面客户端（软件窗口）
├── run_cli.py
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

- `GET /health` — 健康检查  
- `POST /api/v1/sessions` — 创建会话  
- `POST /api/v1/chat` — 对话（支持 stream）  
- `WS /ws` — WebSocket 对话  
- `GET /api/v1/heartbeat` — 心跳状态  
- `GET /api/v1/skills` — 技能列表  
- `GET /api/v1/tools` — 工具列表  
- `GET /`、`GET /client` — QuantaMind Web 客户端

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
