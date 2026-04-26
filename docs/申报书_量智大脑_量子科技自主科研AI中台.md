# 国家重点研发计划项目申报书

## 项目名称：量子科技自主科研人工智能中台关键技术研究与系统研制

---

## 封面信息

| 项目 | 内容 |
|------|------|
| 项目名称 | 量子科技自主科研人工智能中台关键技术研究与系统研制 |
| 申报指南方向 | 量子信息技术 / 人工智能与量子计算融合 |
| 项目负责人 | （填写） |
| 申请单位 | 量子计算工业软件工程技术研发中心 |
| 合作单位 | （填写） |
| 起止年限 | 2026年1月—2030年12月（5年） |
| 申请总经费 | （填写，万元） |
| 项目摘要 | 本项目针对我国量子计算全链路研发中工具孤岛、数据碎片、模型与工具脱节、自主科研能力薄弱等核心问题，研究并研制面向量子科技的自主科研人工智能中台系统（量智大脑）。项目围绕五项关键技术展开：（1）量子科学混合专家推理引擎，突破 Tool Call 协议标准化与多轮工具调用链稳定性问题；（2）以 Run 模型与协同控制平面为核心的多智能体系统，解决父子任务建模、上下文预算分配与并行子任务汇聚问题；（3）面向量子专业工具的分级执行运行时与标准化适配器，打通设计-仿真-制造-测控全链路；（4）基于知识本体的动态演进知识图谱与检索增强生成（RAG）体系；（5）Heartbeat 驱动的自主科研闭环引擎与 Artifact-first 产物体系。预期实现单轮设计-仿真迭代周期缩短30%以上，形成一套自主可控的量子科技 AI 中台软件系统与标准规范体系。 |

---

## 目录

- 一、立项依据
- 二、研究目标
- 三、主要研究内容与技术路线
- 四、技术创新点与考核指标
- 五、年度研究计划与里程碑
- 六、项目基础与研究条件
- 七、研究队伍与分工
- 八、经费预算概算
- 九、预期成果及应用前景

---

## 一、立项依据

### （一）国内外研究现状与发展趋势

**1. 自主科研 AI 系统的理论基础与工程现状**

AI 自主科研（Autonomous AI Research）是指以 AI 智能体为主体，完成"假设生成—实验设计—工具调用—结果分析—知识沉淀"全闭环的科研范式。其核心技术基础包含三个层面：

一是**大模型推理能力**。以 GPT-4、Claude 系列为代表的大型语言模型（LLM）已具备多步推理、代码生成和工具调用（Function Calling / Tool Use）能力，但在量子科技等高度专业化领域，通用模型存在显著的领域适配性不足问题——模型对哈密顿量、约瑟夫森结参数、量子纠错编码等专业概念的理解精度不足，直接限制了其在量子工程任务上的可用性。

二是**工具调用与执行编排能力**。ReAct（Reason + Act）范式、Tool-Augmented Language Model（TALM）、AgentBench 等研究工作已验证了 LLM 通过结构化 Tool Call 与外部系统交互的可行性。但现有研究多局限于简单工具（Web 搜索、代码执行、文件读写），缺乏面向仿真软件、制造执行系统（MES）、低温测控设备（ARTIQ）等量子专业系统的深度集成研究，工具调用的可靠性、权限隔离和异步容错机制尚未得到系统性解决。

三是**多智能体协同与任务分解能力**。近年来，AutoGen、CrewAI、LangGraph 等多智能体框架探索了基于"角色扮演 + 消息传递"的协同机制，但均缺乏对复杂工程场景（长任务、父子任务关系、并行子任务合并、子智能体独立上下文预算）的显式建模，难以支撑量子芯片研制这类多阶段、多专业协同的科研工程任务。

**2. 量子科技专用工业软件的技术现状与差距**

量子芯片研制全链路涉及的软件工具如下：设计层——Qiskit Metal（超导量子芯片参数化版图设计）、KQCircuits（VTT 开发的量子芯片 GDS 生成框架）、qEDA（自研量子电子设计自动化工具）；仿真层——Ansys HFSS（微波本征模仿真）、Ansys Q3D Extractor（电容矩阵提取）、PyEPR / BBQ（能量参与比分析）；制造层——ChipMES/OpenMES（微纳制造 MES）、SECS-II/GEM 设备通信协议；测控层——ARTIQ（先进实时基础设施量子物理，NIST 标准实时测控框架）、Qiskit Pulse（脉冲级别量子门校准）、Mitiq（量子误差缓解）、QCoDeS（量子器件测量自动化）。

上述工具均以独立系统形式运行，数据接口不统一、格式多样（GDS、HDF5、JSON、InfluxDB、SQL），研发人员在不同工具间手动搬运参数、转换格式、同步状态，仅"数据搬运"工作估计消耗科研人力的30%以上。目前国内外均未出现能够统一编排上述工具且支持 AI 驱动的工业级中间件平台，这是本项目重点突破的技术空白。

**3. 量子科研知识体系的形式化表示研究进展**

超导量子器件知识具有高度图结构特征：量子比特（Qubit）、谐振腔（Resonator）、约瑟夫森结（JJ）、耦合器（Coupler）之间的物理关系（耦合强度 $g$、色散频移 $\chi$、Purcell 衰减率 $\kappa_P$）构成天然的知识图谱拓扑。现有工作以结构化数据库（如 Materials Project、AFLOW）为主，尚无专注量子芯片全链路的领域知识图谱。

在检索增强生成（RAG）领域，Dense Passage Retrieval（DPR）、Hybrid BM25+Dense、HyDE（Hypothetical Document Embeddings）等方法已有成熟实现，但针对量子科技领域的长文档切片策略（如如何保留哈密顿量公式与器件参数的上下文关联）、专业术语向量化对齐问题尚无针对性研究。

**4. 当前量子科技 AI 系统存在的核心技术瓶颈**

（1）**上下文窗口瓶颈**：量子芯片设计文档、仿真报告、工艺规范动辄数万词，超出当前主流推理模型（包括本地部署的 qwen、llama 系列）上下文窗口限制，导致关键信息丢失，严重影响推理质量。

（2）**工具执行可靠性瓶颈**：量子仿真（HFSS 求解一次本征模可能需要数十分钟至数小时）、制造工单提交（实时性要求高且不可逆）等操作对工具执行的超时控制、重试策略、幂等性保障提出了严格要求，现有框架缺乏工业级可靠性设计。

（3）**多任务协同状态管理瓶颈**：量子芯片单次迭代涉及设计→仿真→制造→测控四个阶段，每个阶段可能并行运行多个子任务，且各子任务状态需要跨轮次持久化、跨智能体共享，现有聊天驱动的状态管理（基于消息列表）无法满足这一需求。

（4）**知识沉淀与复用瓶颈**：量子科研经验（如"某芯片 T1 下降15%的根因是约瑟夫森结氧化层不均匀，通过调整双角度蒸镀角度解决"）难以从非结构化对话记录中自动提取并转化为可检索的结构化知识条目。

### （二）项目立项的必要性与紧迫性

**1. 核心软件"空心化"风险亟需系统性破解**

我国量子计算研制团队对 Qiskit Metal、ARTIQ 等国际开源工具深度依赖。上述工具由美国团队主导开发，一旦遭遇断源或许可限制，研发流程将面临严重中断风险。国内虽已开展部分国产替代工作（如 qEDA、自研 MES），但各子系统仍缺乏统一的 AI 调度中枢。量智大脑通过构建自主可控的工具适配层与编排层，可有效降低单点依赖风险，并为国产工具提供统一的 AI 集成接口。

