"""
生成量智大脑申报文档的 7 张示意图（matplotlib，支持中文）
输出到 docs/_generated_figures/figure_N.png
"""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ── 字体配置 ──────────────────────────────────────────────
plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "_generated_figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 颜色方案 ──────────────────────────────────────────────
C = {
    "blue_dark":  "#1A3A5C",
    "blue_mid":   "#2A6DB5",
    "blue_light": "#5B9BD5",
    "blue_pale":  "#D6E4F5",
    "teal":       "#1E7C7C",
    "teal_pale":  "#D4EEEE",
    "green":      "#2E7D32",
    "green_pale": "#D7F0D9",
    "orange":     "#E65100",
    "orange_pale":"#FDE5D0",
    "purple":     "#5E35B1",
    "purple_pale":"#EDE7F6",
    "grey_dark":  "#455A64",
    "grey_light": "#ECEFF1",
    "gold":       "#F57F17",
    "gold_pale":  "#FFF9C4",
    "white":      "#FFFFFF",
    "arrow":      "#37474F",
}

FIG_W, FIG_H = 16, 9  # inches, 16:9


def save(fig: plt.Figure, name: str) -> None:
    path = OUT_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved → {path.name}")


def box(ax, x, y, w, h, text, fc=C["blue_pale"], ec=C["blue_mid"],
        fontsize=11, bold=False, radius=0.015, text_color="#1F1F1F"):
    rect = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.005,rounding_size={radius}",
                          linewidth=1.8, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(rect)
    weight = "bold" if bold else "normal"
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, color=text_color, zorder=4,
            wrap=True, multialignment="center")


def arrow(ax, x0, y0, x1, y1, color=C["arrow"], lw=1.8, style="->"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle="arc3,rad=0.0"), zorder=5)


def title_label(ax, text, fontsize=13):
    ax.text(0.5, 0.97, text, ha="center", va="top", transform=ax.transAxes,
            fontsize=fontsize, fontweight="bold", color=C["blue_dark"],
            bbox=dict(boxstyle="round,pad=0.3", fc=C["blue_pale"], ec=C["blue_mid"], lw=1.5))


def layer_bg(ax, y, h, fc, label, lw=0.8):
    rect = FancyBboxPatch((0.01, y), 0.98, h,
                          boxstyle="round,pad=0.005,rounding_size=0.01",
                          linewidth=lw, edgecolor=C["grey_dark"], facecolor=fc,
                          alpha=0.35, zorder=1)
    ax.add_patch(rect)
    ax.text(0.015, y + h / 2, label, ha="left", va="center",
            fontsize=9, color=C["grey_dark"], fontstyle="italic", zorder=2)


