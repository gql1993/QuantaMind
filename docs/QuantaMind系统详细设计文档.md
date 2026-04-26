# QuantaMind 量智大脑 · 系统详细设计文档

**文档版本：** V2.0  
**编制日期：** 2026年3月  
**产品版本：** QuantaMind 0.1.0  
**代码规模：** 34 个 Python 模块 / 4,220 行服务端代码 / 1,258 行 Web 客户端 / 104 个注册工具 / 42 个 API 端点 / 12 个平台适配器  

---

## 目 录

1. [系统概述](#1-系统概述)
2. [系统架构](#2-系统架构)
3. [Gateway 网关层](#3-gateway-网关层)
4. [Brain 推理层（LLM）](#4-brain-推理层)
5. [Orchestrator 编排层](#5-orchestrator-编排层)
6. [Hands 工具执行层](#6-hands-工具执行层)
7. [Agent 智能体团队](#7-agent-智能体团队)
8. [平台集成（四大域）](#8-平台集成)
9. [Memory 记忆层](#9-memory-记忆层)
10. [Heartbeat 心跳引擎](#10-heartbeat-心跳引擎)
11. [流水线引擎](#11-流水线引擎)
12. [数据中台](#12-数据中台)
13. [Web 客户端](#13-web-客户端)
14. [配置管理](#14-配置管理)
15. [接口规范（42 个 API）](#15-接口规范)
16. [数据模型](#16-数据模型)
17. [非功能性设计](#17-非功能性设计)
18. [部署架构](#18-部署架构)

---

## 1. 系统概述

### 1.1 产品定位

QuantaMind 量智大脑是**量子科技自主科研 AI 中台**，为量子芯片的"设计→仿真→制造→校准→测控→数据分析"全生命周期提供多智能体协同的 AI 能力。

### 1.2 核心能力矩阵

| 能力 | 规模 | 说明 |
|------|------|------|
| 多 Agent 协同 | 12 个 | 覆盖理论/设计/仿真/制造/测控运维/测控科研/材料/数据/算法/知识/项目管理 |
| Tool Call 循环 | 104 个工具 | LLM Function Calling，最多 20 轮自主调用 |
| 流水线引擎 | 2 种 | 模板流水线（端到端）+ 对话流水线（自动生成），支持人工审批门 |
| 平台集成 | 12 个开源项目 | Qiskit Metal / KQCircuits / OpenMES / secsgem / Grafana / ARTIQ / Qiskit Pulse / Mitiq / QCoDeS / SeaTunnel / Doris / qData |
| 自主发现 | 4 层级 | L0 实时(5min) / L1 巡检(6h) / L2 实验(12h) / L3 洞察(24h) |
| 报告导出 | Word + Markdown | 含芯片规格、每步数据表格、中文解释 |

### 1.3 技术栈

| 层级 | 技术 |
|------|------|
| 服务端 | Python 3.11+、FastAPI 0.104+、uvicorn、aiohttp、pydantic 2.0+ |
| LLM 接口 | OpenAI Function Calling 协议（兼容 7 家提供商） |
| 芯片设计 | Qiskit Metal 0.5.3（IBM）、KQCircuits 4.9.9（IQM） |
| Web 客户端 | SPA（HTML/CSS/JS），暗色主题，1,258 行 |
| 数据持久化 | config.json + Markdown 记忆 + 内存存储（生产换 Redis/Doris） |

---

## 2. 系统架构

### 2.1 分层架构

```
┌──────────────────────────────────────────────────────────────┐
│                   表现层（Presentation）                       │
│  Web 客户端（12 页面）· 桌面客户端 · CLI                        │
├──────────────────────────────────────────────────────────────┤
│                   网关层（Gateway · 42 个 API）                │
│  FastAPI · REST · WebSocket · SSE 流式 · 流水线引擎             │
├──────────────────────────────────────────────────────────────┤
│                   编排层（Orchestrator）                       │
│  意图路由（关键词匹配）· Tool Call 循环（≤20 轮）· 对话流水线     │
├─────────┬──────────┬──────────┬───────────────────────────────┤
│ Brain   │ Hands    │ Memory   │ Heartbeat                     │
│ LLM推理 │ 104工具   │ 项目记忆  │ L0-L3 自主发现                │
│ 7提供商  │ 12适配器  │ Markdown │ 异步后台                      │
├─────────┴──────────┴──────────┴───────────────────────────────┤
│                   平台适配层（12 个开源项目）                    │
│ Q-EDA: Qiskit Metal + KQCircuits                              │
│ MES:   OpenMES + secsgem + Grafana                            │
│ 测控:  ARTIQ + Qiskit Pulse + Mitiq                           │
│ 数据:  QCoDeS + SeaTunnel + Doris + qData                     │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构（34 个模块）

```
QuantaMind/
├── quantamind/
│   ├── config.py                    # 配置管理（持久化）
│   ├── shared/api.py                # Pydantic 数据模型
│   ├── server/
│   │   ├── gateway.py               # Gateway（42 API，1200+ 行）
│   │   ├── brain.py                 # Brain LLM 推理（7 提供商）
│   │   ├── hands.py                 # 工具注册表（104 工具）
│   │   ├── hands_qiskit_metal.py    # Qiskit Metal（178 行）
│   │   ├── hands_kqcircuits.py      # KQCircuits（180 行）
│   │   ├── hands_openmes.py         # OpenMES（118 行）
│   │   ├── hands_secsgem.py         # secsgem（120 行）
│   │   ├── hands_grafana.py         # Grafana（105 行）
│   │   ├── hands_artiq.py           # ARTIQ（97 行）
│   │   ├── hands_qiskit_pulse.py    # Qiskit Pulse（116 行）
│   │   ├── hands_mitiq.py           # Mitiq（111 行）
│   │   ├── hands_qcodes.py          # QCoDeS（105 行）
│   │   ├── hands_seatunnel.py       # SeaTunnel（86 行）
│   │   ├── hands_doris.py           # Doris（254 行）
│   │   ├── hands_qdata.py           # qData（98 行）
│   │   ├── memory.py                # 项目记忆
│   │   ├── heartbeat.py             # 心跳引擎
│   │   ├── skills_loader.py         # 技能加载
│   │   ├── chip_20bit_spec.py       # 20比特芯片规格
│   │   └── result_explain.py        # 报告解释生成
│   ├── agents/
│   │   ├── base.py                  # BaseAgent 抽象基类
│   │   ├── orchestrator.py          # Orchestrator 编排（200 行）
│   │   └── designer.py              # DesignerAgent
│   └── client/web/index.html        # Web 客户端（1,258 行）
├── tests/test_gateway_api.py        # 9 个 API 测试
├── demo/run_20bit_pipeline.py       # 端到端演示脚本
├── docs/                            # 文档
├── run_gateway.py                   # 启动入口
└── requirements.txt                 # 依赖
```

---

## 3. Gateway 网关层

### 3.1 职责

HTTP REST API（42 端点）+ WebSocket + SSE 流式对话 + 会话管理 + 任务与审批 + 流水线引擎 + 报告导出 + 配置热更新 + Web 客户端静态服务 + 日志收集

### 3.2 内存数据结构

| 存储 | 类型 | 说明 |
|------|------|------|
| sessions | dict[str, dict] | 会话元数据 |
| chat_histories | dict[str, list] | 会话消息历史 |
| tasks | dict[str, dict] | 任务（含种子数据） |
| pipelines | dict[str, dict] | 模板流水线 |
| chat_pipelines | dict[str, dict] | 对话流水线（来自 Orchestrator） |
| _LOG_BUFFER | deque(maxlen=500) | 日志 ring buffer |

### 3.3 种子数据

系统启动时自动创建 5 条示例任务（Q-EDA 仿真、DRC、GDS 导出、T1/T2 测量、制造提交），便于客户端演示。

---

## 4. Brain 推理层

### 4.1 类继承结构

```
BaseBrain（抽象基类）
├── OllamaBrain            # Ollama 本地推理
├── OpenAICompatBrain      # OpenAI 兼容接口
├── FallbackBrain          # LLM 不可用时的内置回复
└── SmartBrain             # 自动尝试 Primary → 降级 Fallback
```

### 4.2 Function Calling

`chat_with_tools(messages, tools)` 返回 `BrainResponse` 流：

| type | 说明 |
|------|------|
| content | 文本内容片段 |
| tool_call | 工具调用请求（name + arguments） |
| tool_calls_done | 一轮工具调用结束 |

### 4.3 支持的 LLM（7 家）

| 提供商 | API Base | 默认模型 |
|--------|----------|---------|
| Ollama | localhost:11434 | qwen2.5:7b |
| DeepSeek | api.deepseek.com/v1 | deepseek-chat |
| 通义千问 | dashscope.aliyuncs.com | qwen-plus |
| OpenAI | api.openai.com/v1 | gpt-4o-mini |
| Kimi | api.moonshot.cn/v1 | moonshot-v1-8k |
| 智谱 | open.bigmodel.cn | glm-4-flash |
| 零一万物 | api.lingyiwanwu.com/v1 | yi-lightning |

---

## 5. Orchestrator 编排层

### 5.1 意图路由

AGENT_REGISTRY 中每个 Agent 有 keywords 列表，Orchestrator 对用户消息逐词匹配，选得分最高的 Agent。

### 5.2 Tool Call 循环（核心流程）

```
用户消息
  ↓
路由到 Agent → 加载 system_prompt + tool_prefixes
  ↓
注入项目记忆（Memory）
  ↓
构建 OpenAI tools 定义（从 Hands 注册表按前缀过滤）
  ↓
创建对话流水线（CL-{uuid}）
  ↓
┌─ Loop（最多 20 轮）────────────────────────┐
│  Brain.chat_with_tools(conv, tools)         │
│  ├── 收到 content → 流式返回给客户端         │
│  ├── 收到 tool_call → Hands.run_tool()      │
│  │   → 结果回注 conv → 记录到流水线步骤      │
│  └── 无 tool_call → 写入记忆 → 结束          │
└────────────────────────────────────────────┘
```

### 5.3 对话流水线

每次对话有工具调用时自动创建 `CL-` 流水线，记录每步的 tool/args/result/status/time，客户端实时可视化。

---

## 6. Hands 工具执行层

### 6.1 注册表

```python
TOOL_REGISTRY: Dict[str, (description, callable)]
register_tool(name, description, func)
async run_tool(tool_name, **kwargs) → Any
```

### 6.2 104 个工具分布

| 平台 | 工具数 | 前缀 | 适配器行数 |
|------|--------|------|-----------|
| 通用 | 2 | echo, search_ | 内建 |
| Qiskit Metal | 8 | metal_ | 178 |
| KQCircuits | 9 | kqc_ | 180 |
| secsgem | 10 | secs_ | 120 |
| OpenMES | 10 | mes_ | 118 |
| Grafana | 7 | grafana_ | 105 |
| ARTIQ | 6 | artiq_ | 97 |
| Qiskit Pulse | 8 | pulse_ | 116 |
| Mitiq | 6 | mitiq_ | 111 |
| QCoDeS | 7 | qcodes_ | 105 |
| SeaTunnel | 8 | seatunnel_ | 86 |
| Doris | 15 | doris_ | 254 |
| qData | 8 | qdata_ | 98 |
| **合计** | **104** | | **1,564** |

### 6.3 优雅降级机制

每个适配器启动时 try/except import：
- **已安装**（如 Qiskit Metal, KQCircuits）→ 真实调用，生成真实文件
- **未安装**（如 ARTIQ, Mitiq）→ Mock 模式，返回合理模拟数据

---

## 7. Agent 智能体团队（12 个）

| # | Agent | 角色 | 工具前缀 | 关键词示例 | 状态 |
|---|-------|------|---------|-----------|------|
| 1 | 🧠 协调者 | 全局调度 | — | （默认路由） | active |
| 2 | 💎 AI 芯片设计师 | 设计 | metal_, kqc_ | 设计/芯片/transmon/gds | active |
| 3 | ⚛️ 理论物理学家 | 理论 | knowledge_, doris_query | 哈密顿/理论/噪声 | active |
| 4 | 🏭 AI 工艺工程师 | 制造 | mes_, secs_, grafana_ | 良率/工艺/批次/spc | active |
| 5 | 🔧 AI 设备运维员 | 测控运维 | artiq_, pulse_, secs_ | 校准/设备/告警/配方 | active |
| 6 | 📡 AI 测控科学家 | 测控科研 | artiq_, pulse_, mitiq_ | 表征/t1/t2/保真度/纠错 | active |
| 7 | 🧪 AI 材料科学家 | 材料 | — | （格物平台） | standby |
| 8 | 📊 AI 数据分析师 | 数据 | doris_, qdata_, seatunnel_, qcodes_ | 数据/查询/血缘/etl | active |
| 9 | 🔬 AI 量子算法工程师 | 算法 | mitiq_, knowledge_ | 算法/vqe/qaoa/电路 | active |
| 10 | 🖥️ AI 仿真工程师 | 仿真 | metal_analyze, kqc_export | 仿真/hfss/sonnet | active |
| 11 | 📚 AI 知识工程师 | 知识 | knowledge_, doris_, qdata_ | 文献/论文/知识图谱 | active |
| 12 | 📋 AI 项目经理 | 管理 | doris_, seatunnel_, grafana_ | 周报/里程碑/进度 | active |

---

## 8. 平台集成（四大域 · 12 个开源项目）

### 8.1 Q-EDA 设计平台

```
Qiskit Metal（IBM · 设计+分析）  ←→  KQCircuits（IQM · 版图+制造）
  TransmonPocket/Cross              Swissmon/SQUID/Airbridge
  RouteMeander/Pathfinder           Ansys HFSS/Q3D/Sonnet 导出
  LOM/EPR 分析                      光学掩膜 + EBL 版图
  GDS 导出                          KLayout 可视化
```

**已安装状态**：Qiskit Metal ✅ 已安装 | KQCircuits ✅ 已安装

### 8.2 MES 制造平台

```
设备 ←(SECS/GEM)→ secsgem ←(REST)→ Gateway ←→ OpenMES(业务) + Grafana(看板)
                                              ←→ QuantaMind Agent(AI 决策)
```

| 层 | 项目 | 工具数 |
|----|------|--------|
| 设备通信 | secsgem | 10 |
| MES 业务 | OpenMES | 10 |
| 可视化 | Grafana | 7 |

### 8.3 测控平台

```
芯片 ←(硬件)→ ARTIQ(实时ns) → Qiskit Pulse(校准) → Mitiq(纠错) → 高质量结果
```

| 层 | 项目 | 工具数 |
|----|------|--------|
| 实时控制 | ARTIQ | 6 |
| 校准优化 | Qiskit Pulse | 8 |
| 错误缓解 | Mitiq | 6 |

### 8.4 数据中台

```
Q-EDA + MES + QCoDeS →(SeaTunnel ETL)→ Doris(OLAP) →(qData 治理)→ AI Agent
```

| 层 | 项目 | 工具数 |
|----|------|--------|
| 数据采集 | QCoDeS | 7 |
| ETL 管道 | SeaTunnel | 8 |
| 数据仓库 | Doris | 15 |
| 数据治理 | qData | 8 |

---

## 9. Memory 记忆层

| 层级 | 名称 | 技术 | 状态 |
|------|------|------|------|
| L2 | 项目记忆 | `~/.quantamind/memory/projects/{id}.md` | **已实现** |
| L1 | 工作记忆 | Redis（计划） | 待实现 |
| L3 | 知识图谱 | Neo4j（计划） | 待实现 |
| L4 | 向量库 | Milvus/pgvector（计划） | 待实现 |

Orchestrator 在每次对话中自动注入项目记忆（最多 2000 字符），工具调用结果自动追加到记忆。

---

## 10. Heartbeat 心跳引擎

| 层级 | 间隔 | 任务 | 发现类型 |
|------|------|------|---------|
| L0 | 5 min | 设备告警、ETL 管道状态 | 设备告警、管道异常 |
| L1 | 6 h | 数据质量检查、良率趋势 | 数据质量、良率预警 |
| L2 | 12 h | 校准状态评估、实验建议 | 实验建议 |
| L3 | 24 h | 跨域关联分析、假设挖掘 | 跨域洞察 |

Gateway 启动时自动创建后台异步任务运行心跳循环。发现存入 `heartbeat.discoveries` 列表，通过 API 返回给客户端。

---

## 11. 流水线引擎

### 11.1 两种流水线

| 类型 | ID前缀 | 触发 | 数据保存 |
|------|--------|------|---------|
| 模板流水线 | PL- | 手动（Web 按钮） | 每步实时保存 |
| 对话流水线 | CL- | 自动（对话有工具调用时） | 完成后保存 |

### 11.2 人工干预

暂停 / 恢复 / 终止 / 审批通过 / 审批拒绝 —— 通过 `POST /api/v1/pipelines/{id}/control`

### 11.3 阶段审批门

启用后每阶段完成自动暂停等待人工审批。5 个审批点：芯片设计→仿真→制造→校准→测控。

### 11.4 报告导出

| 格式 | 内容 |
|------|------|
| Word (.docx) | 芯片规格页 + 工艺规格 + 设计目标 + 版图清单 + 每步数据表格 + 中文解释 |
| Markdown (.md) | 同上，纯文本格式 |

### 11.5 20 比特模板流水线详情

| 阶段 | Agent | 步骤数 | 主要操作 |
|------|-------|--------|---------|
| 1. 芯片设计 | 💎 | ~64 | 创建设计 → 20比特 → 19路由 → 19耦合器 → 空气桥/JJ → GDS + 掩膜 |
| 2. 仿真验证 | 🖥️ | ~8 | Q3D 电容矩阵 → EPR 本征模(5比特) → Ansys + Sonnet |
| 3. 工艺制造 | 🏭 | ~9 | 8步工艺 → 批次派工 → 良率/SPC → 封装 |
| 4. 设备校准 | 🔧 | ~4 | ARTIQ 硬件 → Pulse 全套校准(20比特×2批) |
| 5. 测控表征 | 📡 | ~9 | 光谱/Rabi/T1/T2/Echo/读出(20比特) → CZ门 → Mitiq |
| 6. 数据分析 | 📊 | ~7 | 跨域追溯 → 质量检查 → 保存到数据中台 |
| **合计** | **7 Agent** | **~101** | |

---

## 12. 数据中台

### 12.1 四大数据域

| 域 | 表数 | 主要表 |
|----|------|--------|
| design_domain | 4 | chip_designs, simulation_results, drc_reports, gds_exports |
| manufacturing_domain | 5 | lots, work_orders, yield_records, spc_data, equipment_events |
| measurement_domain | 5 | qubit_characterization, calibration_records, gate_benchmarks, error_mitigation_results, raw_measurements |
| pipeline_domain | 6 | pipeline_runs, pipeline_steps, design_params, calibration_params, measurement_results, fabrication_records |

### 12.2 数据流

```
流水线每步 →(实时)→ pipeline_steps（数据中台）
Q-EDA 设计 →(SeaTunnel)→ design_domain
MES 产线 →(SeaTunnel)→ manufacturing_domain
QCoDeS 测量 →(SeaTunnel)→ measurement_domain
```

### 12.3 AI 训练数据导出

`GET /api/v1/dataplatform/training-export` 导出全部流水线记录 + 步骤记录（含参数和结果 JSON），可用于微调 LLM、训练参数预测模型。

---

## 13. Web 客户端（12 页面）

| 页面 | 功能要点 |
|------|---------|
| 运转看板 | 统计卡片（可点击跳转）、网关/心跳状态、平台状态、快速了解 |
| 对话 | SSE 流式、会话列表（按首条消息命名）、发送防重复、对话流水线面板 |
| 流水线 | 模板列表 + 启动、运行历史、阶段进度条 + 卡片 + 时间线、人工干预、报告下载 |
| 任务 | Tab 筛选、模态详情（替代 alert）、审批操作 + Toast 反馈 |
| 自主发现 | 类型筛选、卡片列表、"在对话中继续"可点击 |
| Agent 团队 | 12 Agent 卡片、点击展开详情（工具/技能/快捷操作） |
| 技能 | Q-EDA / MES / 测控 / 数据中台 四大能力全景 + 10 技能卡片 |
| 数据中台 | 统计、流水线历史、步骤记录筛选、域表结构（可展开 + 点击查看血缘/质量） |
| 会话管理 | 列表 + 删除 |
| 日志 | 级别筛选 + 文本搜索 |
| 调试 | 系统状态/健康 JSON + 手动 API 调用 |
| 设置 | LLM 配置（7 家一键切换）+ Gateway 地址 |

### UX 特性

Logo 可点击回首页 · 统计卡片悬浮跳转 · Toast 操作反馈 · 流水线 localStorage 持久化 · 模态详情对话框

---

## 14. 配置管理

| 配置 | 环境变量 | 默认值 | 持久化 |
|------|---------|--------|--------|
| 数据目录 | QUANTAMIND_ROOT | ~/.quantamind | — |
| Gateway 端口 | QUANTAMIND_GATEWAY_PORT | 18789 | — |
| LLM 提供商 | QUANTAMIND_LLM_PROVIDER | ollama | config.json |
| LLM 模型 | QUANTAMIND_LLM_MODEL | qwen2.5:7b | config.json |
| LLM API Base | QUANTAMIND_LLM_API_BASE | localhost:11434 | config.json |
| LLM API Key | QUANTAMIND_LLM_API_KEY | （空） | config.json |
| 心跳间隔 | QUANTAMIND_HEARTBEAT_INTERVAL | 30 分钟 | — |

优先级：环境变量 > config.json > 默认值。Web 设置页保存后热重载 Brain。

---

## 15. 接口规范（42 个 API）

### 15.1 核心业务 API

| 路径 | 方法 | 说明 |
|------|------|------|
| /health | GET | 健康检查 |
| /api/v1/status | GET | 运转看板汇总 |
| /api/v1/sessions | POST/GET | 创建/列表会话 |
| /api/v1/sessions/{id} | DELETE | 删除会话 |
| /api/v1/sessions/{id}/history | GET | 消息历史 |
| /api/v1/chat | POST | 对话（SSE 流式，响应含 pipeline_id） |
| /ws | WebSocket | WebSocket 对话 |
| /api/v1/agents | GET | Agent 团队（12 个） |
| /api/v1/tasks | GET | 任务列表 |
| /api/v1/tasks/{id} | GET | 任务详情 |
| /api/v1/tasks/{id}/approve | POST | 审批 |

### 15.2 流水线 API

| 路径 | 方法 | 说明 |
|------|------|------|
| /api/v1/pipelines | POST | 创建模板流水线 |
| /api/v1/pipelines | GET | 列表（含模板+对话） |
| /api/v1/pipelines/{id} | GET | 详情 |
| /api/v1/pipelines/{id}/control | POST | 人工干预 |
| /api/v1/pipelines/{id}/report | GET | 报告下载（md/docx） |
| /api/v1/chat-pipelines | GET | 对话流水线列表 |
| /api/v1/chat-pipelines/{id} | GET | 对话流水线详情 |

### 15.3 平台能力 API

| 路径 | 方法 | 说明 |
|------|------|------|
| /api/v1/qeda/capabilities | GET | Q-EDA 能力全景 |
| /api/v1/mes/capabilities | GET | MES 能力全景 |
| /api/v1/measure/capabilities | GET | 测控能力全景 |
| /api/v1/dataplatform/capabilities | GET | 数据中台能力全景 |

### 15.4 数据中台 API

| 路径 | 方法 | 说明 |
|------|------|------|
| /api/v1/dataplatform/tables | GET | 表列表 |
| /api/v1/dataplatform/lineage | GET | 数据血缘 |
| /api/v1/dataplatform/quality | GET | 数据质量 |
| /api/v1/dataplatform/pipeline-history | GET | 流水线历史 |
| /api/v1/dataplatform/step-records | GET | 步骤记录 |
| /api/v1/dataplatform/training-export | GET | AI 训练数据导出 |

### 15.5 系统 API

| 路径 | 方法 | 说明 |
|------|------|------|
| /api/v1/heartbeat | GET | 心跳状态 |
| /api/v1/heartbeat/discoveries | GET | 自主发现 |
| /api/v1/skills | GET | 技能列表 |
| /api/v1/tools | GET | 工具列表（104 个） |
| /api/v1/logs | GET | 日志 |
| /api/v1/debug/status | GET | 系统状态 |
| /api/v1/debug/health | GET | 健康检查 |
| /api/v1/config/llm | GET/POST | LLM 配置 |
| /api/v1/knowledge/search | GET | 知识检索 |
| / | GET | Web 客户端 |

### 15.6 Chat SSE 协议

```
data: {"type":"content","data":"文本片段","session_id":"xxx"}
data: {"type":"done","session_id":"xxx","pipeline_id":"CL-xxx"}
```

---

## 16. 数据模型

### Pydantic 模型

| 模型 | 字段 |
|------|------|
| ChatMessage | role(user/assistant/system), content |
| ChatRequest | session_id?, message, stream |
| ChatChunk | type(content/done/error), data?, session_id? |
| TaskInfo | task_id, status, result?, error?, title?, task_type?, created_at?, session_id?, needs_approval |
| Pipeline | pipeline_id, name, status, steps[], stages[], gates[], chip_spec? |
| PipelineStep | stage, agent, emoji, title, tool, args, result, status, started_at, completed_at |

---

## 17. 非功能性设计

| 维度 | 当前状态 | 规划 |
|------|---------|------|
| 安全 | 无认证 | P1: JWT/API Key |
| 性能 | 单进程内存 | P2: Redis 会话 + 水平扩展 |
| 日志 | 内存 buffer | P3: Prometheus + OpenTelemetry |
| 测试 | 9 个 API 测试 | P2: Agent/Brain/Hands 测试 |
| CI/CD | 无 | P3: Dockerfile + GitHub Actions |

---

## 18. 部署架构

### 当前（单机）

```
浏览器 → http://127.0.0.1:18789 → Gateway（单进程）
桌面快捷方式 → run_desktop_client.py → 自动启动 Gateway + 打开浏览器
```

### 规划（生产）

```
用户 → Nginx(TLS) → Gateway(多实例) → Redis + Neo4j + Milvus + LLM API
                                     → Q-EDA / MES / 测控 / Doris+SeaTunnel+qData
```

---

## 附录 A：20 比特可调耦合器芯片规格

| 参数 | 值 |
|------|-----|
| 文档编号 | TGQ-200-000-FA09-2025 |
| 芯片尺寸 | 12.5 × 12.5 mm |
| 衬底 | 蓝宝石，430±25 μm |
| 金属膜 | 铝/钽，180±2 nm |
| 量子比特 | 20 个 Xmon（Q_odd 4.65GHz, Q_even 4.56GHz） |
| 可调耦合器 | 19 个 Transmon+SQUID（6.88GHz） |
| JJ 结构 | 铝-氧化铝-铝，200×200nm，Dolan Bridge |
| CPW | s=10μm w=5μm Z0≈50Ω |
| 封装 | 48 pin SMP，无氧铜盒 |
| 设计目标 | 单门≥99.9% 双门≥99% 读出≥99% T1≥20μs T2≥15μs |

---

## 附录 B：变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| V1.0 | 2026-03-13 | 初版 |
| V2.0 | 2026-03-14 | 增加代码统计、修复审计结果、完善数据中台表结构、流水线每步实时保存 |
