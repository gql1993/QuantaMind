# QuantaMind

**QuantaMind** 是量子科技自主科研人工智能中台，表现方式为**客户端**：用户通过 QuantaMind 客户端与背后的 AI 中台（Gateway + Brain + Hands + Memory + Heartbeat + Skills）交互。

本包属于独立项目 QuantaMind（位于 E:\work\QuantaMind）。架构说明见项目根目录 [README](../../README.md) 与 [docs](../../docs/)。

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

## 目录结构

```
quantamind/
├── __init__.py
├── config.py                 # 配置与路径
├── run_gateway.py            # 启动 Gateway
├── run_cli.py                # 启动 CLI 客户端
├── requirements.txt
├── README.md
├── shared/                   # 共享 API 类型
│   └── api.py
├── server/                   # 服务端
│   ├── gateway.py            # FastAPI + WebSocket
│   ├── brain.py               # LLM 适配（Ollama）
│   ├── hands.py               # 工具注册与执行
│   ├── memory.py             # Markdown 项目记忆
│   ├── heartbeat.py          # 心跳循环
│   └── skills_loader.py      # YAML+MD 技能加载
├── agents/                   # AI 科学家智能体
│   ├── base.py
│   ├── orchestrator.py       # 路由与协调
│   └── designer.py           # 芯片设计师 Agent
├── client/                   # 客户端（表现层）
│   ├── cli.py                 # CLI
│   └── web/
│       └── index.html         # Web 客户端
└── skills/                   # 内置技能（Markdown+YAML）
    └── design/
        └── transmon-design.md
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

## 后续规划

- Phase 2：MoE 路由、更多 Agent（材料/工艺/测控）、Q-EDA/MES 工具对接、量电融合数据中心对接。  
- Phase 3：领域大模型、Heartbeat 自主科研循环、芯片迭代闭环。

详见项目根目录 [docs](../../docs/) 下的架构设计方案。