**2. AI+量子融合的系统工程问题尚无完整解决方案**

AI 工具（LLM + Agent）与量子专业工具（仿真、制造、测控）的融合是一个系统工程问题，涉及协议适配、上下文管理、执行运行时、知识体系等多个技术层面。目前国内外均缺乏面向量子科技的完整解决方案。本项目从技术框架层面对上述问题进行系统性攻关，研究成果具有唯一性和不可替代性。

**3. 当前研究基础确立了可行路径，需要工程化突破**

项目组已完成 QuantaMind V1.x 原型系统开发，验证了 Gateway→Brain→Orchestrator→Hands→Memory→Heartbeat 六模块架构的可行性，并初步完成多类量子专业工具的适配器原型。但原型系统存在若干已识别的工程瓶颈：对话入口承载过多长任务压力导致吞吐下降、多智能体协同停留在"多角色单入口"尚未形成显式协同控制平面、工具执行缺少分级运行时（query/mutation/long_running/delivery 未区分）、上下文装配粗粒度导致大量无效 Token 消耗。这些瓶颈在量智大脑 V2.0 技术路线中均有明确解决方案，本项目将系统性地推进其工程化实现。

---

## 二、研究目标

### （一）总体目标

以"控制平面—执行平面—数据平面—客户端壳层"四层架构为基础，建立量子科技自主科研人工智能中台系统，解决量子科技 AI 中台五项核心技术问题，产出可工程化部署的完整软件系统、技术标准与知识资产。

### （二）分阶段目标

**第一阶段（2026—2027年）：核心技术攻关与 V1.0 系统研制**

- 完成四层系统架构（Shell / Control Plane / Execution Plane / Data Plane）完整实现；
- 完成量子科学垂直大模型 V1.0（含量子物理专用模型）训练与评测；
- 完成以 Run 模型为核心的多智能体协同控制平面 V1.0；
- 完成面向 ≥30 类工具的分级执行运行时（ToolRuntime）；
- 完成量子科技知识图谱 V1.0（≥10万节点）；
- 完成 ≥3 个端到端典型场景验证。

**第二阶段（2028—2029年）：系统集成与示范应用**

- 完成量智大脑 V2.0 系统，AI 赋能覆盖关键研发环节 ≥50%；
- 完成全链路（设计-仿真-制造-测控）场景示范；
- 完成标准规范体系 ≥3 项；
- 申请发明专利 ≥10 项。

**第三阶段（2030年）：全面完善与推广**

- 完成系统全面验收，形成可复制推广方案；
- 发表 SCI 一区论文 ≥3 篇；
- 完成软件著作权 ≥10 项。

---

## 三、主要研究内容与技术路线

### （一）系统总体架构

**图 1 量智大脑平台技术体系架构图**

量智大脑系统整体采用"四层架构"设计（如图1所示）：

- **壳层（Shell Layer）**：面向用户的交互入口，包含桌面工作台（Desktop Workspace）、Web 控制台（Web Console）、命令行客户端（CLI）和嵌入式面板（Embedded Panel）四种形态，通过统一 API / WebSocket / SSE 与控制平面通信。
- **控制平面（Control Plane）**：系统的调度核心，包含 RunCoordinator（运行协调器）、ContextAssembler（上下文装配器）、CoordinationEngine（多智能体协同引擎）、ApprovalRouter（审批路由器）、ShortcutRegistry（快捷路径注册表）和 SessionFacade（会话门面）六大组件。
- **执行平面（Execution Plane）**：负责实际计算与工具执行，包含 ModelRuntime（模型运行时）、ToolRuntime（工具运行时）、WorkerRuntime（工作者运行时）和 MCPRuntime（MCP 远程工具运行时）。
- **数据平面（Data Plane）**：持久化与知识基础设施，包含 ArtifactStore（产物存储）、RunStateStore（运行状态存储）、ProjectMemory（项目记忆）、KnowledgeBase + VectorIndex（知识库与向量索引）、DataWarehouse（数据仓库）。

本项目五项研究内容与四层架构的对应关系如下：研究内容一对应 ModelRuntime 中的混合专家推理引擎；研究内容二对应 Control Plane 中的 RunCoordinator + CoordinationEngine；研究内容三对应 ToolRuntime + Integrations；研究内容四对应 Data Plane 中的 KnowledgeBase + VectorIndex；研究内容五对应 Heartbeat 驱动的自主闭环引擎 + ArtifactStore。

---

### 研究内容一：量子科学混合专家推理引擎与 Tool Call 协议

#### 1. 科学问题

量子科技 AI 推理面临三个核心科学问题：（1）**领域语义鸿沟**——通用大模型对超导量子电路 Hamiltonian $H = \sum_i \omega_i a_i^\dagger a_i - \sum_i \frac{E_C^{(i)}}{12}(a_i^\dagger - a_i)^4 + \sum_{ij} g_{ij}(a_i^\dagger a_j + a_i a_j^\dagger)$ 等物理公式的语义理解准确率与领域专家相比差距悬殊；（2）**工具调用链稳定性**——在多步 Tool Call 循环（≥10 轮）中，由于上下文累积与错误传播，工具选择准确率快速下降；（3）**上下文预算约束**——量子仿真报告、设计文档、工艺规范的上下文长度远超本地部署模型（典型 qwen2.5:7b 上下文窗口为8K～32K Token）的处理能力上限。

#### 2. 研究目标

构建面向量子科技的混合专家（MoE）推理引擎，实现：（1）量子物理专用模型基准任务准确率较通用基座模型提升 ≥20%；（2）多步 Tool Call 链（≥15轮）成功完成率 ≥85%；（3）上下文压缩后关键信息保留率 ≥95%。

#### 3. 研究内容

**（1）量子科学领域专用语料库与基准评测集构建**

语料库采集来源包括：arXiv quant-ph/cond-mat 领域论文（≥50万篇摘要，≥10万篇全文解析）；量子芯片设计文档、仿真报告、工艺规范（内部数据，需脱敏处理）；量子计算教材与专利文献。语料预处理流程包括：公式 LaTeX 标准化、器件参数数值标注（标注格式：`<param name="Ec" unit="GHz" value="0.15"/>`）、噪声文档过滤（BERT 困惑度筛选）。评测集构建参考 QuantBench 框架设计，包含量子参数推理（如给定 $E_J/E_C$，推断 transmon 非谐性）、工艺问答（刻蚀工序识别）、仿真结果解读（给定 $S_{21}$ 曲线，提取耦合强度）三类题型，共 ≥3000 道标注题目。

**（2）混合专家推理引擎架构研究**

ModelRuntime 采用以下多层推理架构：

```
用户请求
    │
    ▼
[ 任务分类器 ]  ←── 量子领域意图识别（Transformer 分类头，Fine-tuned）
    │
    ├── 量子物理/理论推理  ──► 量子物理专用模型（SFT + RLHF）
    ├── 代码生成/脚本     ──► 代码专用模型（DeepSeek-Coder / Qwen-Coder）
    ├── 工艺/数据分析     ──► 通用模型（qwen2.5 / Llama3）
    └── 高频确定性指令    ──► ShortcutRegistry（直通，不经 LLM）
```