# ══════════════════════════════════════════════════════════════════
# 图 1：量智大脑平台技术体系架构图
# ══════════════════════════════════════════════════════════════════
def fig1():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    title_label(ax, "图 1  量智大脑（QuantaMind）平台技术体系架构图")

    # layer backgrounds
    layers = [
        (0.74, 0.17, C["blue_pale"],   "① 入口层"),
        (0.55, 0.17, C["teal_pale"],   "② 中枢层"),
        (0.34, 0.19, C["green_pale"],  "③ 工具·数据层"),
        (0.14, 0.18, C["gold_pale"],   "④ 自主演进层"),
        (0.03, 0.09, C["purple_pale"], "⑤ 外部系统"),
    ]
    for y, h, fc, lbl in layers:
        layer_bg(ax, y, h, fc, lbl)

    # 入口层
    for i, (lbl, x) in enumerate([
        ("桌面客户端\n（主力形态）", 0.05),
        ("Web 客户端\n（看板·审批）", 0.26),
        ("CLI 客户端\n（脚本·自动化）", 0.47),
        ("嵌入式面板\n（Q-EDA 内嵌）", 0.68),
    ]):
        box(ax, x, 0.77, 0.18, 0.11, lbl, fc=C["blue_pale"], ec=C["blue_mid"], fontsize=10)

    # 中枢层
    for lbl, x, fc, ec in [
        ("Gateway\n统一入口·会话管理", 0.05, C["teal_pale"],   C["teal"]),
        ("Brain\n混合专家推理引擎",     0.27, C["teal_pale"],   C["teal"]),
        ("Orchestrator\n智能体路由·编排", 0.49, C["teal_pale"], C["teal"]),
        ("Agent Matrix\n多角色智能体矩阵", 0.71, C["teal_pale"], C["teal"]),
    ]:
        box(ax, x, 0.58, 0.20, 0.12, lbl, fc=fc, ec=ec, fontsize=10)

    # 工具·数据层
    for lbl, x, fc, ec in [
        ("Hands\n工具编排总线",         0.05, C["green_pale"], C["green"]),
        ("Memory\n项目记忆",             0.25, C["green_pale"], C["green"]),
        ("Knowledge\n知识图谱·向量检索", 0.44, C["green_pale"], C["green"]),
        ("Data Connectors\n数据·存储接入", 0.63, C["green_pale"], C["green"]),
        ("Sidecar API\n领域服务",        0.82, C["green_pale"], C["green"]),
    ]:
        box(ax, x, 0.37, 0.17, 0.12, lbl, fc=fc, ec=ec, fontsize=9.5)

    # 自主演进层
    for lbl, x, fc, ec in [
        ("Heartbeat\n后台自主任务",     0.05, C["gold_pale"], C["gold"]),
        ("Skills Market\n能力包·技能市场", 0.29, C["gold_pale"], C["gold"]),
        ("Policy Engine\n策略·反馈优化", 0.53, C["gold_pale"], C["gold"]),
        ("Model Tuning\n模型持续演进",   0.77, C["gold_pale"], C["gold"]),
    ]:
        box(ax, x, 0.17, 0.20, 0.11, lbl, fc=fc, ec=ec, fontsize=9.5)

    # 外部系统
    extlist = ["Q-EDA / 版图设计", "仿真（HFSS·Q3D）", "MES / SECS·GEM",
               "测控（ARTIQ·QCoDeS）", "数据仓库（Doris）", "对象存储（MinIO）", "飞书·企微"]
    total = len(extlist)
    span = 0.96 / total
    for i, lbl in enumerate(extlist):
        box(ax, 0.02 + i * span, 0.04, span - 0.008, 0.07,
            lbl, fc=C["purple_pale"], ec=C["purple"], fontsize=8.5)

    # 竖向箭头连通各层
    for xc in [0.14, 0.36, 0.58, 0.80]:
        arrow(ax, xc, 0.88, xc, 0.71)
        arrow(ax, xc, 0.70, xc, 0.58)
        arrow(ax, xc, 0.56, xc, 0.50)
        arrow(ax, xc, 0.36, xc, 0.29)
    for xc in [0.14, 0.36, 0.58, 0.80]:
        arrow(ax, xc, 0.17, xc, 0.12)

    fig.tight_layout()
    save(fig, "figure_1.png")


# ══════════════════════════════════════════════════════════════════
# 图 2：Gateway 与客户端接入架构图
# ══════════════════════════════════════════════════════════════════
def fig2():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    title_label(ax, "图 2  Gateway 与客户端统一接入架构图")

    # 客户端
    clients = [("桌面客户端", 0.78), ("Web 客户端", 0.60), ("CLI 客户端", 0.42), ("嵌入式面板", 0.24)]
    for lbl, y in clients:
        box(ax, 0.04, y - 0.06, 0.20, 0.11, lbl, fc=C["blue_pale"], ec=C["blue_mid"], fontsize=11)
        arrow(ax, 0.24, y - 0.005, 0.39, y - 0.005)

    # 协议标注
    ax.text(0.305, 0.70, "REST / WebSocket", ha="center", va="center",
            fontsize=9, color=C["grey_dark"], fontstyle="italic")

    # Gateway 中间件
    box(ax, 0.39, 0.25, 0.22, 0.55, "Gateway\n\n· 会话管理\n· 认证·权限\n· 流式通道\n· 健康检查\n· 审计留痕",
        fc=C["teal_pale"], ec=C["teal"], fontsize=10, bold=True)

    # 下游模块
    downstream = [
        ("Orchestrator\n编排中枢",     0.72, 0.72, C["green_pale"], C["green"]),
        ("Memory\n项目记忆",            0.72, 0.52, C["green_pale"], C["green"]),
        ("Sidecar API\n领域服务",       0.72, 0.32, C["green_pale"], C["green"]),
        ("系统管理\n心跳·配置·日志",   0.72, 0.12, C["gold_pale"],  C["gold"]),
    ]
    for lbl, x, y, fc, ec in downstream:
        box(ax, x, y, 0.24, 0.13, lbl, fc=fc, ec=ec, fontsize=10)
        arrow(ax, 0.61, y + 0.065, x, y + 0.065)

    ax.text(0.50, 0.04, "← 内网 / 专网部署，不依赖公网 →",
            ha="center", va="center", fontsize=9.5, color=C["blue_dark"],
            style="italic",
            bbox=dict(boxstyle="round", fc=C["blue_pale"], ec=C["blue_mid"], lw=1.2))

    fig.tight_layout()
    save(fig, "figure_2.png")


