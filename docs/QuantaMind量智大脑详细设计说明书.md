# QuantaMind（量智大脑）详细设计说明书

**文档编号：** AETHERQ-DD-2026-001  
**版本：** V1.5  
**编制说明：** 量智大脑即 QuantaMind，为长三角 AI+量子融合产业创新平台“1+6”中的智能中台。  
**编制日期：** 2026年3月  
**密级：** 内部公开

---

## 目录

1. [概述](#1-概述)（含 QuantaMind 与 OpenClaw 的架构对应）
2. [系统架构](#2-系统架构)（含各层级技术栈与语言）
3. [Gateway（网关）详细设计](#3-gateway网关详细设计)
4. [Brain（智能体路由与多模型推理）详细设计](#4-brain智能体路由与多模型推理详细设计)
5. [Hands（工具执行层）详细设计](#5-hands工具执行层详细设计)（含三大优先平台与数据中台假设与实时交互）
6. [Memory（记忆与知识）详细设计](#6-memory记忆与知识详细设计)
7. [Heartbeat（心跳与自主任务）详细设计](#7-heartbeat心跳与自主任务详细设计)
8. [Skills（技能）详细设计](#8-skills技能详细设计)
9. [AI 科学家智能体详细设计](#9-ai-科学家智能体详细设计)
10. [客户端详细设计](#10-客户端详细设计)
11. [接口规范](#11-接口规范)
12. [非功能性设计](#12-非功能性设计)
13. [部署与运行](#13-部署与运行)
14. [业务流](#14-业务流)
15. [数据流](#15-数据流)

---

## 1. 概述

### 1.1 定位与范围

**量智大脑 = QuantaMind**，是创新平台“1个智能中台+6大业务平台”中的“1”，即**量子科技自主科研人工智能中台**。其职责为：

- **统一入口**：用户仅通过 QuantaMind 客户端与平台交互，不直接访问六大业务平台。
- **智能内核**：提供会话管理、智能体路由、多模型推理、工具执行、记忆与知识、自主科研心跳及技能市场。
- **能力输出**：通过标准化 API 与技能（Skills）向启元、格物、墨子、悬镜、天元、开物提供 AI 赋能，并接收各平台反馈数据，形成数据驱动闭环。

本说明书对 QuantaMind 服务端（Gateway、Brain、Hands、Memory、Heartbeat、Skills）及客户端形态进行**详细设计**，作为开发、联调与验收依据。

### 1.2 设计目标

| 目标 | 说明 |
|------|------|
| 科研加速 | 芯片设计迭代周期显著缩短（目标量级：10x），依托代理模型、知识复用与自动化流水线。 |
| 自主发现 | AI 科学家团队在材料、算法、工艺等方向具备自主提出假设、设计实验、验证结论的能力。 |
| 全链路贯通 | 打通设计→仿真→制造→测控的数据与工作流，与六大平台 API 级集成。 |
| 自主可控 | 核心组件基于开源/国产技术栈，大模型支持国产与本地部署。 |

### 1.3 术语与缩略语

| 术语 | 含义 |
|------|------|
| Gateway | 量子科研中枢网关，负责会话、鉴权、路由与协议适配。 |
| Brain | 多模型推理引擎 + 智能体路由（MoE）。 |
| Hands | 六大平台工具执行层，封装平台 API 为统一工具调用。 |
| Memory | 记忆与知识层，含工作记忆、项目记忆、知识图谱、向量库、数据仓库。 |
| Heartbeat | 自主科研心跳引擎，多层级定时/事件驱动任务。 |
| Skills | 量子科研技能市场，领域技能注册与执行。 |
| Agent | AI 科学家智能体（理论物理学家、材料科学家、芯片设计师、工艺工程师、设备运维员等）。 |
| MoE | Mixture of Experts，混合专家路由。 |

### 1.4 QuantaMind 与 OpenClaw 的架构对应（OpenClaw 在方案中的位置）

**QuantaMind 服务端架构源自 OpenClaw**。OpenClaw 是一套开源 Agent 框架（本地优先、自主运行、模型无关、技能扩展），其核心组件为 Gateway、Brain、Hands、Memory、Heartbeat、Skills。QuantaMind 将该通用架构**领域特化**为面向量子科技自主科研的“QuantumClaw”，各模块在详细设计中的对应关系如下：

| OpenClaw 通用组件 | QuantaMind（量智大脑）中的对应 | 本说明书章节 |
|-------------------|-----------------------------|---------------|
| **Gateway** | 量子科研中枢网关：会话、鉴权、协议适配、MoE 任务路由 | §3 Gateway 详细设计 |
| **Brain** | 多模型推理引擎 + 智能体路由（MoE）：四大领域大模型 + 专家小模型 + 通用基座 | §4 Brain 详细设计 |
| **Hands** | 六大平台工具执行层：启元/格物/墨子/悬镜/天元/开物 API 及通用工具 | §5 Hands 详细设计 |
| **Memory** | 量子科研知识持久层：工作记忆、项目记忆（Markdown）、知识图谱、向量库、数据仓库 | §6 Memory 详细设计 |
| **Heartbeat** | 自主科研心跳引擎：文献监控、实验设计、假设验证、战略洞察等多级循环 | §7 Heartbeat 详细设计 |
| **Skills** | 量子科研技能市场：设计/仿真/工艺/测控/科研等领域技能，Markdown+YAML 定义 | §8 Skills 详细设计 |

**在实现层面的关系**：

- **若采用 OpenClaw 代码库**：Gateway/Brain/Hands/Memory/Heartbeat/Skills 可基于 OpenClaw 现有实现做配置扩展与二次开发（如替换 Brain 为 MoE、扩展 Hands 为六大平台适配器），则 OpenClaw 位于**运行栈底层**，本说明书描述的是在其之上的“QuantumClaw 特化”行为与接口。
- **若独立实现**：不依赖 OpenClaw 源码，仅**借鉴其架构与命名**，则本说明书中的各章即为从零实现时的设计依据，与 OpenClaw 的对应关系仍如上表，用于与《QuantaMind…基于 OpenClaw 架构设计方案》保持一致。

因此，**OpenClaw 在方案中的位置**可概括为：**架构蓝本与组件映射源**；详细设计中的每一模块（§3–§8）都是对 OpenClaw 同名组件的“量子科研版”细化，而不是脱离 OpenClaw 的另起一套结构。

### 1.5 设计假设：六大平台已就绪与实时交互

**本详细设计采用以下前提假设**，以便在六大平台数据或实现尚未齐全的情况下，仍能明确 QuantaMind 与平台的交互契约与实时能力要求：

- **假设一（平台已建成）**：芯片设计系统（Q-EDA/启元）、芯片产线 MES 系统（墨子）、量子测控系统（悬镜）以及格物、天元、开物等，在设计与实现层面**视为已建成或按本说明书约定建设**，具备对 QuantaMind 暴露的标准化接口与实时交互能力。
- **假设二（数据中台已建成）**：**量电融合数据中台（数据中台）**视为已建成，具备全生命周期数据归集、治理、知识图谱与数据服务能力，并对 QuantaMind 暴露标准化查询与写入接口；本说明书 §5.11 约定其假设能力与 QuantaMind 的交互契约。**重要**：六大业务平台（启元、格物、墨子、悬镜、天元、开物）产生的业务数据**应统一归集并存储在数据中台**，数据中台为全平台数据的权威存储与服务中心，各平台除运行态缓存外，不另设独立持久化数据仓库与 QuantaMind 对接。
- **假设三（实时交互）**：上述平台与数据中台支持 QuantaMind 的**主动调用**（REST/同步或异步）与**被动接收**（可选：平台向 QuantaMind 推送事件或数据，如 MES 告警、测控校准完成、设计任务状态变更、数据中台新数据就绪），形成双向、可实时反馈的闭环。
- **假设四（契约先行）**：各平台及数据中台建设或改造时，以本说明书第 5 章中**三大优先平台与数据中台假设能力与实时交互设计**（§5.6–§5.11）为接口契约；QuantaMind 的 Hands、Memory 与 Heartbeat 按该契约实现调用与订阅，平台侧实现满足契约即可对接。

在此假设下，QuantaMind 的开发与联调可先基于**模拟/桩服务**验证流程，待平台与数据中台就绪后替换为真实端点，无需修改 QuantaMind 侧交互逻辑。

### 1.6 参考文档

- 《长三角一体化国家级AI+量子融合产业创新平台建设方案-详细版本》
- 《长三角…软件开发详细设计说明书》
- 《QuantaMind 量子科技自主科研人工智能中台 — 基于 OpenClaw 架构设计方案》

---

## 2. 系统架构

### 2.1 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│              用 户 层：QuantaMind 客户端（唯一入口）                 │
│        桌面客户端 │ Web 客户端 │ 嵌入式面板 │ CLI                 │
└─────────────────────────────┬─────────────────────────────────┘
                               │ HTTPS / WSS
┌─────────────────────────────▼─────────────────────────────────┐
│                    QuantaMind 服务端（量智大脑）                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │  Gateway    │  │   Brain     │  │  Heartbeat + Skills  │   │
│  │  会话/鉴权  │  │  路由/推理  │  │  自主任务/技能引擎   │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │
│         │                │                    │                │
│  ┌──────▼────────────────▼────────────────────▼──────────┐   │
│  │              AI 科学家智能体团队 (Agents)                │   │
│  └──────┬────────────────────────────────────┬────────────┘   │
│         │                │                    │                │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌─────────▼─────────┐     │
│  │   Hands     │  │   Memory    │  │  数据中台/知识图谱  │     │
│  │  工具执行   │  │  记忆/知识  │  │  对接               │     │
│  └──────┬──────┘  └─────────────┘  └────────────────────┘     │
└─────────┼─────────────────────────────────────────────────────┘
          │ REST / 消息 / 数据回写
┌─────────▼─────────────────────────────────────────────────────┐
│  启元 │ 格物 │ 墨子 │ 悬镜 │ 天元 │ 开物（六大业务平台）        │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 分层与职责

| 层级 | 组件 | 职责 |
|------|------|------|
| L0 表现层 | 桌面/Web/嵌入式/CLI 客户端 | 用户交互、会话维持、展示；不直连业务平台。 |
| L1 网关层 | Gateway | 会话管理、认证鉴权、协议适配、请求路由、流式输出。 |
| L2 智能层 | Brain、Heartbeat、Skills | 意图识别、MoE 路由、多模型推理、自主任务调度、技能执行。 |
| L3 智能体层 | 5+ AI 科学家 Agent | 领域任务执行、多 Agent 协同、与 Hands/Memory 交互。 |
| L4 执行与记忆层 | Hands、Memory | 平台 API 调用、知识持久化、图谱与向量检索。 |
| L5 业务平台层 | 六大平台 | 由 Hands 统一调用，不直接面向用户。 |

### 2.3 与建设方案“三层能力”的对应

| 建设方案能力层 | QuantaMind 实现 |
|----------------|-------------|
| 赋能工具层 | Skills + Hands：将平台能力封装为技能与工具，通过对话或 API 调用。 |
| 协同伙伴层 | Brain + Agents：任务分解、实验方案生成、平台资源调用、结果汇总。 |
| 自主发现层 | Heartbeat + Memory + Agents：假设挖掘、验证实验、知识沉淀与报告。 |

### 2.4 各层级技术栈与语言

各层级及主要组件的**推荐技术栈与开发语言**如下，便于实现选型与团队分工；具体实施时可根据自主可控与性能要求微调。

| 层级/组件 | 开发语言 | 技术栈/框架 | 说明 |
|-----------|----------|-------------|------|
| **L0 表现层** | | | |
| 桌面客户端 | JavaScript/TypeScript | Electron + Node.js | 跨平台安装包、与 Gateway 通信；可选 PyQt5/C++ Qt 做原生高性能客户端。 |
| Web 客户端 | TypeScript/JavaScript | React + Vite（或 Vue） | 浏览器访问，REST/WebSocket 与 Gateway 通信。 |
| 嵌入式面板 | TypeScript/JavaScript 或 C++/Python | 与 Q-EDA 宿主一致（如 Web 组件或 PyQt 插件） | 内嵌于 Q-EDA 等工具内的对话与设计加速入口。 |
| CLI 客户端 | Python 或 Shell | requests/websocket-client、argparse | 脚本与自动化场景。 |
| **L1 网关层** | | | |
| Gateway | **Python** | FastAPI + uvicorn、WebSocket、JWT/鉴权 | 会话管理、路由、流式输出；与 OpenClaw 风格一致，便于扩展。 |
| **L2 智能层** | | | |
| Brain（路由与推理） | **Python** | OpenClaw/自研、HTTP 调用 LLM API、可选 LangChain/自研 Agent 框架 | MoE 路由、多模型调用、与 Agent 编排。 |
| Heartbeat | **Python** | 定时任务（APScheduler/cron）、异步 IO | 多级心跳调度、调用 Brain/Hands/Memory。 |
| Skills 引擎 | **Python** | YAML/Markdown 解析、与 Brain/Hands 联动 | 技能加载、触发匹配、步骤执行。 |
| **L3 智能体层** | | | |
| AI 科学家 Agent | **Python** | 与 Brain 同进程或同语言；Prompt 与工具调用 | 领域 Agent 实现为 Python 模块或配置驱动的推理链。 |
| **L4 执行与记忆层** | | | |
| Hands | **Python** | requests/httpx、gRPC 客户端（可选）、平台 API 适配器 | 工具调用、平台 REST/gRPC、审批挂起逻辑。 |
| Memory | **Python** | Redis 客户端、文件 IO、Neo4j/py2neo、Milvus/pgvector 客户端、可选 SQLAlchemy | 工作记忆、项目记忆、知识图谱与向量检索、与数据中台对接。 |
| **L5 业务平台层** | | | |
| 启元（Q-EDA/全栈软件） | **C++/Python** | C++ 用于编译器/仿真核心；Python 用于 API 服务与脚本；可选 Node.js（若 Q-EDA 前端为 Web） | 性能敏感路径用 C++，服务与工具链用 Python。 |
| 墨子（MES） | **Java/Python 或 C++** | 工业常见为 Java/.NET；API 层可用 Python；实时采集可选 C++ | 见各平台详细设计。 |
| 悬镜（测控） | **C++/Python** | C++ 用于实时控制与采集；Python 用于校准逻辑与 API | 低延迟路径 C++，上层服务 Python。 |
| 格物/天元/开物 | **Python 为主**，可选 C++/Go | Python 服务与算法；高性能组件可用 C++/Go | 见各平台详细设计。 |
| **数据中台** | **Java/Python/Scala** | Kafka、Flink/Spark、GraphDB、向量库、REST/GraphQL 服务 | 大数据与实时流常用 Java/Scala；API 与算法可用 Python。 |

**语言与选型原则**：

- **QuantaMind 服务端（Gateway、Brain、Hands、Memory、Heartbeat、Skills）**：统一采用 **Python**，与 OpenClaw 生态及现有 QuantaMind 实现一致，便于快速迭代与 AI/ML 集成；性能瓶颈处可单独用 C++/Rust 实现扩展模块并由 Python 调用。
- **客户端**：桌面以 **JavaScript/TypeScript + Electron** 为主，Web 以 **TypeScript + React** 为主；嵌入式与宿主技术栈一致。
- **六大业务平台**：各平台按领域需求选型，**需对外暴露 REST/消息等标准接口**；性能关键路径（如仿真、测控实时）建议 C++，服务与 API 层建议 Python 或 Java。
- **数据中台**：以大数据与流处理技术栈为主，对外服务接口需支持 QuantaMind（Python）便捷调用（REST/GraphQL/Kafka 等）。

---

## 3. Gateway（网关）详细设计

### 3.1 职责边界

- 接收客户端连接（WebSocket / REST），维持会话生命周期。
- 认证鉴权：Token/JWT 或内网双向认证；支持多租户与项目隔离。
- 将请求路由至 Brain（对话/任务）或 Heartbeat/Skills 相关端点。
- 协议适配：统一内部语义，对外暴露 REST + WebSocket（含流式）。

### 3.2 核心接口（对外）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 健康检查 | GET | /health | 无鉴权，用于探活与负载均衡。 |
| 创建会话 | POST | /api/v1/sessions | 创建会话，返回 session_id。 |
| 查询会话 | GET | /api/v1/sessions/{id} | 查询会话元信息。 |
| 对话 | POST | /api/v1/chat | 请求体：session_id, message, stream（可选）；支持流式。 |
| WebSocket | WS | /ws | 建立长连接，消息类型：chat、task_status、heartbeat 等。 |
| 技能列表 | GET | /api/v1/skills | 返回可用技能列表（名称、描述、触发条件）。 |
| 工具列表 | GET | /api/v1/tools | 返回 Agent 可调用的工具列表（供前端展示或调试）。 |

### 3.3 会话与多租户

- **会话**：每个客户端连接对应一个会话；session_id 由服务端生成，建议 UUID。会话可绑定 project_id，用于数据隔离。
- **超时**：会话空闲超时（可配置，建议 30min）后关闭，客户端需重连或重新创建会话。
- **并发**：单会话内可串行处理多轮对话；单用户/项目可限制并发会话数（如 10）。

### 3.4 协议约定

- **REST**：JSON 请求/响应；Content-Type: application/json；错误返回 HTTP 4xx/5xx + JSON body（code, message）。
- **WebSocket**：消息格式 JSON；客户端发送 `{ "type": "chat", "payload": { "message": "..." } }`；服务端流式回复 `{ "type": "content", "data": "..." }`，结束为 `{ "type": "done" }`。
- **流式对话**：REST 下通过 Transfer-Encoding: chunked + SSE 或 NDJSON 返回；WS 下通过 type=content 逐片推送。

---

## 4. Brain（智能体路由与多模型推理）详细设计

### 4.1 组件构成

- **路由器（MoE）**：根据用户输入进行意图分类与领域判定，选择主 Agent 及可选的协同 Agent、领域模型。
- **多模型推理**：调用通用基座模型（通义/DeepSeek/Ollama）、垂直领域模型（量子物理/材料/工艺/视觉）、专家小模型（频率预测、T1/T2 预测等）。
- **推理协同**：支持链式（步骤依次执行）、并行（多模型同时推理再融合）两种模式。

### 4.2 路由策略

- **输入**：当前会话上下文 + 用户最新 message。
- **输出**：主 Agent、协同 Agent 列表、推荐领域模型、是否启用工具调用。
- **策略**：基于关键词/触发词（如“设计”“transmon”“工艺”“校准”）+ 可选分类器模型；复合任务路由至 Orchestrator，由协调者分解子任务并调度多 Agent。

路由决策表示例（可配置）：

| 意图/关键词 | 主 Agent | 协同 | 主要平台 |
|------------|----------|------|----------|
| 芯片设计、版图、Q-EDA | 芯片设计师 | 理论物理学家 | 启元 |
| 材料、超导、衬底 | 材料科学家 | 工艺工程师 | 格物 |
| 工艺、良率、MES | 工艺工程师 | 芯片设计师 | 墨子 |
| 校准、测控、T1/T2 | 设备运维员 | 理论物理学家 | 悬镜 |
| 算法、纠错、哈密顿量 | 理论物理学家 | — | 知识库/天元 |

### 4.3 模型配置（可配置 YAML/环境变量）

- **基座模型**：api 端点、model_id、temperature、max_tokens；fallback_chain 顺序。
- **领域模型**：qphysics-lm、qmaterial-lm、qprocess-lm、qvision-lm 的端点与触发词列表。
- **专家小模型**：frequency_predictor、t1t2_predictor、routing_quality 等，输入/输出 schema 与调用方式（本地 HTTP/内网 RPC）。

### 4.4 推理流程（单轮对话）

1. Gateway 将请求转至 Brain。
2. Brain 调用路由器，得到主 Agent + 模型 + 是否用工具。
3. 构造 prompt（系统角色 + 项目记忆摘要 + 对话历史 + 当前 message）。
4. 若需工具：先调用模型得到 tool_calls，转 Hands 执行，将结果再喂回模型，直至模型返回最终文本或结束。
5. 流式：每生成一段即通过 Gateway 推送给客户端；非流式：聚合后一次性返回。
6. 可选：将本轮对话与结果摘要写入 Memory（项目记忆/实验日志）。

---

## 5. Hands（工具执行层）详细设计

### 5.1 职责

- 将 Brain/Agent 下发的“工具调用”解析为对六大平台及通用能力的实际请求。
- 统一处理认证（平台侧 API Key/证书）、超时、重试、错误转换。
- 返回结构化结果给 Brain，便于模型生成下一句或最终答复。

### 5.2 工具注册与描述

- 每个工具具有：name、description、parameters（JSON Schema）、endpoint（URL 或内部服务名）、timeout、async（是否异步）。
- 工具列表可从配置文件或 Skills 中加载，通过 `/api/v1/tools` 暴露给前端/调试。

### 5.3 平台工具矩阵（概要）

| 平台 | 典型工具示例 | 说明 |
|------|--------------|------|
| 启元 | qeda_create_design, qeda_auto_route, ansys_simulate | 设计创建、布线、仿真提交。 |
| 格物 | materials_db_search, dft_calculator, suggest_recipe | 材料检索、计算、配方建议。 |
| 墨子 | mes_query, yield_report, process_trace | 工单、良率、追溯。 |
| 悬镜 | calibrate, benchmark, get_metrics | 校准、基准测试、指标。 |
| 天元 | submit_job, query_resource, get_result | 作业提交、资源、结果。 |
| 开物 | run_vqe, run_qaoa, quantum_ml | 量子算法、混合训练。 |
| 通用 | arxiv_search, file_ops, shell_exec | 文献、文件、脚本（需沙箱）。 |

### 5.4 调用约定

- **请求**：tool_name、arguments（JSON 对象）；可选 request_id 用于关联与去重。
- **响应**：success、data 或 error（code, message）；异步任务返回 task_id，由 Hands 或 Gateway 提供 task 状态查询。
- **超时与重试**：每个工具单独配置 timeout；可配置重试次数与退避策略；超时后返回明确错误，由 Agent 决定是否提示用户或换策略。

### 5.5 安全与审批

- 高风险操作（如 GDS 导出、制造任务提交）可配置为“需审批”：Hands 将请求挂起，生成审批单，审批通过后再实际调用平台 API；审批结果通过 Gateway 推送给客户端。

### 5.6 设计假设与三大优先平台总则

在**六大平台与数据中台数据/实现尚未齐全**的现状下，本设计假定**芯片设计系统（Q-EDA）、芯片产线 MES 系统、量子测控系统**以及**数据中台**已具备与 QuantaMind 实时交互的能力；格物、天元、开物可后续按同类契约扩展。以下 §5.7–§5.11 分别约定三系统与数据中台的**假设能力**、**与 QuantaMind 的交互方式**及**接口契约**，供平台建设与 Hands/Memory 开发共同遵守。交互模式统一为：

- **QuantaMind → 平台**：REST API 同步/异步调用（创建任务、查询状态、获取结果）；长耗时任务采用“提交 → 轮询/回调”模式。
- **平台 → QuantaMind**（可选）：WebSocket/SSE 事件推送或 Webhook 回调，用于任务状态变更、告警、校准完成等，便于 Heartbeat 与 Agent 实时响应。
- **数据回写**：平台按约定格式向 QuantaMind 或数据中台推送脱敏/聚合数据，支撑 Memory 与模型迭代。

### 5.7 芯片设计系统（Q-EDA / 启元）假设能力与实时交互

#### 5.7.1 假设能力（参考行业 Q-EDA 与量子芯片设计流程）

芯片设计系统在设计中**假定**具备以下能力，与业界量子 EDA（如参数化组件、自动布线、电磁仿真、DRC）及建设方案“启元”描述一致：

| 能力域 | 假设功能 | 说明 |
|--------|----------|------|
| 项目管理 | 创建/查询/归档设计项目 | 按芯片类型（transmon/xmon/fluxonium 等）、比特数、拓扑组织项目。 |
| 参数化组件 | 量子比特、耦合器、读出谐振器等组件库 | 支持几何与电学参数（pad 尺寸、JJ 面积、耦合长度等）；组件可编程放置与约束。 |
| 布局与布线 | 自动布局、自动布线、频率分配辅助 | 满足设计规则与串扰约束；支持 heavy-hex、grid 等拓扑。 |
| 设计规则检查（DRC） | 最小间距、金属密度、接地连续性等 | 返回违规列表与位置，供 Agent 迭代修改。 |
| 电磁仿真对接 | 本征模、驱动模、Q3D 等仿真任务提交与结果获取 | 支持异步提交；返回频率、Q 值、耦合系数等。 |
| 版图导出 | GDSII 或等效格式导出 | 用于交付制造（墨子）；可配置审批后导出。 |
| 设计-仿真闭环 | 根据仿真/测试结果反推参数建议 | 支持“目标频率 → 几何参数”等逆向推荐（可由 AI 代理模型或平台内置）。 |

#### 5.7.2 与 QuantaMind 的交互方式

- **QuantaMind → Q-EDA**：Hands 将 AI 芯片设计师 Agent 的“工具调用”转为对 Q-EDA 的 REST 调用，例如：创建设计、添加/修改组件、执行布线、提交 DRC、提交仿真、查询任务状态、获取结果、导出 GDS（经审批）。支持同步（轻量查询）与异步（仿真、批量 DRC）。
- **Q-EDA → QuantaMind**：可选。设计系统在**任务状态变更**（如仿真完成、DRC 完成、导出就绪）时，通过 Webhook 或消息总线向 QuantaMind 推送事件；QuantaMind 的 Heartbeat 或会话可据此更新状态并触发后续步骤（如“仿真已完成，请分析结果并给出下一轮参数建议”）。
- **嵌入式面板**：Q-EDA 前端可内嵌 QuantaMind 客户端组件；用户在设计界面内直接发起对话、调起“设计加速”技能，无需切窗；会话与 Gateway 保持同一 session。

#### 5.7.3 接口契约（Hands 侧期望）

以下为 Hands 对 Q-EDA 的**最小契约**，平台实现时提供对应 API 即可与 QuantaMind 联调（未实现前可用 Mock 替代）：

| 能力 | 方法 | 路径/动作 | 请求要点 | 响应要点 |
|------|------|-----------|----------|----------|
| 创建设计 | POST | /api/designs | chip_type, qubit_count, topology, project_id | design_id, created_at |
| 添加/更新组件 | POST/PATCH | /api/designs/{id}/components | type, params, position | component_id, status |
| 自动布线 | POST | /api/designs/{id}/route | algorithm, constraints | task_id（异步）或 result |
| DRC 检查 | POST | /api/designs/{id}/drc | rule_set | violations[] 或 task_id |
| 提交仿真 | POST | /api/designs/{id}/simulate | sim_type, freq_range | task_id |
| 查询任务 | GET | /api/tasks/{task_id} | — | status, result（若完成）|
| 导出 GDS | POST | /api/designs/{id}/export | format: gdsii | task_id 或 file_url |
| 事件推送（可选） | Webhook/WS | 平台配置的回调 URL 或 QuantaMind 订阅 | event: task_completed, design_id, task_id | QuantaMind 消费后更新 Memory/会话 |

### 5.8 芯片产线 MES 系统（墨子）假设能力与实时交互

#### 5.8.1 假设能力（参考半导体 MES 与建设方案“墨子”）

芯片产线 MES 在设计中**假定**具备以下能力，与半导体 MES 的工单、追溯、设备、良率及建设方案“黑灯工厂”“数字孪生”描述一致：

| 能力域 | 假设功能 | 说明 |
|--------|----------|------|
| 工单与批次 | 工单创建、下发、进度查询；批次（Lot）与晶圆/芯片追溯 | 与设计项目、版图版本、工艺路线绑定；支持工单状态机（待排产/生产中/完成/异常）。 |
| 工艺与配方 | 工艺路线、工序、配方（Recipe）管理；参数下发与采集 | 支持按设备与工序的工艺参数查询与历史追溯；可与数字孪生联动。 |
| 设备管理 | 设备状态、OEE、告警、维护工单 | 实时或近实时设备状态（运行/ idle/故障/维护）；告警可推送至 QuantaMind。 |
| 质量与良率 | 良率统计、SPC、缺陷分类、Wafer Map | 按批次/工序/设备的良率与关键参数；支持 QuantaMind 查询用于根因分析与工艺优化建议。 |
| 追溯 | 设计→制造→测控的批次与芯片级追溯 | 支持“某 GDS 版本 → 哪些 Lot → 哪些测控结果”的关联查询。 |
| 数字孪生对接 | 工艺仿真、排产仿真、参数优化建议执行 | 支持在孪生环境中验证工艺参数后再下发物理产线；QuantaMind 可提交“建议参数”由 MES/孪生评估。 |

#### 5.8.2 与 QuantaMind 的交互方式

- **QuantaMind → MES**：Hands 将 AI 工艺工程师、设备运维员等 Agent 的请求转为对 MES 的 REST 调用，例如：查询工单列表/详情、查询良率与 SPC、查询设备状态与告警、提交工艺参数建议（或审批后下发）、查询批次追溯。长耗时或批量统计可采用异步 + 轮询。
- **MES → QuantaMind**：**实时性关键**。MES 在**告警发生、工单状态变更、关键工序完成、良率异常**等事件时，通过 Webhook 或消息队列（如 Kafka）向 QuantaMind 推送；QuantaMind 的 Heartbeat（L0 实时监控）消费后可选：更新 Memory、生成待办、触发 Agent 分析（如“某设备告警，请设备运维员给出建议”）。推送内容需脱敏与分级，符合数据安全约定。
- **数据回写**：MES 按约定周期或事件向数据中台/QuantaMind 推送聚合数据（如工序良率、设备 OEE、工艺参数分布），供 Memory 与工艺模型训练。

#### 5.8.3 接口契约（Hands 侧期望）

| 能力 | 方法 | 路径/动作 | 请求要点 | 响应要点 |
|------|------|-----------|----------|----------|
| 工单列表/详情 | GET | /api/work-orders, /api/work-orders/{id} | status, design_id, time_range | list 或 detail（含 lot、工序、状态）|
| 良率/SPC 查询 | GET | /api/analytics/yield, /api/analytics/spc | lot_id, process_step, time_range | aggregates, time_series |
| 设备状态与告警 | GET | /api/equipment/status, /api/equipment/alerts | equipment_id, active_only | status, alerts[] |
| 工艺参数建议（可选）| POST | /api/process/suggestions 或 /api/digital-twin/evaluate | process_step, params, design_context | acceptance, suggested_adjustment |
| 追溯查询 | GET | /api/traceability | design_id 或 lot_id 或 chip_id | chain: design → lots → steps → test |
| 事件推送（可选）| Webhook/Kafka | 平台配置 | event: alarm, wo_status_change, step_complete | QuantaMind 订阅并处理 |

### 5.9 量子测控系统（悬镜）假设能力与实时交互

#### 5.9.1 假设能力（参考量子测控与建设方案“悬镜”）

量子测控系统在设计中**假定**具备以下能力，与业界自动化校准、T1/T2/保真度测量及建设方案“万比特级测控”“一键校准”“基准测试”描述一致：

| 能力域 | 假设功能 | 说明 |
|--------|----------|------|
| 校准 | 单比特/双比特光谱、Rabi、门校准、读出优化；一键或分步自动化校准 | 支持按芯片/比特列表发起校准任务；返回校准后参数（频率、幅值、相位等）。 |
| 性能测量 | T1、T2、随机基准测试（RB）、门保真度、SPAM 误差 | 支持单比特与双比特；结果结构化返回（数值+不确定度），供 QuantaMind 写入 Memory 与报告。 |
| 基准测试（Benchmarking）| Quantum Volume、CLOPS 等标准或自定义基准 | 支持任务提交与结果查询；可与“中国标准”评测体系对齐。 |
| 实时控制与读出 | 脉冲序列下发、IQ 采集、实时反馈（如实时纠错解码）| 面向研究或闭环实验；可提供“运行作业”类 API，QuantaMind 通过 Hands 提交作业并取回结果。 |
| 系统健康 | 测控链路状态、制冷机状态、比特可用性 | 支持 QuantaMind 查询当前系统是否可接受校准/测量任务；异常时可接收推送告警。 |

#### 5.9.2 与 QuantaMind 的交互方式

- **QuantaMind → 测控**：Hands 将 AI 设备运维员、理论物理学家等 Agent 的请求转为对测控系统的 REST 调用，例如：发起校准任务、查询校准状态、发起 T1/T2/RB 测量、查询基准测试结果、查询系统健康与比特可用性。校准与测量多为长耗时，采用异步提交 + 轮询或回调。
- **测控 → QuantaMind**：**实时性重要**。测控系统在**校准完成、测量完成、系统异常（如制冷机报警、比特失效）**时，通过 Webhook 或消息推送至 QuantaMind；Heartbeat 或 Agent 可据此更新实验记录、触发“分析本轮校准结果并建议下一组实验”等闭环。
- **数据回写**：测控按约定向 QuantaMind/数据中台推送校准后参数、T1/T2/保真度时间序列与统计，支撑 Memory 与代理模型/良率模型迭代。

#### 5.9.3 接口契约（Hands 侧期望）

| 能力 | 方法 | 路径/动作 | 请求要点 | 响应要点 |
|------|------|-----------|----------|----------|
| 发起校准 | POST | /api/calibration/run | qubit_ids, calibration_type, options | task_id |
| 校准状态/结果 | GET | /api/calibration/tasks/{id} | — | status, result（params, metrics）|
| T1/T2/RB 测量 | POST | /api/measurement/run | measurement_type, qubit_ids, options | task_id |
| 测量结果 | GET | /api/measurement/tasks/{id} 或 /api/measurement/results | task_id 或 filter | values, uncertainties, timestamp |
| 基准测试 | POST/GET | /api/benchmark/run, /api/benchmark/results | benchmark_type, params | task_id 或 report |
| 系统健康 | GET | /api/system/health, /api/qubits/availability | — | status, available_qubits[], alerts |
| 事件推送（可选）| Webhook/WS | 平台配置 | event: calibration_done, measurement_done, system_alert | QuantaMind 订阅并处理 |

### 5.10 三大平台与 QuantaMind 的端到端数据流（假设已就绪）

在三大平台均按上述契约就绪的前提下，典型端到端流如下，供实现与联调参考：

1. **设计 → 制造 → 测控**  
   - QuantaMind（AI 芯片设计师）通过 Hands 调用 Q-EDA 创建设计、布线、DRC、仿真；仿真通过后经审批导出 GDS。  
   - QuantaMind 或 MES 将 GDS 与工单关联；MES 排产并下发产线；墨子在关键节点（如工序完成、良率汇总）向 QuantaMind 推送事件。  
   - 芯片下线后，测控系统执行校准与基准测试；测控将结果推送给 QuantaMind；QuantaMind 将设计参数–工艺参数–测控结果关联写入 Memory，支撑下一轮设计迭代与代理模型训练。

2. **实时监控与闭环**  
   - Heartbeat L0 定期轮询或订阅 MES 告警、测控健康；发现异常时生成待办或触发 Agent（如设备运维员）分析。  
   - 测控校准完成事件触发 QuantaMind 更新项目记忆并可选触发“实验设计”心跳，推荐下一组实验参数。

3. **数据飞轮**  
   - 设计参数、MES 良率与工艺参数、测控 T1/T2/保真度按约定写入数据中台或 Memory；QuantaMind 的模型与技能据此持续优化，实现“越用越准”的迭代加速。

### 5.11 数据中台假设能力与实时交互

#### 5.11.1 设计假设与数据归属原则

**数据中台（量电融合数据中台）**在设计中**假定已建成**，作为全平台数据枢纽与 AI 能力中台的“数据燃料库”，与建设方案中“建设量子科技知识图谱与数据中台”的描述一致。

**数据归属原则**：**六大业务平台（启元、格物、墨子、悬镜、天元、开物）产生的业务数据应统一存储在数据中台**。即：设计域（Q-EDA 设计、仿真结果等）、制造域（MES 工单、良率、工艺参数等）、测控域（校准结果、T1/T2、基准测试等）、应用域（天元作业与结果、开物 QML 运行等）、材料与器件域（格物）等，均由各平台按约定格式与周期**写入数据中台**，由数据中台负责持久化、治理与对外服务。QuantaMind 与各业务系统仅从数据中台拉取或订阅所需数据，不在业务平台侧重复建设面向 QuantaMind 的独立数据仓库。各平台可保留运行态缓存与实时接口（如任务状态查询），但**持久化业务数据以数据中台为准**。

QuantaMind 的 Memory 与 Brain 依赖数据中台提供上述归集后的设计/制造/测控/知识数据，并回写洞察与训练数据，形成“数据→AI→洞察→决策→新数据”闭环。

#### 5.11.2 假设能力（参考建设方案数据中台）

| 能力域 | 假设功能 | 说明 |
|--------|----------|------|
| 全生命周期数据归集 | 设计、制造、测控、应用各域数据采集与入湖 | **六大业务平台（启元、格物、墨子、悬镜、天元、开物）产生的业务数据统一写入数据中台**；来自 Q-EDA、MES、测控、格物、天元、开物等的结构化与非结构化数据，按统一标准入数据湖；支持实时流（Kafka 等）与批量导入。数据中台为上述数据的权威存储。 |
| 数据治理与标准 | 数据清洗、标注、分级分类、脱敏 | 支持按项目/敏感级的数据访问策略；为 AI 训练与检索提供合规数据。 |
| 知识图谱 | 动态演进的量子科技知识图谱 | 实体（材料、器件、工艺、算法、论文、专利、项目等）与关系；支持从文献、平台数据自动抽取与人工校验；与 QuantaMind Memory 的图谱查询对接。 |
| 数据服务与 API | 统一查询、联邦查询、训练数据集供给 | 支持 REST/GraphQL 按需查询；支持按主题/时间/项目筛选的训练数据集导出（供 Brain 模型训练与微调）。 |
| 数据反馈与闭环 | 接收 QuantaMind 或平台的写入与更新 | 接收工艺建议、设计版本、实验结论等回写；更新知识图谱与统计视图，供下一轮检索与训练使用。 |

#### 5.11.3 与 QuantaMind 的交互方式

- **QuantaMind → 数据中台**：  
  - **Memory**：通过数据中台 API 或消息总线**拉取**脱敏/聚合数据（如设计域统计、良率汇总、测控指标时间序列），用于知识图谱与向量库更新、RAG 检索、项目记忆补充。  
  - **Brain**：请求训练数据集（按主题/时间/项目）、知识图谱查询（实体、关系、路径）、联邦查询（跨域统计）；支持同步查询与异步大批量导出。  
  - **Heartbeat**：定时或事件触发时从数据中台拉取最新数据摘要，用于文献关联、实验设计推荐、假设挖掘等。

- **数据中台 → QuantaMind**：  
  - **可选推送**：当新数据就绪（如某批次测控结果入湖、知识图谱增量更新）时，通过 Webhook 或消息主题通知 QuantaMind；QuantaMind 的 Heartbeat 或 Agent 可据此触发“新数据可用，请更新模型或生成报告”等任务。  
  - **数据回写**：各平台与 QuantaMind 按约定向数据中台**写入**任务级/统计级数据；数据中台负责持久化、治理与再暴露给 QuantaMind 查询。

#### 5.11.4 接口契约（Memory/Brain 侧期望）

以下为 QuantaMind 对数据中台的**最小契约**，数据中台实现时提供对应能力即可与 QuantaMind 联调（未实现前可用 Mock 或本地数据层替代）：

| 能力 | 方法/方式 | 路径/动作 | 请求要点 | 响应/说明 |
|------|-----------|-----------|----------|-----------|
| 知识图谱查询 | GET / POST | /api/graph/query 或 GraphQL | entity_type, filters, path_query, limit | 实体列表、关系、路径结果 |
| 向量/检索服务 | POST | /api/retrieval/search | query_embedding 或 query_text, top_k, filters | 相似文档/片段列表（供 RAG）|
| 训练数据集供给 | GET / POST | /api/datasets/request 或 /api/datasets/{id}/export | domain, time_range, project_id, format | 任务 id 或文件/流（脱敏后）|
| 数据写入/回写 | POST | /api/ingest 或 /api/events | topic, payload（设计摘要、工艺建议、实验结论等）| 写入确认或 event_id |
| 实时数据流（可选）| 订阅 | Kafka 等主题（如 design.updated, mes.yield, qc.calibration）| QuantaMind 订阅所需主题 | 数据中台向主题推送，QuantaMind 消费 |
| 新数据就绪通知（可选）| Webhook | 数据中台配置的回调 URL | event: data_ready, domain, scope | QuantaMind 收到后触发拉取或任务 |

#### 5.11.5 与 Memory 的职责划分

- **Memory**：负责 QuantaMind 内部的工作记忆（Redis）、项目记忆（Markdown）、以及可选的本体知识图谱与向量库**缓存/镜像**；对**持久化、全平台共享、大规模训练数据**的权威数据源为数据中台。  
- **数据中台**：负责**六大业务平台数据的统一存储**及全生命周期数据的**归集、治理、知识图谱主库、训练数据集生成**；对 QuantaMind 暴露查询与写入接口，不直接承载 QuantaMind 的会话或实时工作记忆。各业务平台产生的持久化数据以数据中台为准，QuantaMind 仅从数据中台拉取或订阅。  
- 在数据中台未就绪时，Memory 可仅使用本地/文件/Redis 存储，并预留与数据中台对接的适配器；数据中台就绪后开启同步或拉取，无需改动 Memory 上层逻辑。

---

## 6. Memory（记忆与知识）详细设计

### 6.1 存储层级

| 层级 | 名称 | 存储介质 | 内容 | TTL/策略 |
|------|------|----------|------|----------|
| L1 | 工作记忆 | Redis | 当前会话上下文、进行中任务状态、Agent 间消息 | 24h |
| L2 | 项目记忆 | 文件系统（Markdown） | 项目说明、设计决策、实验记录、偏好 | 持久 |
| L3 | 知识图谱 | Neo4j | 实体（材料、器件、工艺、论文等）与关系 | 持久 |
| L4 | 向量库 | Milvus/pgvector | 论文摘要、设计描述、报告等嵌入 | 持久 |
| L5 | 数据仓库 | PostgreSQL/ClickHouse | 设计参数、仿真结果、良率等结构化数据 | 持久 |

### 6.2 知识图谱（L3）

- **实体类型**：Qubit、Material、Process、Device、Paper、Experiment、Person、Project 等。
- **关系**：工艺-材料、算法-硬件、论文-引用等；支持从平台数据与文献自动抽取 + 人工校验。
- **接口**：面向 Brain/Agent 的查询 API：按实体类型/属性查询、路径查询、摘要生成；可选自然语言转 Cypher/查询模板。

### 6.3 向量库（L4）与 RAG

- **索引内容**：文献摘要、设计规范、历史设计说明、实验报告等文本的嵌入。
- **检索**：用户或 Agent 提问时，先做向量检索取 Top-K 相关片段，再与 prompt 一起送入模型（RAG）。
- **更新**：新论文、新项目总结、新实验报告写入后，异步或定时生成嵌入并写入向量库。

### 6.4 项目记忆（L2）与自动沉淀

- **路径**：按 project_id 组织目录，如 `memory/projects/{project_id}/`，下含 `context.md`、`experiments/*.md`、`decisions.md` 等。
- **沉淀时机**：Agent 完成设计/实验/分析后，由 Brain 或专用模块生成摘要，追加到对应 Markdown；可选同时触发知识图谱与向量库更新。

### 6.5 与数据中台对接

- **设计假设**：数据中台已建成（见 §1.5 假设二、§5.11）。Memory 与数据中台的对接按 §5.11.4 接口契约实现。  
- **拉取**：Memory 从数据中台拉取脱敏/聚合数据（REST/GraphQL/Kafka 订阅），用于知识图谱与向量库更新、RAG 检索、项目记忆补充。  
- **写入**：**六大业务平台**按规范向数据中台推送/写入本平台产生的任务级与统计级数据（设计、制造、测控、应用、材料等），数据中台为上述数据的统一存储；QuantaMind 的洞察与训练相关回写也写入数据中台。数据分级与合规按《建设方案》与平台约定执行。  
- **未就绪时**：数据中台未就绪时，Memory 仅使用本地存储并预留数据中台适配器；就绪后开启对接即可。

---

## 7. Heartbeat（心跳与自主任务）详细设计

### 7.1 多层级循环

| 层级 | 名称 | 建议周期 | 主要任务 |
|------|------|----------|----------|
| L0 | 实时监控 | 5min | 仿真任务状态、MES 告警、测控健康、DRC 预警。 |
| L1 | 文献监控 | 6h | arXiv 等检索、摘要、与项目相关性、推送。 |
| L2 | 实验设计 | 12h | 分析已完成实验、贝叶斯推荐下一组参数、生成实验草案。 |
| L3 | 假设验证 | 24h | 从知识图谱挖掘假设、设计并执行验证仿真、更新图谱与报告。 |
| L4 | 战略洞察 | 7d | 周度进展分析、风险与机会、竞争态势、周报。 |

### 7.2 配置方式

- 通过配置文件（如 YAML）或管理 API 定义各 level 的 interval、active_hours、tasks 列表、是否需要审批、资源上限（如 GPU 小时）。
- 敏感任务（如自动提交制造）可设为需人工审批；Heartbeat 只生成建议或待办，不直接执行。

### 7.3 执行与状态

- 调度器按周期触发各 level；任务执行时调用 Brain/Agents 与 Hands，结果写回 Memory 或推送通知（如飞书/邮件）。
- 提供 `/api/v1/heartbeat/status`、`/api/v1/heartbeat/discoveries` 等接口，供客户端展示“自主发现”与运行状态。

### 7.4 与 Gateway 的关系

- Heartbeat 作为服务端内部组件，不直接对外暴露；客户端通过 Gateway 的 REST/WS 获取心跳状态与发现列表。

---

## 8. Skills（技能）详细设计

### 8.1 定位

- Skills 将量子科研领域能力封装为可复用、可触发的“技能”，每个技能对应一组步骤、所需工具与可选 Agent。
- 与 OpenClaw 的 Skill 定义兼容（Markdown + YAML front matter），便于从社区或内部扩展。

### 8.2 技能定义结构（YAML + Markdown）

- **元数据**：name、version、trigger（触发词/正则）、tools、agents、domain。
- **正文**：步骤说明（Step 1/2/3…）、输入输出约定、异常处理；供人与 Agent 理解执行流程。

示例（节选）：

```yaml
name: transmon-quantum-bit-design
version: 1.0.0
trigger: "设计transmon|创建量子比特|transmon design"
tools: [qeda_create_design, qeda_add_qubit, frequency_predictor, qeda_check_drc]
agents: [designer_agent, theorist_agent]
domain: quantum_chip_design
```

### 8.3 技能加载与执行

- **加载**：启动时或热加载时扫描技能目录，解析 YAML + Markdown，注册到技能引擎；通过 `/api/v1/skills` 返回列表。
- **执行**：用户输入匹配 trigger 或显式指定技能名时，由 Brain 或 Orchestrator 按技能步骤调用 Agent 与 Hands，直至完成或失败。
- **版本**：技能支持版本号，配置中可指定默认使用的版本，便于灰度与回滚。

### 8.4 技能分类（建议目录结构）

- design/：芯片设计（transmon、xmon、布线、频率分配等）。
- simulation/：仿真分析（本征模、EPR、串扰、代理模型等）。
- fabrication/：工艺（配方优化、良率预测、缺陷分类等）。
- characterization/：测控（光谱、T1/T2、校准、基准测试等）。
- research/：文献、假设生成、实验设计、论文辅助等。
- orchestration/：芯片迭代闭环、设计-制造交接、多 Agent 协同等。

---

## 9. AI 科学家智能体详细设计

### 9.1 角色清单

| Agent | 角色名 | 主模型倾向 | 主要能力 | 绑定平台 |
|-------|--------|------------|----------|----------|
| theorist_agent | AI理论物理学家 | 量子物理模型 | 哈密顿量、纠错理论、文献、算法 | 知识库、天元 |
| material_agent | AI材料科学家 | 材料模型 | 材料预测、DFT、实验设计 | 格物 |
| designer_agent | AI芯片设计师 | 通用+专家模型 | 版图、布线、仿真、DRC、迭代 | 启元 |
| process_agent | AI工艺工程师 | 工艺模型 | 工艺优化、良率、SPC、DFM | 墨子 |
| devops_agent | AI设备运维员 | 通用 | 校准、故障诊断、基准测试 | 悬镜 |
| orchestrator | 协调者 | 通用 | 任务分解、多 Agent 调度、冲突仲裁 | 全平台 |

### 9.2 Agent 能力与工具绑定

- 每个 Agent 在配置中声明 capabilities（自然语言描述）、tools（可调用的 Hands 工具列表）、memory_scope（可读/写的 Memory 区域）。
- 执行时由 Brain 或 Orchestrator 将任务分发给对应 Agent，Agent 通过 Brain 调用 LLM 与 Hands，结果可写回 Memory 并返回给协调者或用户。

### 9.3 多 Agent 协同模式

- **链式（Chain）**：理论物理学家 → 材料科学家 → 芯片设计师 → 工艺工程师 → 设备运维员；适用于从零到交付的全流程。
- **星形（Star）**：以芯片设计师为中心，其余 Agent 提供建议；适用于设计迭代。
- **辩论（Debate）**：多 Agent 提出方案与异议，Orchestrator 仲裁；适用于关键决策。
- **并行（Parallel）**：多 Agent 独立出方案，评分后选优；适用于探索性设计。

模式由 Orchestrator 根据任务类型选择，或在技能定义中指定。

### 9.4 与建设方案智能体的对应

- 建设方案中的“AI理论物理学家”“AI材料科学家”“AI芯片设计师”“AI工艺工程师”“AI设备运维员”与本说明书中的 5 大 Agent 一一对应；Orchestrator 对应“智能体路由”中的协调与分解职责。

---

## 10. 客户端详细设计

### 10.1 形态与场景

| 形态 | 技术选型 | 场景 |
|------|----------|------|
| 桌面客户端 | Electron（已实现安装包）/ PyQt | 主力形态，全功能、内网/离线。 |
| Web 客户端 | 浏览器 + 内网地址 | 轻量查看、审批、看板。 |
| 嵌入式面板 | Q-EDA 等工具内嵌 iframe/组件 | 设计时即调起对话与设计加速。 |
| CLI | 命令行脚本 | 脚本化、CI、自动化。 |

### 10.2 与 Gateway 的通信

- **桌面/Web**：默认通过 HTTPS + WebSocket 连接 Gateway 的 base_url（如 `https://quantamind.example.com` 或内网 IP）；会话创建后携带 session_id 发起对话与任务请求。
- **嵌入式**：同域或配置 CORS；若 Q-EDA 与 Gateway 同域，可直接使用同一 session。
- **CLI**：通过 REST 创建会话并轮询或流式拉取回复；可选 API Key 写入配置文件或环境变量。

### 10.3 功能范围（客户端侧）

- **必须**：登录/鉴权、会话创建与恢复、发送消息、接收流式/非流式回复、展示技能与工具列表（可选）。
- **可选**：任务列表与状态、心跳与自主发现展示、设计加速入口、项目/记忆浏览（若 Gateway 暴露相应 API）。

### 10.4 不归属客户端的能力

- 业务逻辑、路由、推理、工具执行、记忆写入、心跳调度均仅在服务端；客户端不直连六大平台。

---

## 11. 接口规范

### 11.1 通用约定

- **Base URL**：`/api/v1`；版本可通过 URL 或 Header 体现。
- **认证**：Header `Authorization: Bearer <token>` 或 `X-API-Key: <key>`；WebSocket 可在建立时通过 query 或首帧传递 token。
- **错误响应**：HTTP 状态码 + JSON body：`{ "code": "ERR_xxx", "message": "..." }`；可选 request_id 便于排查。

### 11.2 主要请求/响应示例

**创建会话**

- 请求：`POST /api/v1/sessions`，body `{}` 或 `{ "project_id": "optional" }`。
- 响应：`{ "session_id": "uuid", "created_at": "ISO8601" }`。

**对话**

- 请求：`POST /api/v1/chat`，body `{ "session_id": "uuid", "message": "文本", "stream": true }`。
- 流式响应：chunked 或 SSE，每行/每块为 JSON：`{ "type": "content", "data": "..." }` 或 `{ "type": "tool_call", "name": "...", "args": {} }`，结束 `{ "type": "done" }`。
- 非流式响应：`{ "reply": "完整回复文本" }`。

**技能列表**

- 请求：`GET /api/v1/skills`。
- 响应：`{ "skills": [ { "name", "version", "description", "trigger" } ] }`。

**工具列表**

- 请求：`GET /api/v1/tools`。
- 响应：`{ "tools": [ { "name", "description", "parameters" } ] }`。

### 11.3 与六大平台的接口（Hands 侧）

- 由各平台提供 REST/消息接口；Hands 按平台文档调用，统一封装为工具。**三大优先平台（Q-EDA、MES、测控）与数据中台的假设能力与接口契约**见 §5.6–§5.11；请求/响应格式、异步任务轮询、事件推送约定以该处为准。数据回写格式由数据中台或平台约定。在平台或数据中台未就绪阶段，Hands/Memory 可对接**模拟/桩服务**实现相同契约，便于 QuantaMind 端到端联调。

---

## 12. 非功能性设计

### 12.1 安全

- **网络**：内网部署为主；若对外暴露则 TLS 全链路；可选 mTLS。
- **身份与权限**：统一认证（LDAP/AD 或本地）；RBAC（管理员/科学家/工程师/观察者）；项目级数据隔离。
- **AI 安全**：高风险工具调用可配置审批；Agent 操作可审计；模型输出可做安全过滤与敏感信息脱敏。
- **数据**：敏感数据加密存储；密钥集中管理；合规与审计日志。

### 12.2 性能与可用性

- **延迟**：对话首字 P99 建议 &lt; 2s（依赖模型与网络）；工具调用超时单独配置。
- **扩展**：Gateway、Brain 无状态水平扩展；会话与工作记忆依赖 Redis，可集群。
- **高可用**：关键组件多实例 + 负载均衡；数据库/Redis 主从或集群；避免单点。

### 12.3 可观测性

- **日志**：结构化日志（JSON），含 request_id、session_id、level、message。
- **指标**：QPS、延迟分位、错误率、队列深度、各模型/工具调用耗时；Prometheus 格式暴露。
- **追踪**：request_id 贯穿 Gateway → Brain → Hands；可选 OpenTelemetry 与分布式追踪。

### 12.4 可扩展性

- **Agent**：新增 Agent 通过配置注册，声明能力与工具即可接入路由与协同。
- **技能**：新增 Markdown+YAML 技能文件并加载即可。
- **模型**：新增领域模型或专家模型时，在 Brain 配置中注册路由与端点即可。
- **平台**：新平台通过 Hands 增加工具定义与适配器即可，符合统一调用与安全规范。

---

## 13. 部署与运行

### 13.1 运行环境

- **推荐**：Linux 服务器（内网）；Python 3.10+；Redis；可选 Neo4j、Milvus/pgvector、PostgreSQL、Kafka（与数据中台对接时）。
- **配置**：通过环境变量或配置文件指定 Gateway 端口、模型端点、平台 API 地址、Memory 存储路径、Heartbeat 周期等。

### 13.2 进程与部署方式

- **单体**：单进程内聚 Gateway、Brain、Hands、Memory、Heartbeat、Skills（当前 QuantaMind 实现方式），适合开发与小规模部署。
- **拆分**：可将 Gateway 与 Brain 拆成独立服务，通过内网 HTTP/gRPC 调用；Hands、Memory、Heartbeat 可作为 Brain 的依赖或独立微服务，按规模与运维习惯选择。

### 13.3 配置项要点

- Gateway：host、port、session_ttl、max_concurrent_sessions。
- Brain：基座/领域/专家模型 endpoint 与 key、路由策略、temperature。
- Hands：各工具 endpoint、timeout、重试、审批开关。
- Memory：Redis 地址、文件路径、Neo4j/Milvus 连接串。
- Heartbeat：各 level 的 interval、active_hours、tasks、审批与资源上限。
- 客户端：Gateway base_url、认证方式（Token/API Key）。

### 13.4 与实施阶段对应

- **第一阶段（2026–2027）**：Gateway + 单模型对话 + 基础工具（至少 1 个平台）+ 桌面客户端 + 可选 Heartbeat L0；对应量智大脑 V0.9。**三大优先平台（Q-EDA、MES、测控）与数据中台可先以 Mock/桩服务实现 §5.7–§5.11 契约**，使 QuantaMind 与 Hands/Memory 完成联调与技能验证；待平台与数据中台就绪后切换为真实端点即可。
- **第二阶段（2028–2029）**：全系列 Agent、MoE 路由、多平台 Hands、Memory L2–L4、Heartbeat 多级；对应量智大脑 V1.0。建议 Q-EDA、MES、测控与**数据中台**按契约上线真实接口，并开通**平台 → QuantaMind 事件推送**及**数据中台新数据就绪通知**，实现实时闭环。
- **第三阶段（2030）**：自主科研闭环、知识图谱与数据飞轮成熟、全面智能化；对应量智大脑 V2.0。

---

## 14. 业务流

### 14.1 概述

业务流描述 QuantaMind 中**典型业务场景的端到端流程**，包括谁发起、经哪些组件、与平台如何协作、何时结束或进入下一环节。与第 5 章（Hands/平台契约）、第 9 章（Agent）配合，用于实现与联调时的流程对齐。

### 14.2 对话与任务流（单轮/多轮）

| 步骤 | 执行方 | 动作 |
|------|--------|------|
| 1 | 用户/客户端 | 发起会话（可选带 project_id），发送 message（可带 stream=true）。 |
| 2 | Gateway | 鉴权、绑定 session，将请求转 Brain。 |
| 3 | Brain | 意图识别与路由，选定主 Agent 及是否用工具；构造 prompt（含 Memory 检索摘要、对话历史）。 |
| 4 | Brain/Agent | 调用 LLM；若返回 tool_calls，则转 Hands 执行工具，将结果再喂回 LLM，循环直至无 tool_call 或结束。 |
| 5 | Hands | 按工具名调用对应平台 API（Q-EDA/MES/测控/数据中台等），返回结构化结果给 Brain。 |
| 6 | Brain | 将最终回复（文本或含结构化摘要）流式或一次性返回 Gateway。 |
| 7 | Gateway | 推送给客户端（WS 或 chunked）；可选将本轮摘要写入 Memory。 |

**分支**：若工具为“需审批”操作，Hands 挂起并生成审批单，流程暂停；用户审批通过后 Hands 继续执行，结果再回 Brain 与用户。

### 14.3 设计加速流（芯片设计 → 仿真 → 迭代）

| 步骤 | 执行方 | 动作 |
|------|--------|------|
| 1 | 用户/技能 | 通过自然语言或技能触发“设计某芯片”（如 transmon、码距、目标保真度）。 |
| 2 | Brain/Orchestrator | 路由至芯片设计师 Agent（可协同理论物理学家）；分解为：需求澄清 → 拓扑与频率分配 → 版图 → 仿真 → DRC → 导出。 |
| 3 | 芯片设计师 Agent + Hands | 调用 Q-EDA：创建设计、添加组件、自动布线、提交 DRC、提交仿真（异步）；轮询任务状态。 |
| 4 | Q-EDA | 返回设计 ID、任务 ID、仿真结果、违规列表等；可选推送“仿真完成”事件。 |
| 5 | Agent | 分析结果，若不满足目标则生成参数调整建议并重新调用 Q-EDA（迭代）；满足则进入导出或交付制造。 |
| 6 | 可选 | 导出 GDS 经审批后调用 Q-EDA 导出接口；设计元数据与关键参数写 Memory/数据中台。 |

### 14.4 制造-测控闭环流（设计 → MES → 测控 → 反馈）

| 步骤 | 执行方 | 动作 |
|------|--------|------|
| 1 | 上游 | 设计阶段产出 GDS 及设计版本号；与 MES 工单/工艺路线绑定。 |
| 2 | MES | 工单下发、批次生产；关键工序完成或良率异常时向 QuantaMind 推送事件（可选）。 |
| 3 | QuantaMind/Heartbeat 或 Agent | 消费 MES 事件或定时拉取良率/设备状态；工艺工程师 Agent 可分析并给出工艺建议（或写入数字孪生评估）。 |
| 4 | 测控 | 芯片下线后执行校准、T1/T2/RB、基准测试；完成后向 QuantaMind 推送或由 QuantaMind 轮询结果。 |
| 5 | QuantaMind | 将设计参数–工艺参数–测控结果关联写入 Memory/数据中台；设备运维员或芯片设计师 Agent 可生成“本轮结论与下一轮设计建议”。 |
| 6 | 闭环 | 下一轮设计迭代利用上述数据（代理模型、知识图谱、历史实验）加速收敛。 |

### 14.5 自主科研心跳流

| 步骤 | 执行方 | 动作 |
|------|--------|------|
| 1 | Heartbeat 调度器 | 按配置周期（如 5min/6h/24h/7d）触发对应 level。 |
| 2 | Heartbeat | 执行该 level 的任务列表：如拉取 MES 告警、测控健康、数据中台最新摘要、文献检索、假设挖掘等。 |
| 3 | 可选 | 调用 Brain/Agent 完成“分析告警”“推荐下一组实验参数”“生成周报”等；或仅写 Memory/待办，由用户或后续会话处理。 |
| 4 | 输出 | 更新 Memory、推送通知（飞书/邮件）、或通过 Gateway 暴露“自主发现”列表供客户端展示。 |

### 14.6 审批流（高风险操作）

| 步骤 | 执行方 | 动作 |
|------|--------|------|
| 1 | Agent/Hands | 需审批的工具调用（如 GDS 导出、制造任务提交）到达 Hands。 |
| 2 | Hands | 不直接调用平台 API，而是生成审批单（含操作类型、参数、请求来源），状态置为“待审批”。 |
| 3 | Gateway | 将审批单推送给客户端（或审批中心）；可选 WebSocket 推送。 |
| 4 | 用户/审批人 | 在客户端或审批界面通过/拒绝。 |
| 5 | Gateway/Hands | 收到审批结果；通过则 Hands 执行原工具调用并返回结果，拒绝则向 Agent 返回“用户拒绝”等语义。 |

---

## 15. 数据流

### 15.1 概述

数据流描述系统中**数据的来源、去向、格式与触发方式**，包括客户端与 QuantaMind 之间、QuantaMind 内部各组件之间、QuantaMind 与六大平台及数据中台之间的数据传递与持久化，便于实现接口、存储与合规设计。

### 15.2 客户端 ↔ Gateway

| 方向 | 内容 | 协议/格式 |
|------|------|-----------|
| 客户端 → Gateway | 创建会话、发送 message、查询会话/任务、审批操作、心跳轮询 | REST JSON；WebSocket JSON 帧 |
| Gateway → 客户端 | session_id、流式回复（content 片段）、tool_call 展示、任务状态、审批待办、心跳状态 | REST chunked/SSE/NDJSON；WebSocket 推送 |

**不经过 Gateway 的数据**：客户端不直连平台；所有业务数据经 Gateway 进入或离开 QuantaMind。

### 15.3 Gateway ↔ Brain

| 方向 | 内容 |
|------|------|
| Gateway → Brain | 会话 id、用户 message、stream 标志、可选 project_id；可带近期对话历史或由 Brain 自读 Memory。 |
| Brain → Gateway | 流式文本块、或最终 reply；可选 tool_call 列表（由 Gateway 转 Hands，结果再回 Brain）；错误码与 message。 |

**内部**：可为同步 HTTP 或内网 RPC；请求建议带 request_id 以便追踪。

### 15.4 Brain ↔ Hands

| 方向 | 内容 |
|------|------|
| Brain → Hands | 工具名、参数字典（JSON）；可选 request_id、session_id。 |
| Hands → Brain | 执行结果：success、data 或 error（code, message）；异步任务为 task_id，Brain 或 Gateway 负责轮询后再次喂回 Brain。 |

### 15.5 Brain / Heartbeat ↔ Memory

| 方向 | 内容 |
|------|------|
| 读 | 项目记忆摘要、会话相关上下文、知识图谱查询结果、向量检索结果（RAG）、训练数据集元信息。 |
| 写 | 会话摘要、项目记忆追加、实验记录、设计决策摘要；可选触发知识图谱与向量库更新。 |

**存储分层**：见 §6；工作记忆（Redis）、项目记忆（文件）、图谱/向量/数仓可分别由 Memory 模块对接。

### 15.6 QuantaMind ↔ 六大平台（Hands 侧）

| 方向 | 内容 |
|------|------|
| QuantaMind → 平台 | 见 §5.7–§5.9 接口契约：设计/工单/测控等 API 的请求（JSON），异步任务为 POST 后 GET 轮询或回调。 |
| 平台 → QuantaMind | 同步 API 的响应（JSON）；异步任务结果；可选 Webhook/事件推送（任务完成、告警、校准完成等），由 QuantaMind 订阅或接收。 |

**数据格式**：请求/响应体以 JSON 为主；大文件或流式按平台约定（如 file_url、分片上传）。

### 15.7 QuantaMind ↔ 数据中台

| 方向 | 内容 |
|------|------|
| QuantaMind → 数据中台 | **拉取**：Memory/Brain/Heartbeat 通过 REST/GraphQL/Kafka 消费：知识图谱查询、向量检索、训练数据集、主题数据摘要。**写入**：任务级/统计级数据回写（设计摘要、工艺建议、实验结论、运行日志等），见 §5.11.4。 |
| 数据中台 → QuantaMind | 查询结果（实体、关系、文档列表、数据集）；可选“新数据就绪”Webhook 或 Kafka 事件，触发 QuantaMind 拉取或执行任务。 |

### 15.8 数据流总览图

```
                     ┌─────────────────────────────────────────────────────────┐
                     │                      客户端                              │
                     │            (消息 / 流式回复 / 审批 / 状态)                 │
                     └─────────────────────────┬─────────────────────────────────┘
                                               │ REST / WebSocket
                     ┌─────────────────────────▼─────────────────────────────────┐
                     │  Gateway  ←────────────────────────────────────────────  │
                     │    会话、鉴权、路由、流式输出、审批推送                    │
                     └───┬───────────────────────────────┬──────────────────────┘
                         │ 请求/上下文                    │ 回复/事件
                         ▼                               ▲
                     ┌───▼───────────────────────────────┴──────────────────────┐
                     │  Brain  ←→  Memory（读/写 记忆、图谱、向量、检索）        │
                     │    路由、推理、Agent、工具调度                             │
                     └───┬─────────────────────────────────────────────────────┘
                         │ 工具名+参数                    │ 工具结果
                         ▼                               ▲
                     ┌───▼───────────────────────────────┴──────────────────────┐
                     │  Hands：调用平台 API / 审批挂起 / 事件接收                 │
                     └───┬───────────────────────────────────┬──────────────────┘
                         │ 请求/回写                          │ 响应/推送
         ┌───────────────┼───────────────┬───────────────────┼───────────────┐
         ▼               ▼               ▼                   ▼               ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────┐
    │ Q-EDA   │   │  MES    │   │  测控   │   │ 格物/   │   │  数据中台   │
    │ 启元    │   │ 墨子    │   │ 悬镜    │   │天元/开物│   │ (拉取/写入) │
    └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────────┘
```

### 15.9 数据持久化与保留

- **Gateway**：会话元数据可落库或 Redis；对话内容按策略可仅留日志或同步写入 Memory。
- **Memory**：工作记忆 TTL 见 §6；项目记忆、图谱、向量、数仓持久化，保留策略与数据中台一致或按项目配置。
- **平台与数据中台**：**六大业务平台的业务数据统一存储在数据中台**，由各平台按约定写入数据中台，数据中台负责持久化与对外服务。QuantaMind 仅保存为完成任务所必需的副本或摘要，及训练/分析用脱敏数据；持久化业务数据的权威来源为数据中台，符合数据分级与合规要求。

---

## 附录 A：文档修订记录

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-03 | 初稿，量智大脑=QuantaMind 详细设计 | — |
| V1.1 | 2026-03 | 增加设计假设（§1.5）；三大优先平台（Q-EDA、MES、测控）已就绪与实时交互设计（§5.6–§5.10）；接口契约与端到端数据流 | — |
| V1.2 | 2026-03 | 增加数据中台已建成假设（§1.5 假设二）；数据中台假设能力与实时交互设计（§5.11）；Memory 与数据中台职责划分（§5.11.5、§6.5）| — |
| V1.3 | 2026-03 | 新增 §14 业务流（对话与任务、设计加速、制造-测控闭环、心跳、审批）；§15 数据流（客户端↔Gateway、Brain↔Hands↔Memory、与平台/数据中台、总览图、持久化）| — |
| V1.4 | 2026-03 | 明确六大业务平台数据统一存储在数据中台（§1.5 假设二、§5.11.1 数据归属原则、§5.11.2 能力表、§5.11.5、§6.5、§15.9）| — |
| V1.5 | 2026-03 | 新增 §2.4 各层级技术栈与语言（L0–L5 及数据中台的语言与框架约定）| — |

---

## 附录 B：与架构设计文档的对应

| 本说明书章节 | 《QuantaMind…基于 OpenClaw 架构设计方案》对应 |
|-------------|-------------------------------------------|
| §2 系统架构（含 §2.4 技术栈与语言）| §4 总体架构、附录 A 技术栈总览 |
| §3 Gateway | §5 QuantumClaw Gateway |
| §4 Brain | §6 QuantumBrain、MoE 路由 |
| §5 Hands | §7 QuantumHands |
| §6 Memory | §8 QuantumMemory |
| §7 Heartbeat | §9 QuantumHeartbeat |
| §8 Skills | §10 QuantumSkills |
| §9 Agents | §11 AI 科学家智能体团队 |
| §10 客户端 | §2 QuantaMind 的呈现形态 |
| §12 非功能性 | §15 安全与权限体系 |
| §14 业务流 | 典型业务流程（对话、设计加速、制造-测控闭环、心跳、审批）|
| §15 数据流 | 数据流向、接口数据、与架构设计“数据流与集成架构”对应 |

---

*本说明书为 QuantaMind（量智大脑）的详细设计文档，与《建设方案》及《软件开发详细设计说明书》中“量智大脑”部分一致，量智大脑即 QuantaMind。*