专家路由策略：基于 Task Embedding 相似度的软路由（Soft Router），而非 hard switch。各专家输出通过加权汇聚（attention-based merging），支持单专家激活和多专家协同两种模式。模型后端接口统一遵循 OpenAI API 兼容格式，同时支持 Ollama 本地后端、vLLM 推理后端和云端 API，通过 `runtimes/models/router.py` 动态切换，实现本地/云端混合推理。

**（3）Tool Call 协议标准化研究**

研究量子工程 Tool Call 协议扩展规范（在 OpenAI Function Calling 基础上扩展以下字段）：

```json
{
  "name": "sim_run_eigenmode",
  "class": "long_running",          // query | mutation | long_running | delivery
  "timeout_ms": 3600000,
  "idempotent": false,
  "approval_required": false,
  "artifact_output": "simulation_report",
  "parameters": {
    "project_path": { "type": "string" },
    "setup_name":   { "type": "string" },
    "num_modes":    { "type": "integer", "default": 5 }
  }
}
```

多轮 Tool Call 稳定性研究：针对工具调用链超过15轮的场景，研究工具结果摘要压缩（Tool Result Compaction）算法，将已完成工具结果压缩为结构化摘要而非原始返回值，降低上下文 Token 消耗；研究工具调用死循环检测算法，基于调用图（Tool Call Graph）的环检测防止工具重复无效调用。

**（4）量子场景上下文装配器（ContextAssembler）研究**

ContextAssembler 负责在推理前将多源上下文按预算动态装配，其核心数据结构为上下文预算（Context Budget）：

```
ContextBudget {
  total_limit:    int       // 模型上下文窗口上限（Token）
  allocation: {
    system_context:          15%   // Agent 身份 + 工具定义
    project_memory_context:  20%   // 项目历史摘要
    recent_conversation:     25%   // 最近 N 轮对话
    artifact_context:        20%   // 相关 Artifact 摘要
    knowledge_rag_context:   15%   // RAG 检索结果
    tool_result_context:     5%    // 工具返回结果（compressed）
  }
}
```

研究量子科技文档的**语义感知切片算法**（Semantic-Aware Chunking）：针对包含物理公式和器件参数表的技术文档，设计保留公式上下文的切片策略（不在公式中间截断，保留公式前后2段上下文）；研究**上下文缓存机制**（Context Cache），对同一项目的系统提示和知识库段落建立 KV Cache，避免跨请求重复编码。

#### 4. 技术路线

**图 2 Gateway 与客户端接入架构图**

基础设施：量子物理专用模型基于 qwen2.5-72B 或等效开源模型进行领域持续预训练（CPT）→ 监督微调（SFT）→ 基于人类反馈的强化学习（RLHF）三阶段训练流程；混合专家路由的任务分类器采用 BERT-Base 结构微调，推理时在 CPU 上完成（<10ms），不引入额外 GPU 负担；Tool Call 协议基于 JSON Schema Draft-07 扩展；ContextAssembler 实现为独立服务，与 Gateway 通过内部 gRPC 接口通信。

---

### 研究内容二：以 Run 模型为核心的量子科研多智能体协同系统

#### 1. 科学问题

多智能体系统在量子科研场景面临三个核心问题：（1）**Run 生命周期建模**——量子科研任务（如"对当前芯片批次做 T1/T2 统计分析并给出工艺优化建议"）是持续数小时甚至数天的长生命周期任务，如何将其抽象为可持久化、可中断恢复、可审计的运行实体（Run）；（2）**父子任务依赖与并发控制**——主任务与子智能体任务之间存在依赖关系（如仿真任务完成后才能进行参数分析），且子任务可能并行运行，需要支持 DAG 拓扑的任务调度和结果汇聚；（3）**子任务上下文隔离**——每个子智能体需要独立的上下文视图（避免跨任务知识污染），但同时需要从父任务继承必要的项目上下文。

#### 2. 研究目标

建成以 Run 模型为核心的多智能体协同控制平面，支持 ≥10 类专业智能体协同运行，多智能体协同任务成功率 ≥80%，全部 Run 操作可审计，关键任务支持审批路由。

#### 3. 研究内容

**（1）统一 Run 数据模型研究**

研究面向量子科研的统一 Run 模型，其核心数据结构如下：

```python
@dataclass
class Run:
    run_id:      str
    run_type:    RunType       # chat_run | digest_run | pipeline_run
                               # simulation_run | calibration_run | data_sync_run
    parent_run_id: Optional[str]
    agent_id:    str
    status:      RunStatus     # pending | running | waiting_approval
                               # paused | completed | failed | cancelled
    context_snapshot: dict     # 运行时上下文快照
    budget:      RunBudget     # token_limit, tool_calls_limit, wall_time_limit
    artifacts:   List[ArtifactRef]
    events:      List[RunEvent]
    policy:      RunPolicy     # timeout, retry, fallback, approval_rules
    created_at:  datetime
    completed_at: Optional[datetime]
```

量子科研场景对应的 RunType 如下：`chat_run`（交互问答）、`digest_run`（情报摘要生成）、`pipeline_run`（设计-仿真-测控流水线）、`simulation_run`（HFSS/Q3D 仿真）、`calibration_run`（量子比特校准序列）、`data_sync_run`（数据中台 ETL 同步）、`repair_run`（异常修复执行）。所有 Run 状态变迁记录为不可变事件（RunEvent），支持完整历史回放。

**（2）多智能体协同控制平面设计与实现**

协同控制平面（CoordinationEngine）包含以下五个核心组件：

- **Coordinator**：接收父任务，判断是走快捷路径（ShortcutRegistry）、单智能体路径，还是多智能体协同路径；
- **Planner**：将父任务分解为协同计划（CoordinationPlan），生成包含子任务节点、执行顺序（串行/并行）、依赖边的有向无环图（DAG）；
- **Delegation**：按 DAG 拓扑顺序向 SpecialistAgent 派发子 Run；
- **Merger**：等待所有子 Run 完成，按预定汇聚策略（concat / summarize / vote / rank）合并结果，生成父任务的 Artifact；
- **Supervisor**：监控子 Run 健康状态，处理子任务超时（触发 fallback 策略）、失败（触发 retry 或跳过策略）和子任务间死锁（基于等待图检测）。

典型量子芯片设计-仿真协同流程的 DAG 结构示例：

```
用户: "评估当前 20-qubit 芯片的频率碰撞风险并给出调参建议"
    │
    ▼  [Planner 分解]
    ├─ SubRun_A: AI芯片设计师 → qeda_get_chip_spec()  // 获取当前芯片频率规格
    ├─ SubRun_B: AI仿真工程师 → sim_run_eigenmode()    // 仿真本征模 [依赖A]
    ├─ SubRun_C: AI理论物理学家 → theorist_frequency_collision_check()  // 碰撞分析 [依赖B]
    └─ SubRun_D: AI芯片设计师 → theorist_design_proposal()  // 参数调优建议 [依赖C]
                                    │
                                    ▼  [Merger 汇聚]
                               综合评估报告 Artifact
```

研究 Planner 的任务分解算法：基于 Chain-of-Thought 引导 LLM 生成结构化 DAG（JSON 格式），结合量子科研流程知识图谱（包含常见科研任务的标准分解模式）作为先验约束，提升生成 DAG 的可靠性。

**（3）智能体能力画像（Agent Profile）体系研究**

升级 V1 基于关键词的 Agent Registry 为基于能力画像的多维度智能体描述体系：

