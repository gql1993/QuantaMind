"""Generate figures for the framework/collaboration paper."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = r"E:\work\QuantaMind\docs\paper_figures"
os.makedirs(OUT, exist_ok=True)
with open(r"E:\work\QuantaMind\docs\paper_collaboration_experiments.json") as f:
    data = json.load(f)
plt.rcParams.update({"font.size": 9, "figure.dpi": 200, "savefig.bbox": "tight"})

# Fig A: Single vs Multi-Agent comparison
exp1 = data["exp1_single_vs_multi"]
fig, axes = plt.subplots(1, 3, figsize=(7, 2.5))
metrics = [("Success Rate (%)", [exp1["summary"]["single"]["success_rate"], exp1["summary"]["multi"]["success_rate"]]),
           ("Tool Accuracy (%)", [exp1["summary"]["single"]["avg_tool_accuracy"], exp1["summary"]["multi"]["avg_tool_accuracy"]]),
           ("Avg Rounds", [exp1["summary"]["single"]["avg_rounds"], exp1["summary"]["multi"]["avg_rounds"]])]
colors = [["#EF5350", "#42A5F5"]] * 3
for ax, (title, vals) in zip(axes, metrics):
    bars = ax.bar(["Single", "Multi"], vals, color=["#EF5350", "#42A5F5"], edgecolor="#333", lw=0.5, width=0.5)
    ax.set_title(title, fontsize=8, fontweight="bold")
    ax.set_ylim(0, max(vals) * 1.2)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f"{v}", ha="center", fontsize=7)
fig.suptitle("Fig. 5: Single-Agent vs. Multi-Agent Task Completion", fontsize=9, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig5_single_vs_multi.png"))
plt.close()

# Fig B: Routing accuracy per agent
exp2 = data["exp2_routing"]
agents = list(exp2["per_agent_accuracy"].keys())
accs = [exp2["per_agent_accuracy"][a]["accuracy"] for a in agents]
short_names = [a.replace("_engineer","").replace("_scientist","").replace("_analyst","").replace("_","\n") for a in agents]
fig, ax = plt.subplots(figsize=(7, 3))
colors_bar = ["#66BB6A" if a >= 80 else "#FFA726" if a >= 60 else "#EF5350" for a in accs]
bars = ax.bar(range(len(agents)), accs, color=colors_bar, edgecolor="#333", lw=0.5)
ax.set_xticks(range(len(agents)))
ax.set_xticklabels(short_names, fontsize=6.5)
ax.set_ylabel("Routing Accuracy (%)")
ax.set_ylim(0, 110)
ax.axhline(y=exp2["accuracy"], color="#d32f2f", linestyle="--", lw=1, label=f'Overall: {exp2["accuracy"]}%')
for bar, v in zip(bars, accs):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5, f"{v}%", ha="center", fontsize=6.5)
ax.legend(fontsize=7)
ax.set_title("Fig. 6: Intent Routing Accuracy per Agent (50 queries)", fontsize=9, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig6_routing_accuracy.png"))
plt.close()

# Fig C: Tool-call chain depth
exp3 = data["exp3_chain_depth"]
scenarios = exp3["scenarios"]
fig, ax = plt.subplots(figsize=(6, 2.5))
names = [s["scenario"] for s in scenarios]
tools = [s["tools_in_chain"] for s in scenarios]
rounds = [s["actual_rounds"] for s in scenarios]
x = np.arange(len(names))
w = 0.35
ax.bar(x - w/2, tools, w, label="Tools in Chain", color="#42A5F5", edgecolor="#333", lw=0.5)
ax.bar(x + w/2, rounds, w, label="Actual Rounds", color="#66BB6A", edgecolor="#333", lw=0.5)
ax.set_xticks(x)
ax.set_xticklabels(names, fontsize=6.5, rotation=15)
ax.set_ylabel("Count")
ax.legend(fontsize=7)
ax.set_title("Fig. 7: Tool-Call Chain Depth across Scenarios", fontsize=9, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig7_chain_depth.png"))
plt.close()

# Fig D: Cross-agent information retention
exp4 = data["exp4_cross_agent"]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 2.5))
names4 = [s["name"].replace("-to-", "\nto\n").replace("-", "\n") for s in exp4["scenarios"]]
retention = [s["info_retention"] * 100 for s in exp4["scenarios"]]
latency = [s["latency_sec"] for s in exp4["scenarios"]]
ax1.bar(names4, retention, color="#AB47BC", edgecolor="#333", lw=0.5)
ax1.set_ylabel("Information Retention (%)")
ax1.set_ylim(80, 100)
ax1.set_title("Retention", fontsize=8, fontweight="bold")
for i, v in enumerate(retention):
    ax1.text(i, v + 0.3, f"{v:.0f}%", ha="center", fontsize=7)
ax2.bar(names4, latency, color="#FF7043", edgecolor="#333", lw=0.5)
ax2.set_ylabel("Latency (seconds)")
ax2.set_title("End-to-End Latency", fontsize=8, fontweight="bold")
for i, v in enumerate(latency):
    ax2.text(i, v + 1, f"{v}s", ha="center", fontsize=7)
fig.suptitle("Fig. 8: Cross-Agent Pipeline Performance", fontsize=9, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig8_cross_agent.png"))
plt.close()

print("New figures generated:")
for f in ["fig5_single_vs_multi.png", "fig6_routing_accuracy.png", "fig7_chain_depth.png", "fig8_cross_agent.png"]:
    fp = os.path.join(OUT, f)
    print(f"  {f}: {os.path.getsize(fp):,} bytes")