# ══════════════════════════════════════════════════════════════════
# 图 3：Brain 与工具调用循环示意图
# ══════════════════════════════════════════════════════════════════
def fig3():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    title_label(ax, "图 3  Brain 混合专家推理引擎与工具调用循环示意图")

    # 左侧输入
    box(ax, 0.03, 0.60, 0.18, 0.14, "System Prompt\n· Agent 专精描述\n· 项目记忆摘要",
        fc=C["blue_pale"], ec=C["blue_mid"], fontsize=9.5)
    box(ax, 0.03, 0.40, 0.18, 0.14, "Tool Definitions\n· 工具名称\n· 参数 Schema",
        fc=C["blue_pale"], ec=C["blue_mid"], fontsize=9.5)
    box(ax, 0.03, 0.20, 0.18, 0.14, "对话历史\n· 用户消息\n· 工具结果回注",
        fc=C["blue_pale"], ec=C["blue_mid"], fontsize=9.5)

    # Brain 核心（混合专家）
    box(ax, 0.27, 0.30, 0.26, 0.42,
        "Brain\n混合专家推理引擎\n\n通用 LLM\n量子物理模型\n代码生成模型\n专家规则",
        fc=C["teal_pale"], ec=C["teal"], fontsize=10.5, bold=True)

    # 输出
    box(ax, 0.62, 0.68, 0.22, 0.12, "文本回复\n（流式输出）",
        fc=C["green_pale"], ec=C["green"], fontsize=10)
    box(ax, 0.62, 0.52, 0.22, 0.12, "Tool Call\n（结构化调用指令）",
        fc=C["gold_pale"], ec=C["gold"], fontsize=10)

    # Hands
    box(ax, 0.62, 0.30, 0.22, 0.16, "Hands\n工具编排执行层\n（异步·可追溯）",
        fc=C["orange_pale"], ec=C["orange"], fontsize=10)
    box(ax, 0.62, 0.10, 0.22, 0.14, "外部系统\n设计·仿真·MES·测控·数据",
        fc=C["purple_pale"], ec=C["purple"], fontsize=9.5)

    # 箭头
    for y in [0.67, 0.47, 0.27]:
        arrow(ax, 0.21, y, 0.27, y)
    arrow(ax, 0.53, 0.74, 0.62, 0.74)
    arrow(ax, 0.53, 0.58, 0.62, 0.58)
    arrow(ax, 0.53, 0.45, 0.62, 0.38)
    arrow(ax, 0.62, 0.36, 0.53, 0.36)   # 工具结果回注
    arrow(ax, 0.62, 0.30, 0.62, 0.24)
    arrow(ax, 0.73, 0.10, 0.53, 0.30)

    # 循环标注
    ax.annotate("结果回注", xy=(0.53, 0.36), xytext=(0.56, 0.28),
                ha="center", fontsize=8.5, color=C["orange"],
                arrowprops=dict(arrowstyle="-", color=C["orange"], lw=1))

    ax.text(0.85, 0.52, "MAX_TOOL_ROUNDS = 20\n（防止死循环）",
            ha="center", va="center", fontsize=9, color=C["grey_dark"],
            bbox=dict(boxstyle="round", fc=C["grey_light"], ec=C["grey_dark"], lw=1))

    fig.tight_layout()
    save(fig, "figure_3.png")