```python
@dataclass
class AgentProfile:
    agent_id:          str
    role_name:         str              # "AI芯片设计师"
    tool_prefixes:     List[str]        # ["metal_", "kqc_", "qeda_"]
    context_layers:    List[ContextLayerType]  # 该 Agent 需要哪些上下文层
    allowed_run_types: List[RunType]    # 允许触发的 Run 类型
    shortcut_ids:      List[str]        # 允许走的快捷路径
    artifact_outputs:  List[ArtifactType]  # 该 Agent 产出的 Artifact 类型
    collaboration_role: CollabRole      # planner | specialist | executor | merger
    context_budget_override: Optional[ContextBudget]
    approval_policy:   ApprovalPolicy   # 哪些操作需要人工审批
```

研究基于 Embedding 相似度的语义路由（替代 V1 中的关键词匹配）：用户输入经向量化后，与各 Agent 的能力描述向量做余弦相似度排序，选择 Top-k Agent（k=1 或多个参与协同），提升路由准确率。

**（4）审批路由与人机协同机制研究**

研究面向量子工程高风险操作的分级审批机制（ApprovalRouter），按操作风险等级划分五类：

| 操作类型 | 风险等级 | 默认审批策略 |
|------|------|------|
| query（只读查询） | 低 | 自动执行 |
| mutation（参数修改） | 中 | 日志记录 + 事后审计 |
| device_command（设备指令） | 高 | 实时弹窗确认 |
| mes_operation（制造工单） | 极高 | 人工审批 + 双人确认 |
| delivery（外部推送） | 中 | 首次人工确认，后续自动 |

#### 4. 技术路线

**图 3 子任务二：Brain 与 Orchestrator 工具循环示意图**

Run 持久化采用 PostgreSQL，状态变迁基于 event sourcing 模式；CoordinationEngine 与 RunCoordinator 通过异步消息队列（asyncio Queue）通信；Planner 的 DAG 生成采用 JSON Schema 约束的结构化输出（Structured Output），防止生成无效拓扑；子智能体的上下文隔离通过 ContextAssembler 的 `fork_budget(parent_run_id)` 接口实现，继承父任务的项目记忆层但隔离对话层。

---

### 研究内容三：量子专业工具分级执行运行时与全链路适配器体系

#### 1. 科学问题

量子工具集成面临三个核心工程问题：（1）**工具异质性**——设计工具（Python 库调用，毫秒级）、仿真软件（进程调用，小时级）、制造系统（HTTPS API，实时性要求高且不可重试）、测控设备（ARTIQ 实时系统，微秒级时序精度）四类工具的执行语义、超时特征、幂等性要求截然不同，不能用同一套执行机制；（2）**跨系统数据一致性**——同一个约瑟夫森结的参数在设计系统（GDS 坐标）、仿真系统（HFSS 结构参数）、测控系统（Qiskit Pulse 脉冲幅度）中采用不同表示，需要研究统一的参数语义映射；（3）**执行安全与权限边界**——AI 自主调用 MES 系统下发工单、对 ARTIQ 系统执行脉冲序列存在物理风险，必须建立工具级权限隔离和审批机制。

#### 2. 研究目标

建成面向量子科技的工具分级执行运行时（ToolRuntime），标准化接入 ≥30 类工具，六大类系统全链路连通率 ≥95%，工具接口标准化率100%。

#### 3. 研究内容

**（1）工具分级执行运行时（ToolRuntime）设计**

研究按工具行为特征划分的四级执行运行时：

```
Level 1 - query:        只读查询，线程内同步执行，超时3s
Level 2 - mutation:     状态变更，线程隔离执行，超时30s，支持幂等重试
Level 3 - long_running: 长时计算（仿真/模型训练），Worker 进程隔离，
                        超时可配置（默认4h），支持进度轮询和取消
Level 4 - delivery:     外部投递（MES 工单/设备指令/消息推送），
                        独立 Worker，不可重试，必须单次确认
```

ToolRuntime 核心组件设计（对应 `runtimes/tools/`）：

- `executor.py`（ToolExecutor）：根据工具的 `class` 字段选择执行策略；
- `isolation.py`：管理 thread / asyncio_task / subprocess / worker_process 四种执行隔离模式；
- `retries.py`：实现指数退避（Exponential Backoff）+ 抖动（Jitter）重试策略，仅对 mutation 类工具生效；
- `cancellation.py`：基于 asyncio.CancelledError + subprocess.terminate 的分层取消机制；
- `progress.py`：通过 SSE（Server-Sent Events）向前端实时推送 long_running 工具进度。

**（2）量子专业系统适配器体系研究**

研究以下六类量子专业系统的标准化适配器：

**设计类工具适配器（integrations/qeda/）**：

Qiskit Metal 适配器——封装 `DesignPlanar` 对象的参数化操作（`add_transmon()`、`add_resonator()`、`route_cpw()`），将 Python 对象状态序列化为 JSON Artifact；KQCircuits 适配器——封装 `.gds` 文件生成流程（`kqcircuits.elements.element.Element` 参数化实例→ `gdspy.GdsLibrary` 导出→ GDS Artifact 上传至 MinIO）。

**仿真类工具适配器（integrations/simulation/）**：

HFSS 适配器——通过 PyAEDT `hfss.EigenModeSetup` API 提交本征模求解，实现求解任务的异步状态查询（`solution_type == "EigenMode"` 时采用 long_running 级执行），输出包含本征频率、Q 值矩阵的 `simulation_report` Artifact；支持 HFSS 无头（headless）模式下的后台计算。

**制造类工具适配器（integrations/mes/）**：

SECS/GEM 适配器——基于 `secs4net` 或自研 Python SECS-II 解析库，封装 S6F3（工艺程序启动）、S14F1（设备状态查询）等标准 SECS 消息；适配器对所有 S6Fx 下行消息（设备指令）强制标记为 `delivery` 级，走审批路由；ChipMES REST 适配器封装工单查询、派工和报工操作。

**测控类工具适配器（integrations/measurement/）**：

ARTIQ 适配器——通过 ARTIQ 的 `sipyco.pc_rpc.Client` 接口提交 Kasli 控制器实验（`.py` 脚本），封装频谱仪扫描（`run_spectroscopy()`）、Rabi 摆动测量（`run_rabi()`）、T1/T2 测量（`run_t1_t2()`）三类标准化接口；实验结果数据（HDF5 格式）自动解析为 `measurement_report` Artifact；Qiskit Pulse 适配器封装脉冲日历（Pulse Schedule）的构建与优化操作，支持 DRAG 参数扫描和随机基准测试（Randomized Benchmarking）结果解析。

**数据类工具适配器（integrations/warehouse/）**：

Apache Doris 适配器——封装 Text2SQL（基于量子科研数据库 Schema 的 SQL 生成）、OLAP 聚合查询和数据质量检查三类操作，所有 DDL 操作标记为 `mutation` 级；SeaTunnel REST 适配器封装 ETL 任务的提交和状态查询，支持设计数据→ Doris、MES 数据→ Doris 的标准同步任务模板。

**（3）跨系统参数语义映射研究**

研究量子芯片参数在不同工具表示之间的语义映射规则。以 transmon qubit 为例：

