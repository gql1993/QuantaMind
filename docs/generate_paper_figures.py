"""
生成论文所需的 7 张图，保存为 PNG
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT = r"E:\work\QuantaMind\docs\paper_figures"
os.makedirs(OUT, exist_ok=True)

with open(r"E:\work\QuantaMind\docs\paper_experiment_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

plt.rcParams.update({"font.size": 9, "figure.dpi": 200, "savefig.bbox": "tight"})

# ── Fig 1: System Architecture ──
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.axis("off")
layers = [
    (0.5, 6.2, 9, 0.6, "#E3F2FD", "L0: User Layer (Desktop / Web / CLI Client)"),
    (0.5, 5.3, 9, 0.6, "#BBDEFB", "L1: Gateway (Session / Auth / Protocol / Streaming)"),
    (0.5, 4.4, 9, 0.6, "#90CAF9", "L2: Brain (MoE Router / Multi-Model Inference / Function Calling)"),
    (0.5, 3.5, 9, 0.6, "#64B5F6", "L3: 12 AI Scientist Agents"),
    (0.5, 2.6, 9, 0.6, "#42A5F5", "L4: Hands (120+ Tools) + Memory (RAG / Knowledge Graph)"),
    (0.5, 1.5, 9, 0.8, "#1E88E5", "L5: Q-EDA | Ansys HFSS/Q3D | CHIPMES | ARTIQ | Doris | Grafana"),
]
for x, y, w, h, color, label in layers:
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", facecolor=color, edgecolor="#333", linewidth=0.8))
    ax.text(x + w/2, y + h/2, label, ha="center", va="center", fontsize=8, fontweight="bold")
for i in range(5):
    ax.annotate("", xy=(5, layers[i+1][1]+layers[i+1][3]), xytext=(5, layers[i][1]),
                arrowprops=dict(arrowstyle="->", color="#555", lw=1))
sides = [
    (0.1, 1.0, "Heartbeat\n(L0-L3)", "#FFF9C4"),
    (9.6, 1.0, "Skills\nMarket", "#C8E6C9"),
]
for x, y, label, color in sides:
    ax.add_patch(mpatches.FancyBboxPatch((x-0.3, y), 1.2, 5.5, boxstyle="round,pad=0.05", facecolor=color, edgecolor="#333", linewidth=0.6, alpha=0.5))
    ax.text(x+0.3, y+2.7, label, ha="center", va="center", fontsize=7, rotation=90)
ax.set_title("Fig. 1: QuantaMind System Architecture", fontsize=10, fontweight="bold")
fig.savefig(os.path.join(OUT, "fig1_architecture.png"))
plt.close()

# ── Fig 2: Agent Workflow ──
fig, ax = plt.subplots(figsize=(7, 2.5))
ax.set_xlim(0, 13); ax.set_ylim(0, 2.5); ax.axis("off")
agents = [
    ("Orch.", "#E0E0E0"), ("Theory", "#FFCDD2"), ("Design", "#C8E6C9"),
    ("Simul.", "#BBDEFB"), ("Material", "#FFF9C4"), ("Process", "#FFE0B2"),
    ("DevOps", "#D1C4E9"), ("Measure", "#B2DFDB"), ("Algo.", "#F0F4C3"),
    ("Data", "#CFD8DC"), ("Knowledge", "#FFECB3"), ("PM", "#F5F5F5"),
]
for i, (name, color) in enumerate(agents):
    x = 0.3 + i * 1.05
    ax.add_patch(mpatches.FancyBboxPatch((x, 0.7), 0.9, 1.0, boxstyle="round,pad=0.05", facecolor=color, edgecolor="#333", lw=0.7))
    ax.text(x+0.45, 1.2, name, ha="center", va="center", fontsize=6.5, fontweight="bold")
    ax.text(x+0.45, 0.9, f"#{i+1}", ha="center", va="center", fontsize=6, color="#666")
    if i < 11:
        ax.annotate("", xy=(x+1.0, 1.2), xytext=(x+0.95, 1.2), arrowprops=dict(arrowstyle="->", color="#888", lw=0.8))
ax.set_title("Fig. 2: Twelve AI Scientist Agents (Research Workflow Order)", fontsize=9, fontweight="bold")
fig.savefig(os.path.join(OUT, "fig2_agents.png"))
plt.close()

# ── Fig 3: Tool Call Loop ──
fig, ax = plt.subplots(figsize=(6, 3))
ax.set_xlim(0, 8); ax.set_ylim(0, 4); ax.axis("off")
boxes = [
    (0.5, 2.5, "User\nPrompt", "#E3F2FD"), (2.2, 2.5, "Brain\n(LLM)", "#BBDEFB"),
    (4.2, 2.5, "Tool Call?", "#FFF9C4"), (6.0, 2.5, "Response", "#C8E6C9"),
    (4.2, 0.5, "Hands\n(Execute)", "#FFE0B2"), (2.2, 0.5, "Result", "#D1C4E9"),
]
for x, y, label, color in boxes:
    ax.add_patch(mpatches.FancyBboxPatch((x, y), 1.4, 1.0, boxstyle="round,pad=0.08", facecolor=color, edgecolor="#333", lw=0.8))
    ax.text(x+0.7, y+0.5, label, ha="center", va="center", fontsize=7.5, fontweight="bold")
arrows = [
    ((1.9, 3.0), (2.2, 3.0)), ((3.6, 3.0), (4.2, 3.0)), ((5.6, 3.0), (6.0, 3.0)),
    ((4.9, 2.5), (4.9, 1.5)), ((4.2, 1.0), (3.6, 1.0)), ((2.2, 1.0), (1.5, 1.0)),
]
for (x1,y1),(x2,y2) in arrows:
    ax.annotate("", xy=(x2,y2), xytext=(x1,y1), arrowprops=dict(arrowstyle="->", color="#555", lw=1.2))
ax.annotate("", xy=(2.2, 1.5), xytext=(1.5, 1.5), arrowprops=dict(arrowstyle="->", color="#d32f2f", lw=1.2, connectionstyle="arc3,rad=0.3"))
ax.text(1.0, 1.8, "loop\n(max 8)", fontsize=6, color="#d32f2f", ha="center")
ax.text(5.3, 2.2, "Yes", fontsize=6, color="#666"); ax.text(5.9, 3.2, "No", fontsize=6, color="#666")
ax.set_title("Fig. 3: ReAct Tool-Call Loop", fontsize=9, fontweight="bold")
fig.savefig(os.path.join(OUT, "fig3_toolcall.png"))
plt.close()

# ── Fig 4: Theoretical Physicist Modules ──
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.set_xlim(0, 10); ax.set_ylim(0, 4.5); ax.axis("off")
modules = [
    (0.3, 3.3, "M0\nData\nIngestion", "#E0E0E0"),
    (1.5, 3.3, "M1\nHamiltonian\nModeling", "#FFCDD2"),
    (2.7, 3.3, "M2\nNoise\nBudget", "#C8E6C9"),
    (3.9, 3.3, "M3\nParameter\nInversion", "#BBDEFB"),
    (5.1, 3.3, "M4\nExperiment\nDesign", "#FFF9C4"),
    (6.3, 3.3, "M5\nPulse\nOptim.", "#FFE0B2"),
    (7.5, 3.3, "M6\nDiagnosis", "#D1C4E9"),
    (1.5, 1.5, "M7\nDesign\nOptimization", "#B2DFDB"),
    (3.9, 1.5, "M8\nKnowledge\nRetrieval", "#FFECB3"),
]
for x, y, label, color in modules:
    ax.add_patch(mpatches.FancyBboxPatch((x, y), 1.05, 0.95, boxstyle="round,pad=0.05", facecolor=color, edgecolor="#333", lw=0.7))
    ax.text(x+0.525, y+0.475, label, ha="center", va="center", fontsize=6.5, fontweight="bold")
for i in range(6):
    ax.annotate("", xy=(modules[i+1][0], modules[i+1][1]+0.475), xytext=(modules[i][0]+1.05, modules[i][1]+0.475),
                arrowprops=dict(arrowstyle="->", color="#555", lw=0.8))
ax.annotate("", xy=(modules[7][0]+0.525, modules[7][1]+0.95), xytext=(modules[6][0]+0.525, modules[6][1]),
            arrowprops=dict(arrowstyle="->", color="#d32f2f", lw=1, connectionstyle="arc3,rad=-0.5"))
ax.text(5, 0.8, "Data Objects: DeviceGraph, HamiltonianModel, NoiseModel,\nCalibratedModelState, ExperimentPlan, DiagnosisReport, DesignProposal",
        fontsize=6.5, ha="center", style="italic", color="#555")
ax.set_title("Fig. 4: Theoretical Physicist Agent - Nine Functional Modules", fontsize=9, fontweight="bold")
fig.savefig(os.path.join(OUT, "fig4_modules.png"))
plt.close()

# ── Fig 5: Design Pipeline ──
fig, ax = plt.subplots(figsize=(7, 2))
ax.set_xlim(0, 10); ax.set_ylim(0, 2.5); ax.axis("off")
steps = [
    ("NL\nPrompt", "#E3F2FD"), ("Orchestrator\nRoute", "#BBDEFB"),
    ("create_design\n(Metal)", "#C8E6C9"), ("add_transmon\n(\u00d720)", "#A5D6A7"),
    ("add_route\n(\u00d719)", "#81C784"), ("export_gds", "#66BB6A"),
    ("Q3D\nExtraction", "#FFF9C4"), ("Validate\n(Theory)", "#FFCDD2"),
]
for i, (label, color) in enumerate(steps):
    x = 0.2 + i * 1.22
    ax.add_patch(mpatches.FancyBboxPatch((x, 0.7), 1.05, 1.0, boxstyle="round,pad=0.05", facecolor=color, edgecolor="#333", lw=0.7))
    ax.text(x+0.525, 1.2, label, ha="center", va="center", fontsize=6, fontweight="bold")
    if i < 7:
        ax.annotate("", xy=(x+1.22, 1.2), xytext=(x+1.1, 1.2), arrowprops=dict(arrowstyle="->", color="#555", lw=0.8))
ax.set_title("Fig. 5: 20-Qubit Chip Design Pipeline", fontsize=9, fontweight="bold")
fig.savefig(os.path.join(OUT, "fig5_pipeline.png"))
plt.close()

# ── Fig 7: Noise Budget (bar chart from experiment data) ──
noise = data["exp2_noise"]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3))

t1_data = noise["T1_breakdown_us"]
t1_mechs = ["Purcell", "Dielectric", "TLS", "Quasiparticle", "Radiation"]
t1_vals = [t1_data["Purcell"], t1_data["dielectric_loss"], t1_data["TLS"], t1_data["quasiparticle"], t1_data["radiation"]]
t1_rates = [1/v * 1000 for v in t1_vals]
colors1 = ["#EF5350", "#FF7043", "#FFA726", "#66BB6A", "#42A5F5"]
ax1.barh(t1_mechs, t1_rates, color=colors1, edgecolor="#333", linewidth=0.5)
ax1.set_xlabel("Relaxation Rate (1/ms)")
ax1.set_title("T1 Decomposition", fontsize=9, fontweight="bold")
ax1.invert_yaxis()

t2_data = noise["T2_breakdown_us"]
t2_mechs = ["T1 limit", "Flux noise", "Thermal", "Charge"]
t2_vals = [t2_data["T1_limit"], t2_data["flux_noise_Tphi"], t2_data["thermal_photon_Tphi"], t2_data["charge_noise_Tphi"]]
t2_rates = [1/v * 1000 for v in t2_vals]
colors2 = ["#AB47BC", "#EF5350", "#FF7043", "#66BB6A"]
ax2.barh(t2_mechs, t2_rates, color=colors2, edgecolor="#333", linewidth=0.5)
ax2.set_xlabel("Dephasing Rate (1/ms)")
ax2.set_title("T2 Decomposition", fontsize=9, fontweight="bold")
ax2.invert_yaxis()

fig.suptitle("Fig. 7: Noise Budget Analysis for Q1", fontsize=10, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig7_noise_budget.png"))
plt.close()

# ── Fig 8 (bonus): Qubit Frequency Comparison ──
ham = data["exp1_hamiltonian"]
q_ids = [qp["qubit_id"] for qp in ham["qubit_params"]]
q_freqs = [qp["freq_01_GHz"] for qp in ham["qubit_params"]]
design_freqs = [5.152 if i % 2 == 0 else 4.650 for i in range(20)]

fig, ax = plt.subplots(figsize=(7, 3))
x = np.arange(20)
ax.bar(x - 0.15, design_freqs, 0.3, label="Design", color="#42A5F5", edgecolor="#333", linewidth=0.5)
ax.bar(x + 0.15, q_freqs, 0.3, label="Agent Predicted", color="#EF5350", edgecolor="#333", linewidth=0.5)
ax.set_xticks(x); ax.set_xticklabels(q_ids, fontsize=5.5, rotation=45)
ax.set_ylabel("Frequency (GHz)"); ax.set_ylim(4.4, 5.4)
ax.legend(fontsize=7); ax.grid(axis="y", alpha=0.3)
ax.set_title("Fig. 8: Qubit Frequency - Design vs. Agent Prediction", fontsize=9, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig8_freq_comparison.png"))
plt.close()

# ── Fig 9 (bonus): Simulation Results Q1-Q5 ──
sim_data = data["exp5_simulation"]["simulations"]
fig, axes = plt.subplots(1, 4, figsize=(7, 2.5))
labels = [s["qubit"] for s in sim_data]
metrics = [
    ("C_self (fF)", [s["q3d_summary"]["C_self_fF"] for s in sim_data], "#42A5F5"),
    ("g (MHz)", [s["q3d_summary"]["g_nearest_MHz"] for s in sim_data], "#66BB6A"),
    ("f_01 (GHz)", [s["lom_summary"]["freq_GHz"] for s in sim_data], "#EF5350"),
    ("Q factor", [s["eigenmode_summary"]["Q_factor"] for s in sim_data], "#AB47BC"),
]
for ax, (title, vals, color) in zip(axes, metrics):
    ax.bar(labels, vals, color=color, edgecolor="#333", linewidth=0.5)
    ax.set_title(title, fontsize=7, fontweight="bold")
    ax.tick_params(labelsize=6)
fig.suptitle("Fig. 9: Full-Chip Simulation Results (Q1-Q5)", fontsize=9, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig9_simulation.png"))
plt.close()

print("All figures generated:")
for f in sorted(os.listdir(OUT)):
    print(f"  {f}: {os.path.getsize(os.path.join(OUT, f)):,} bytes")