# ══════════════════════════════════════════════════════════════════
# 图 4：多智能体路由与流水线结构图
# ══════════════════════════════════════════════════════════════════
def fig4():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    title_label(ax, "图 4  多智能体路由与对话流水线结构图")

    # 用户请求
    box(ax, 0.02, 0.42, 0.13, 0.16, "用户请求\n自然语言",
        fc=C["blue_pale"], ec=C["blue_mid"], fontsize=11, bold=True)
    arrow(ax, 0.15, 0.50, 0.22, 0.50)

    # 路由器
    box(ax, 0.22, 0.38, 0.14, 0.24, "意图路由\n_route()\n关键词 +\n上下文",
        fc=C["teal_pale"], ec=C["teal"], fontsize=10, bold=True)

    # Agents
    agents = [
        ("AI 芯片设计师",    0.48, 0.84),
        ("AI 理论物理学家",  0.48, 0.72),
        ("AI 仿真工程师",    0.48, 0.60),
        ("AI 工艺工程师",    0.48, 0.48),
        ("AI 测控科学家",    0.48, 0.36),
        ("AI 数据分析师",    0.48, 0.24),
        ("AI 情报·知识",    0.48, 0.12),
    ]
    for lbl, x, y in agents:
        box(ax, x, y - 0.04, 0.20, 0.09, lbl,
            fc=C["green_pale"], ec=C["green"], fontsize=9.5)
        arrow(ax, 0.36, 0.50, x, y + 0.005, color=C["teal"])

    # Hands / Tools
    box(ax, 0.74, 0.33, 0.22, 0.34, "Hands\n工具总线\n\nmetal_* kqc_*\nsim_* mes_*\nartiq_* doris_*\nintel_* ...",
        fc=C["gold_pale"], ec=C["gold"], fontsize=9.5)
    for lbl, x, y in agents:
        arrow(ax, x + 0.20, y + 0.005, 0.74, 0.50, color=C["green"])

    # Pipeline 记录
    box(ax, 0.02, 0.10, 0.18, 0.22,
        "流水线记录\nPipeline ID\n步骤·参数\n结果摘要\n可审计",
        fc=C["purple_pale"], ec=C["purple"], fontsize=9.5)
    ax.annotate("", xy=(0.10, 0.32), xytext=(0.10, 0.50),
                arrowprops=dict(arrowstyle="<->", color=C["purple"], lw=1.5))

    fig.tight_layout()
    save(fig, "figure_4.png")