| 物理参数 | 设计工具表示 | 仿真工具表示 | 测控表示 |
|------|------|------|------|
| 约瑟夫森能量 $E_J$ | JJ 面积（μm²）× 临界电流密度（A/m²） | HFSS 中 lumped LC 的 L 值（nH） | Rabi 频率 $\Omega_R$（MHz） |
| 充电能量 $E_C$ | 岛区到地电容（fF） | Q3D 提取的 Maxwell 电容矩阵对角元 | 频谱 cavity pull $\chi$（MHz） |
| 跃迁频率 $f_{01}$ | $\approx \sqrt{8E_J E_C}/h - E_C/(2h)$ 解析公式 | 本征模求解第一激发态频率 | 频谱仪测量峰位 |

建立上述映射规则库（参数语义映射图谱），使 AI 在获取 HFSS 仿真结果后能够自动推断对应的 Qiskit Pulse 脉冲参数初值，减少人工换算。

#### 4. 技术路线

**图 4 多智能体路由与流水线结构图**

工具契约定义采用 JSON Schema 并纳入版本管理（契约版本与工具实现版本独立演进）；适配器均实现 `async def execute(params: dict) → ToolResult` 标准接口；长时仿真任务采用 Celery + Redis 作为任务队列（支持 Worker 水平扩展）；跨系统数据通过 MinIO 对象存储传递（工具间通过 Artifact URL 引用而非直接传递大数据量）。

---

### 研究内容四：量子科技动态演进知识图谱与检索增强生成体系

#### 1. 科学问题

量子科技知识体系的形式化面临两个核心挑战：（1）**知识图谱动态性**——量子计算是高速演进领域，每周 arXiv 新增数百篇相关论文，如何实现知识图谱的自动增量更新（Auto-incremental Knowledge Graph Update）而不引入噪声节点；（2）**量子领域 RAG 语义对齐**——量子科技文档中大量存在形如"由于 Purcell 效应导致读出腔 $\kappa$ 增大，进而削弱比特与腔的色散耦合 $\chi$"的多跳物理推理链，标准的单段落切片 + 向量检索无法捕捉这类需要跨段落推理的知识，召回质量不足。

#### 2. 研究目标

建成量子科技动态演进知识图谱（≥10万知识节点），向量检索 Top-5 准确率 ≥80%，情报更新时效达到日级；建成全生命周期数据中台，实现设计-制造-测控跨域数据贯通。

#### 3. 研究内容

**（1）量子科技知识本体建模**

建立量子计算领域本体（Quantum Computing Domain Ontology，QCDO），核心概念层次如下：

```
量子器件层（Quantum Device）
├── 超导量子比特（Transmon / Xmon / Fluxonium / SQUID）
├── 微波谐振腔（Readout Resonator / Bus Coupler）
├── 约瑟夫森结（Al/AlOx/Al JJ / SQUID / Tunable JJ）
├── 传输线（CPW / Microstrip / Airbridge）
└── 控制线路（XY line / Z line / Readout line）

物理参数层（Physical Parameter）
├── 频率（qubit freq / cavity freq / coupling freq）
├── 相干时间（T1 / T2* / T2_echo / T_phi）
├── 门保真度（single-qubit gate fidelity / two-qubit gate fidelity）
└── 非谐性（anharmonicity）/ 色散频移（dispersive shift χ）

工艺参数层（Process Parameter）
├── 薄膜沉积（Al / Nb / Ta 溅射参数：功率/时间/气压）
├── 光刻（EBL / 193nm 步进，剂量/焦距）
├── 刻蚀（ICP/RIE，功率/气体比例）
└── JJ 制备（双角度蒸镀：角度/氧化时间/氧化压强）

关系层（Relation）
├── affects（工艺参数 affects 物理参数）
├── depends_on（物理参数 depends_on 器件结构）
├── measured_by（物理参数 measured_by 测控序列）
└── improved_by（性能问题 improved_by 解决方案）
```

本体实现采用 OWL 2 DL 语言，通过 Protégé 工具建模，存储于 Neo4j 图数据库（知识图谱层）与 PostgreSQL（元数据层）双存储架构。

**（2）自动化知识抽取与图谱增量更新算法**

研究基于 LLM 的量子领域关系抽取管线（Knowledge Extraction Pipeline）：

- **文档解析**：对 arXiv PDF 采用 PyMuPDF + mathpix API 解析，保留 LaTeX 公式（不转文本），生成结构化文档 AST；
- **实体识别**：采用 NER 模型（fine-tuned SciBERT）识别量子器件名称、物理参数、数值与单位，标注准确率目标 ≥90%；
- **关系抽取**：基于量子知识本体的关系类型，设计 few-shot prompt，引导 LLM 从实验描述段落中提取三元组（head entity, relation, tail entity）；
- **知识冲突检测**：新三元组入库前，与现有图谱进行一致性检查（如新论文报告 transmon T1=500μs，与图谱中同结构器件的历史数据分布偏差超过3σ时触发人工复核标记）；
- **增量更新调度**：Heartbeat 每日02:00触发 arXiv 爬取任务，自动完成上述管线，新增实体和关系标注 `source: arxiv-YYYY-MM-DD`，支持版本回溯。

**（3）量子领域 RAG 技术研究**

针对量子科技知识的多跳推理需求，研究以下 RAG 增强技术：

**层次化索引**（Hierarchical Indexing）：建立"摘要层"（Chunk Summary，128 Token）和"详情层"（Full Chunk，512 Token）双层索引，检索时先用摘要层粗检（Top-20），再用详情层精检（Top-5）；

**知识图谱引导的检索增强**（Graph-Guided RAG）：将向量检索结果作为初始节点，通过知识图谱的 1-hop 邻域扩展，补充物理因果链（如检索到"T1 下降"节点，自动扩展到"可能原因：JJ 界面 TLS 缺陷 / 基底介质损耗 / 准粒子"节点），将图谱子图作为结构化上下文注入推理；

**假设文档嵌入**（HyDE）：对量子物理专业问题，先由 LLM 生成假设答案文档（Hypothetical Answer），再用假设文档的 Embedding 代替问题 Embedding 做检索，提升对专业长文档的召回率。

**（4）情报自动追踪与知识图谱融合**

情报追踪系统与知识图谱深度融合：arXiv 每日新论文不仅推送摘要，同时触发实体识别和关系抽取，自动更新知识图谱；已入图的实体（如"量子纠错编码"）会自动关联到最新相关论文，支持"针对某具体技术点的文献增量订阅"。情报分类体系（taxonomy）涵盖超导量子芯片设计、量子纠错、量子测控与校准、量子材料、AI+量子五大方向，支持可配置的关键词+语义双重过滤。

#### 4. 技术路线

**图 5 Hands 工具注册与外部系统映射图**

知识图谱存储：Neo4j Community 3.0+；向量索引：PGVector（pgvector 扩展，支持 IVFFLAT 和 HNSW 索引），嵌入模型采用 text-embedding-3-small（OpenAI API）或 bge-large-zh（本地 Ollama）；文档解析流程运行于独立 Worker 进程，避免干扰主推理链路；增量更新日志写入 PostgreSQL event_log 表，支持全量重建（full_rebuild）和增量更新（incremental）两种模式。

---

### 研究内容五：Heartbeat 驱动的自主科研闭环引擎与 Artifact-first 产物体系

#### 1. 科学问题

量智大脑自主科研闭环涉及两个核心工程问题：（1）**长期运行稳定性与任务状态恢复**——Heartbeat 驱动的后台任务需要在系统重启、网络中断、外部服务不可用等场景下实现状态持久化与自动恢复，单次任务失败不应导致整个调度周期丢失；（2）**科研产物（Artifact）的结构化表示**——AI 科研产出（仿真报告、情报日报、参数调优建议、工艺异常诊断）长期以非结构化文本形式存在于聊天记录中，无法有效复用、检索和版本管理，必须建立一等产物（First-Class Artifact）体系。

#### 2. 研究目标

建成可稳定运行的 Heartbeat 调度引擎，支持 ≥5 类后台任务周期化运行；建成 Artifact-first 产物体系，实现 ≥8 类 Artifact 类型的结构化存储与复用；完成 ≥3 类自主科研闭环场景的工程验证。

#### 3. 研究内容

**（1）Heartbeat 调度引擎与自主任务管理**

研究基于事件驱动的 Heartbeat 调度引擎，核心设计如下：

```python
class HeartbeatScheduler:
    """
    多层调度策略：
    - cron 表达式（如每日09:00 触发情报摘要）
    - 条件触发（如数据仓库新增数据 > 阈值时触发分析）
    - 手动触发（用户或 AI 主动调用）
    """
    tasks: Dict[str, ScheduledTask]   # 注册的定时任务
    lock_store: PostgresAdvisoryLock  # 防止分布式环境下重复触发
    fallback_policy: TaskFallback     # 失败时降级策略
```

量子科研场景的后台任务清单：`intel_digest_run`（每日情报摘要，09:00）、`knowledge_warm_run`（知识库缓存预热，每4小时）、`taxonomy_update_run`（情报分类体系更新，每12小时）、`health_check_run`（外部系统连通性巡检，每10分钟）、`yield_report_run`（制造良率周报，每周五17:00）、`calibration_reminder_run`（量子比特校准提醒，按芯片最后校准时间触发）。

研究面向量子科研调度的**自适应策略引擎**（Policy Engine）：基于历史执行记录（任务成功率、平均耗时、外部服务可用性统计），动态调整任务调度间隔和 retry 策略；当仿真服务连续3次失败时，自动降低仿真类任务调度频率并向用户发送告警。

**（2）Artifact-first 产物体系研究**

研究面向量子科研的结构化 Artifact 类型系统。所有量智大脑产出均以 Artifact 形式持久化（而非仅存于聊天记录），核心 Artifact 类型如下：

```python
class ArtifactType(Enum):
    intel_report     = "intel_report"      # 情报日报
    simulation_report= "simulation_report" # 仿真分析报告
    measurement_report="measurement_report"# 量子比特测量报告
    design_proposal  = "design_proposal"   # 芯片设计/调参建议
    pipeline_report  = "pipeline_report"   # 流水线执行报告
    db_diagnosis     = "db_diagnosis"      # 数据库诊断报告
    yield_report     = "yield_report"      # 制造良率报告
    approval_record  = "approval_record"   # 审批记录
```

每类 Artifact 定义标准化 JSON Schema，包含：`artifact_id`（UUID）、`run_id`（来源 Run）、`artifact_type`、`version`（语义版本）、`payload`（类型特定数据结构）、`checksum`（SHA256 完整性校验）、`created_at`、`tags`（可检索标签）。Artifact 内容存储于 MinIO 对象存储，元数据索引存储于 PostgreSQL，支持版本历史查询（`list_versions(artifact_id)`）和差异对比（`diff(v1, v2)`）。

**（3）快捷路径（Shortcut）注册表与高频指令优化**

研究面向量子科研高频确定性指令的快捷路径机制，将约30%以上的高频指令从通用 LLM 推理链中剥离，直接走确定性执行路径（ShortcutRegistry），响应时间从约3s 降低至 <200ms：

典型快捷路径示例：`intel_today`（发送今日情报）、`system_status`（查询 Gateway + 外部系统健康状态）、`db_status`（数据仓库连通性检查）、`latest_runs`（最近10条 Run 列表）、`calibration_status`（量子比特最近校准时间和状态）。

快捷路径识别采用意图嵌入分类（Intent Embedding Classifier），置信度阈值可配置；快捷路径注册通过 `@shortcut(trigger_patterns=["今日情报", "发日报"])` 装饰器声明。

**（4）自主科研闭环场景工程验证**

基于上述四类机制，在以下典型量子科研任务上验证"完全自主运行"的闭环能力（即无人工干预，系统自主完成全流程）：

**场景A：量子芯片 T1/T2 统计分析与工艺优化建议生成**

```
触发：Heartbeat 检测到新一批芯片测控数据入库
  → 数据分析师 Agent 执行 warehouse_query() 提取 T1/T2 数据
  → 理论物理学家 Agent 执行 theorist_noise_budget() 分析主导噪声
  → 工艺工程师 Agent 查询工艺参数历史，定位相关工序
  → 系统生成 measurement_report + design_proposal Artifact
  → 通过飞书推送给负责工程师（delivery 级，首次需确认）
```

**场景B：每日量子计算前沿情报自动摘要与推送**

```
触发：Heartbeat 09:00 触发 intel_digest_run
  → 情报员 Agent 调用 intel_search_arxiv() 获取近24h新论文
  → 依量子物理专用模型对每篇论文进行分类摘要（关键贡献/方法/数值结果）
  → 对超过关键词阈值的论文触发实体抽取并更新知识图谱
  → 生成 intel_report Artifact（含论文列表、分类树、趋势分析）
  → 通过飞书 Bot 推送至量子研发群
```

#### 4. 技术路线

**图 6 记忆—知识—情报数据通路图**

Heartbeat 调度基于 APScheduler 实现，任务状态持久化至 PostgreSQL（支持重启后自动恢复）；Artifact 存储采用 MinIO + PgMetadata 双存储；ShortcutRegistry 采用装饰器注册模式（运行时动态发现）；MCP（Model Context Protocol）运行时（`runtimes/mcp/`）为未来远程工具服务预留扩展点，支持将量子仪器控制服务以 MCP Server 形式接入，实现工具能力的远程分发与安全隔离。

---

### （二）技术路线总结

**图 7 Heartbeat + Skills + Sidecar 部署与依赖关系图**

项目五项研究内容构成"基础→调度→执行→知识→闭环"完整技术链，研制路径为"先内核、后执行、再知识、终闭环"四步走：第一步（2026 H1）完成四层架构骨架和 contracts/ 模块；第二步（2026 H2—2027 H1）完成 ModelRuntime、CoordinationEngine 和 ToolRuntime 三大执行内核；第三步（2027 H2—2028 H2）完成知识图谱、数据中台和 RAG 体系；第四步（2029—2030）完成 Heartbeat 闭环、Artifact 体系和全场景系统集成验证。

---

## 四、技术创新点与考核指标

### （一）主要技术创新点

**创新点一：面向量子工程的混合专家推理引擎与 Tool Call 协议标准**

首次提出将量子物理专用模型、代码生成模型、通用对话模型通过可微软路由（Differentiable Router）协同激活的混合专家架构，解决通用模型在量子工程专业任务上的精度不足问题。创新性地提出量子工程 Tool Call 协议扩展标准（增加 class/idempotent/approval_required/artifact_output 四个量子工程特化字段），并研究多轮工具调用链中的工具结果压缩（Tool Result Compaction）算法，解决长工具调用链中的上下文 Token 溢出问题。

**创新点二：以 Run 为一等公民的量子科研多智能体协同系统**

首次面向量子芯片研制全生命周期构建以 Run（运行实体）为核心的多智能体协同架构。提出量子科研任务分解算法：基于量子科研流程知识图谱先验约束 LLM 结构化输出，生成带依赖边的 DAG 协同计划，并研究 DAG 执行中的子任务并发控制（Concurrency Limit）、结果汇聚（Result Merging Strategy）和故障降级（Graceful Degradation）机制。提出基于能力画像（Agent Profile）的多维度智能体语义路由算法，替代现有关键词路由，路由准确率显著提升。