# ══════════════════════════════════════════════════════════════════
# 图 5：Hands 工具注册与外部系统映射图
# ══════════════════════════════════════════════════════════════════
def fig5():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    title_label(ax, "图 5  Hands 工具编排总线与外部系统映射图")

    # 注册表
    box(ax, 0.03, 0.30, 0.20, 0.40,
        "Tool Registry\n工具注册表\n\n统一注册\n描述·Schema\n权限前缀\n异步执行\n结果标准化",
        fc=C["teal_pale"], ec=C["teal"], fontsize=10, bold=True)

    # 适配器层 + 外部系统
    groups = [
        ("设计适配器\nmetal_* kqc_* qeda_*",  "Q-EDA / Qiskit Metal / KQCircuits",  0.72, C["blue_pale"], C["blue_mid"]),
        ("仿真适配器\nsim_* metal_analyze_*",  "HFSS / Q3D / 仿真引擎",              0.60, C["green_pale"], C["green"]),
        ("制造适配器\nmes_* secs_* chipmes_*", "ChipMES / OpenMES / SECS·GEM",       0.48, C["orange_pale"], C["orange"]),
        ("测控适配器\nartiq_* pulse_* mitiq_*","ARTIQ / Qiskit Pulse / Mitiq",        0.36, C["purple_pale"], C["purple"]),
        ("数据适配器\nwarehouse_* doris_* ...", "Doris / SeaTunnel / QData / MinIO",  0.24, C["gold_pale"], C["gold"]),
        ("情报·知识\nintel_* knowledge_*",     "arXiv / 飞书 / PGVector",            0.12, C["teal_pale"], C["teal"]),
    ]
    for adapt_lbl, ext_lbl, y, fc, ec in groups:
        box(ax, 0.30, y, 0.20, 0.09, adapt_lbl, fc=fc, ec=ec, fontsize=9.5)
        box(ax, 0.65, y, 0.30, 0.09, ext_lbl,   fc=fc, ec=ec, fontsize=9.5)
        arrow(ax, 0.23, 0.50, 0.30, y + 0.045, color=C["teal"])
        arrow(ax, 0.50, y + 0.045, 0.65, y + 0.045)

    # 可扩展提示
    ax.text(0.50, 0.04, "可扩展：新增工具 = 注册描述 + 实现函数，无需修改编排内核",
            ha="center", va="center", fontsize=9.5, color=C["blue_dark"],
            bbox=dict(boxstyle="round", fc=C["blue_pale"], ec=C["blue_mid"], lw=1.2))

    fig.tight_layout()
    save(fig, "figure_5.png")


# ══════════════════════════════════════════════════════════════════
# 图 6：记忆—知识—情报数据通路图
# ══════════════════════════════════════════════════════════════════
def fig6():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    title_label(ax, "图 6  记忆—知识—情报数据通路图")

    # 数据来源
    sources = [
        ("对话与项目交互",  0.05, 0.74),
        ("设计·仿真数据",  0.05, 0.56),
        ("制造·测控数据",  0.05, 0.38),
        ("arXiv 等外部情报", 0.05, 0.20),
    ]
    for lbl, x, y in sources:
        box(ax, x, y, 0.18, 0.10, lbl, fc=C["blue_pale"], ec=C["blue_mid"], fontsize=9.5)

    # 治理层
    govs = [
        ("Memory\n项目记忆层",    0.32, 0.74, C["teal_pale"],  C["teal"]),
        ("数据中台\n归集·治理层",  0.32, 0.56, C["teal_pale"],  C["teal"]),
        ("Knowledge\n知识图谱层",  0.32, 0.38, C["green_pale"], C["green"]),
        ("情报处理层\n摘要·分类",  0.32, 0.20, C["gold_pale"],  C["gold"]),
    ]
    for lbl, x, y, fc, ec in govs:
        box(ax, x, y, 0.18, 0.10, lbl, fc=fc, ec=ec, fontsize=9.5)

    # 连接数据源 → 治理层
    for (_, sx, sy), (_, gx, gy, _, _) in zip(sources, govs):
        arrow(ax, sx + 0.18, sy + 0.05, gx, gy + 0.05)

    # 应用层
    apps = [
        ("向量检索\n（RAG）",           0.62, 0.74, C["purple_pale"], C["purple"]),
        ("实验推荐\n决策建议",           0.62, 0.60, C["purple_pale"], C["purple"]),
        ("动态知识图谱\n可视化",         0.62, 0.46, C["purple_pale"], C["purple"]),
        ("情报日报\n飞书·企微推送",      0.62, 0.32, C["purple_pale"], C["purple"]),
        ("模型微调\n知识持续更新",        0.62, 0.18, C["purple_pale"], C["purple"]),
    ]
    for lbl, x, y, fc, ec in apps:
        box(ax, x, y, 0.20, 0.10, lbl, fc=fc, ec=ec, fontsize=9.5)

    # 治理层 → 应用层
    arrow(ax, 0.50, 0.79, 0.62, 0.79)
    arrow(ax, 0.50, 0.61, 0.62, 0.65)
    arrow(ax, 0.50, 0.43, 0.62, 0.51)
    arrow(ax, 0.50, 0.25, 0.62, 0.37)
    arrow(ax, 0.50, 0.25, 0.62, 0.23)

    # 反馈箭头（决策 → 数据源）
    ax.annotate("", xy=(0.14, 0.38), xytext=(0.62, 0.65),
                arrowprops=dict(arrowstyle="-|>", color=C["orange"], lw=1.5,
                                connectionstyle="arc3,rad=-0.35"))
    ax.text(0.36, 0.13, "决策结果反哺数据中台，形成数据→AI→洞察→决策→新数据闭环",
            ha="center", va="center", fontsize=9, color=C["orange"],
            bbox=dict(boxstyle="round", fc=C["orange_pale"], ec=C["orange"], lw=1.2))

    fig.tight_layout()
    save(fig, "figure_6.png")