**创新点三：量子专业工具分级执行运行时与参数语义映射图谱**

首次系统性提出面向量子专业工具的四级执行分类（query/mutation/long_running/delivery），建立对应的隔离模式（thread/asyncio/subprocess/dedicated_worker）和可靠性策略矩阵。创新性地建立超导量子芯片参数在设计（GDS/版图参数）、仿真（电磁仿真参数）、测控（脉冲控制参数）三个表示空间之间的语义映射规则图谱，实现跨系统参数自动换算，消除研发人员手动参数转换工作。

**创新点四：量子科技知识图谱自动构建与图谱引导 RAG**

首次建立面向超导量子计算全链路的领域本体（QCDO），涵盖器件、参数、工艺、关系四个层次。提出基于量子领域 NER + LLM 关系抽取的知识图谱自动增量更新算法，并设计带一致性检验的入库策略（σ 阈值触发人工复核）。创新性地提出 Graph-Guided RAG 方法：以向量检索结果为初始节点，通过知识图谱邻域扩展补充物理因果推理链，解决量子科技文档多跳推理的召回不足问题。

**创新点五：Heartbeat 驱动的量子科研自主闭环引擎与 Artifact-first 产物体系**

首次面向量子科研场景建立 Artifact-first 产物体系：将仿真报告、情报日报、调参建议等科研产出结构化为具有版本管理、完整性校验、跨任务引用能力的一等产物（First-Class Artifact）。提出基于 APScheduler + event sourcing 的量子科研 Heartbeat 调度引擎，结合自适应策略引擎（Policy Engine），在特定量子科研任务上实现从触发到产物输出的完全无监督自主闭环。

### （二）主要考核指标

| 序号 | 指标名称 | 目标值 | 完成时间 | 考核方式 |
|------|------|------|------|------|
| 1 | 量子领域专用语料库规模 | ≥100万条（含≥10万篇全文） | 2026年底 | 数据集审查 |
| 2 | 量子物理模型基准任务准确率 | 较通用基座模型提升≥20% | 2027年中 | 标准 QuantBench 评测 |
| 3 | 多步 Tool Call 链（≥15轮）成功率 | ≥85% | 2027年底 | 压力测试 |
| 4 | 上下文压缩后关键信息保留率 | ≥95% | 2027年中 | 人工标注集评估 |
| 5 | Run 状态可追溯率 | 100% | 2027年底 | 系统功能验收 |
| 6 | 多智能体协同任务成功率 | ≥80% | 2028年中 | 标准场景测试集 |
| 7 | 语义路由准确率（较关键词路由提升） | ≥85%，提升≥15% | 2027年底 | 标准测试集 |
| 8 | 工具接入数量（分级运行时） | ≥30类 | 2028年底 | 功能清单验收 |
| 9 | 六类系统全链路连通率 | ≥95% | 2028年中 | 端到端连通测试 |
| 10 | 工具接口标准化率 | 100% | 2027年底 | 规范审查 |
| 11 | 知识图谱节点数 | ≥10万 | 2027年底 | 图谱统计 |
| 12 | RAG Top-5 检索准确率 | ≥80% | 2028年中 | 标准问答评测集 |
| 13 | 知识图谱增量更新时效 | 日级（<24h） | 2027年底 | 运行日志 |
| 14 | Artifact 类型覆盖 | ≥8类 | 2028年中 | 功能清单验收 |
| 15 | 自主闭环场景数 | ≥3类（全流程无人工干预） | 2029年底 | 场景演示验收 |
| 16 | 设计-仿真单轮迭代周期缩短率 | ≥30% | 2029年底 | 对比实测（同一团队历史基线） |
| 17 | 系统核心接口可用率 | ≥99.5%（7×24h 长跑测试） | 2029年底 | 压力测试报告 |
| 18 | 标准/规范文件数 | ≥3项（含工具契约标准、智能体接口规范） | 2030年底 | 文件评审 |
| 19 | SCI 一区发表论文数 | ≥3篇 | 2030年底 | 论文检索 |
| 20 | 发明专利申请数 | ≥20项 | 2030年底 | 专利申请记录 |

---

## 五、年度研究计划与里程碑

### 第一年度（2026年）：架构骨架与核心技术攻关启动

**主要任务（按季度）：**

Q1：完成 `contracts/`（Run、Event、Artifact、Tool、Context 数据模型）、`core/runs/`（RunCoordinator、lifecycle、persistence）设计与实现；完成量子科技本体（QCDO V0.5）建模。

Q2：完成 `runtimes/tools/`（ToolExecutor + 四级执行策略）、`runtimes/models/`（ModelRuntime 基础版）、`shortcuts/`（ShortcutRegistry + 5类快捷路径）；启动量子科学专用语料库构建（目标：≥50万条）。

Q3：完成 `core/coordination/`（CoordinationEngine 骨架：Coordinator + Planner + Delegation）；完成 Gateway V2.0 基础版（支持 Run 状态 SSE 推送）；完成 arXiv 情报追踪基础版。

Q4：完成 `core/context_assembler/`（8层上下文装配 + 预算控制）；启动量子物理专用模型预训练（CPT 阶段）；完成 ≥5 类工具标准化适配器原型。

**阶段里程碑（2026年底）：**
- V2.0 架构骨架运行，四层架构可端到端通信
- 完成 ≥5 类快捷路径、≥3 类智能体协同原型
- 语料库 V0.5 完成

---

### 第二年度（2027年）：核心技术突破与 V1.0 系统研制

**主要任务：**

Q1-Q2：完成量子物理专用模型 SFT + RLHF 训练；完成混合专家路由软路由机制；完成 Tool Call 协议标准 V1.0；完成 ContextAssembler 工具结果压缩算法。

Q3-Q4：完成多智能体 DAG 协同计划生成算法；完成量子科技知识图谱 V1.0（≥10万节点）；完成 ≥30 类工具标准化适配器；完成 Artifact-first 产物体系 V1.0（≥8类 Artifact）。

**阶段里程碑（2027年底，第一阶段验收）：**
- 量智大脑 V1.0 系统通过功能验收
- 量子物理专用模型基准准确率达标（较通用模型提升≥20%）
- 知识图谱 V1.0 完成，RAG 评测达标
- 完成 ≥3 个典型端到端场景演示
- 考核指标 1-10 验收达标

---

### 第三年度（2028年）：系统集成与深度示范

**主要任务：**
- 完成 V2.0 系统升级（混合专家路由完整版、企业级权限与多项目隔离）；
- 完成设计-仿真-测控全链路场景集成验证；
- 完成数据中台（Apache Doris + SeaTunnel）完整对接；
- 完成 MCPRuntime 预留框架；
- 申请发明专利 ≥5 项，起草标准规范 V0.5。

**阶段里程碑（2028年底）：**
- AI 赋能覆盖关键研发环节 ≥30%
- 全链路连通率达标（≥95%）
- 多智能体协同任务成功率达标（≥80%）

---

### 第四年度（2029年）：示范应用完成与成果固化

**主要任务：**
- AI 赋能覆盖关键研发环节 ≥50%；
- 完成 ≥3 类自主闭环场景工程验证；
- 完成设计-仿真迭代周期缩短率 ≥30% 的对比实测；
- 完成标准规范 ≥3 项正式发布；
- 申请发明专利累计 ≥15 项，发表论文 ≥5 篇。

**阶段里程碑（2029年底，第二阶段验收）：**
- 示范应用通过验收
- 考核指标 11-17 验收达标

---

### 第五年度（2030年）：全面完善与成果推广

**主要任务：**
- 完成全部考核指标验证与系统全面优化；
- 发布可复制推广方案包；
- 完成发明专利 ≥20 项申请；
- 发表 SCI 一区论文 ≥3 篇；
- 举办技术开放日与标准推广研讨会。

**最终验收里程碑（2030年底）：**
- 全部20项考核指标通过验收
- 完整交付物清单提交

---

## 六、项目基础与研究条件

### （一）前期研究基础

项目组在 QuantaMind V1.x 原型系统基础上，已完成以下关键验证工作，形成本项目的直接研究基础：

**1. 四层架构可行性验证**：当前 V1.x 已实现 FastAPI Gateway + Brain（Ollama 本地 LLM）+ Orchestrator（关键词路由多智能体）+ Hands（工具执行）+ Memory（Markdown 项目记忆）+ Heartbeat（APScheduler 定时任务）六模块原型，端到端可运行，架构分层思路已验证。

**2. 工具适配器原型验证**：已完成以下适配器的原型对接验证：Qiskit Metal 版图参数化操作（`hands_qiskit_metal.py`）、KQCircuits GDS 生成（`hands_kqcircuits.py`）、ARTIQ 实时测控（`hands_artiq.py`）、Qiskit Pulse 脉冲校准（`hands_qiskit_pulse.py`）、Apache Doris 数据查询（`hands_doris.py`）、ChipMES REST 接口（`hands_chipmes.py`）、arXiv 情报追踪（`arxiv_intel.py`，3309行）等，证明各类工具适配器的技术路径可行。

**3. 知识与情报能力验证**：已实现 PGVector 向量检索（`ai_pgvector` 数据库配置）、arXiv 论文定向追踪与飞书推送（支持量子芯片设计、量子误差纠正等方向分类）、项目记忆系统（Markdown 存储 + 摘要写入机制）的原型验证，知识检索技术路径已通。

**4. 已识别的工程瓶颈（本项目重点攻关方向）**：基于 V1.x 原型的工程实践，明确识别了以下待解决的技术瓶颈：（a）无统一 Run 模型，长任务状态散落于 `chat_jobs / pipelines / tasks` 多个结构，重启后状态丢失；（b）多智能体协同停留在"多角色单入口"，CoordinationEngine 尚未实现；（c）工具执行缺少分级 Runtime，同步长任务（如 HFSS 仿真）阻塞主对话线程；（d）ContextAssembler 未实现，上下文以全量消息列表注入，存在大量无效 Token；（e）Artifact 尚未作为一等产物管理，科研产出仅存于对话流水线字典，不可复用。上述瓶颈已在 QuantaMind 2.0 设计方案（`docs/QuantaMind_2.0_目录与模块设计稿.md`）中有明确架构解决方案，本项目以此为基础进行系统性工程化实现。

### （二）现有研究条件

具备 GPU 算力（可支撑70B 级模型微调）、PostgreSQL + pgvector 数据库基础设施、MinIO 对象存储、Grafana 监控看板等基础设施；具备与主要量子专业工具（Qiskit Metal、ARTIQ、ChipMES）的技术对接经验；具备量子计算、AI 工程、工业软件交叉背景的核心团队。

---

## 七、研究队伍与分工

### （一）核心团队

| 姓名 | 职称 | 研究方向 | 承担内容 |
|------|------|------|------|
| （填写） | 研究员 | AI+量子融合系统 | 总负责，四层架构总体设计 |
| （填写） | 副研究员 | 大模型推理工程 | 研究内容一（混合专家推理引擎） |
| （填写） | 副研究员 | 多智能体系统 | 研究内容二（多智能体协同） |
| （填写） | 副研究员 | 量子工业软件 | 研究内容三（工具运行时与适配器） |
| （填写） | 副研究员 | 知识图谱/NLP | 研究内容四（知识图谱与 RAG） |
| （填写） | 助研 | 系统工程 | 研究内容五（自主闭环与 Artifact） |
| （填写） | 博士生 | 量子物理 | 研究内容一（专用模型评测与语料建设） |
| （填写） | 博士生 | 量子测控 | 研究内容三（测控适配器） |
| （填写） | 硕士生×3 | AI工程 | 各研究内容工程实现支撑 |

---

## 八、经费预算概算

| 预算科目 | 预算金额（万元） | 说明 |
|------|------|------|
| 设备费 | （填写） | GPU 服务器（大模型训练推理）、存储设备 |
| 材料费 | （填写） | 云 API 调用费、数据采集费用、软件许可 |
| 测试化验加工费 | （填写） | 第三方系统测试、模型评测 |
| 燃料动力费 | （填写） | GPU 集群运行能耗 |
| 差旅费 | （填写） | 学术交流、工具对接现场调研 |
| 会议费 | （填写） | 项目年会、标准研讨会 |
| 国际合作与交流费 | （填写） | 国际量子计算会议、合作访问 |
| 劳务费 | （填写） | 研究生及合同制研究人员劳务 |
| 专家咨询费 | （填写） | 量子物理与工业软件领域专家咨询 |
| 其他直接费用 | （填写） | 知识产权费、出版费 |
| 间接费用 | （填写） | 按政策规定比例 |
| **合计** | **（填写）** | |

---

## 九、预期成果及应用前景

### （一）核心技术成果

1. **软件系统**：量子科技自主科研人工智能中台系统（量智大脑）V2.0 完整源代码与部署包，含四层架构完整实现（`quantamind_v2/` 模块体系）；量子科学混合专家推理模型；量子科技知识图谱数据集（≥10万节点）。

2. **标准规范**（≥3项）：量子工程 Tool Call 协议扩展规范 V1.0；量子科研多智能体 Run 模型与接口规范 V1.0；量子科技 AI 工具契约标准 V1.0。

3. **学术成果**：SCI 一区论文 ≥3 篇（目标发表于 Nature Machine Intelligence、IEEE Transactions on Quantum Engineering、npj Quantum Information 等期刊）；发明专利 ≥20 项；软件著作权 ≥10 项。

4. **基础设施**：量子科技专用领域语料库（≥100万条）；量子科技基准评测集（QuantBench，≥3000题）；量子科研 Artifact 资产库（≥20个技能包，≥100份样例 Artifact）。

### （二）应用前景

1. **直接应用**：在量子芯片研制团队内部完成工程部署，预期实现单轮设计-仿真迭代周期缩短≥30%，情报检索效率提升5倍以上，自主化任务处理占比达到研发日常工作量的20%以上。

2. **推广价值**：量智大脑作为量子科技 AI 中台基础设施，具备向其他量子计算机构复制推广的能力；其中工具契约标准、Run 模型规范可作为量子软件行业标准，推动量子计算软件生态协同发展。

3. **长期影响**：本项目建立的"LLM + 领域专用模型 + 工具编排 + 知识图谱 + 自主闭环"技术框架，具有超越量子计算领域的普适性，可为核聚变、高能物理、材料科学等其他科学计算领域的 AI 中台建设提供方法论参考。

---

**申报单位（盖章）：**

**项目负责人（签名）：**

**填报日期：** 2026年4月