# ══════════════════════════════════════════════════════════════════
# 图 7：Heartbeat + Skills + Sidecar 部署与依赖关系图
# ══════════════════════════════════════════════════════════════════
def fig7():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    title_label(ax, "图 7  Heartbeat + Skills + Sidecar 部署与依赖关系图")

    # 核心 Gateway
    box(ax, 0.38, 0.42, 0.24, 0.16, "Gateway\n统一入口·主进程",
        fc=C["teal_pale"], ec=C["teal"], fontsize=12, bold=True)

    # Heartbeat
    box(ax, 0.05, 0.68, 0.24, 0.20,
        "Heartbeat\n后台自主心跳\n\n· 定时情报摘要\n· 健康巡检\n· 自动报告生成\n· 策略触发",
        fc=C["gold_pale"], ec=C["gold"], fontsize=9.5)
    arrow(ax, 0.29, 0.78, 0.38, 0.54)

    # Skills
    box(ax, 0.05, 0.38, 0.24, 0.22,
        "Skills Market\n能力包·技能市场\n\n· YAML 规则包\n· Markdown 知识包\n· 领域流程包\n· 热加载支持",
        fc=C["green_pale"], ec=C["green"], fontsize=9.5)
    arrow(ax, 0.29, 0.49, 0.38, 0.49)

    # Policy Engine
    box(ax, 0.05, 0.10, 0.24, 0.20,
        "Policy Engine\n策略·反馈优化\n\n· 任务优先级\n· 自适应阈值\n· 学习与更新",
        fc=C["purple_pale"], ec=C["purple"], fontsize=9.5)
    arrow(ax, 0.29, 0.20, 0.38, 0.45)

    # Sidecar API
    box(ax, 0.72, 0.68, 0.24, 0.20,
        "Sidecar API\n设计·仿真领域服务\n\n· 独立部署\n· 独立扩容\n· 标准 REST 接口",
        fc=C["blue_pale"], ec=C["blue_mid"], fontsize=9.5)
    arrow(ax, 0.62, 0.54, 0.72, 0.78)

    # 外部平台
    box(ax, 0.72, 0.38, 0.24, 0.22,
        "外部平台集成\n\n· Q-EDA 平台\n· 制造平台\n· 云服务平台\n· 其他中心平台",
        fc=C["orange_pale"], ec=C["orange"], fontsize=9.5)
    arrow(ax, 0.62, 0.49, 0.72, 0.49)

    # 远程监控
    box(ax, 0.72, 0.10, 0.24, 0.20,
        "监控·运维\n\n· Grafana 看板\n· 健康检查 API\n· 日志·链路追踪",
        fc=C["gold_pale"], ec=C["gold"], fontsize=9.5)
    arrow(ax, 0.62, 0.45, 0.72, 0.20)

    # 说明
    ax.text(0.50, 0.04,
            "部署模式：Gateway 主进程 + Sidecar 微服务，Heartbeat / Skills / PolicyEngine 作为独立线程挂载，支持按需扩缩容",
            ha="center", va="center", fontsize=9, color=C["blue_dark"],
            bbox=dict(boxstyle="round", fc=C["blue_pale"], ec=C["blue_mid"], lw=1.2))

    fig.tight_layout()
    save(fig, "figure_7.png")


if __name__ == "__main__":
    print("正在生成 7 张示意图...")
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6(); fig7()
    print("全部完成，图片保存于:", OUT_DIR)
