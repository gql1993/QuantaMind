# QuantaMind Paper Writing Workspace

## Task
Write a 20+ page PhD-level academic paper about QuantaMind (quantum research multi-agent system).
Target: Springer LNCS format, single-column, single-space, all English, 50+ references.

## Current Best Draft
- `E:\work\QuantaMind\docs\QuantaMind_Paper_LNCS_final.docx` — 17.4 pages, 193 paragraphs, 8 tables, 8 figures, no Chinese
- Needs: expand to 20+ pages, improve figure quality, add more references from QDA paper

## Template
- `E:\work\QuantaMind\demo\splnproc2510.docx` — Springer LNCS Word template (converted from .docm)
- Styles: papertitle, author, address, abstract, keywords, heading1, heading2, p1a, Normal, figurecaption, tablecaption, equation, referenceitem, acknowlegments

## Experiment Data
- `E:\work\QuantaMind\docs\paper_experiment_data.json` (34,788 bytes)
- Contains: exp1_hamiltonian (20 qubits, 19 couplers), exp2_noise (T1/T2 breakdown), exp3_diagnosis (4 anomaly types), exp4_plans (3 experiment plans), exp5_simulation (Q1-Q5 full sim), exp6_optimization (X 99.925%, CZ 99.84%)

## Figures (all PNG, in E:\work\QuantaMind\docs\paper_figures\)
- fig1_architecture.png (77KB) — 6-layer system architecture
- fig2_agents.png (45KB) — 12 agent workflow
- fig3_toolcall.png (34KB) — ReAct tool-call loop
- fig4_modules.png (79KB) — M0-M8 theoretical physicist modules
- fig5_pipeline.png (39KB) — 20-qubit design pipeline
- fig7_noise_budget.png (48KB) — T1/T2 noise decomposition bar chart
- fig8_freq_comparison.png (38KB) — qubit frequency design vs predicted
- fig9_simulation.png (35KB) — Q1-Q5 simulation results (4 subplots)

## Reference Papers (for style and citations)
1. `E:\量子科技\凌浩工程\AI for quantum\AI加量子论文\El Agente An Autonomous Agent for Quantum.pdf` — 203 pages, El Agente Q architecture, hierarchical multi-agent, quantum chemistry
2. `E:\量子科技\凌浩工程\AI for quantum\AI加量子论文\automating quantum simulations.pdf` — 76 pages, El Agente Cuantico, quantum simulation automation
3. `C:\Users\Huawei\Desktop\Quantum Design Automation.pdf` — 143 pages, 562 references, comprehensive QDA survey (layout, simulation, Hamiltonian, decoherence, TCAD, verification, QEC)
4. `C:\Users\Huawei\Desktop\Bridging the Racial Gap...docx` — Reference for LNCS formatting (heading style, table style, reference format)

## Reference Format (from Bridging paper)
```
Author A, Author B, Author C, et al. Title[J]. Journal, Year, Volume(Issue): Pages.
Author A, Author B. Title[C]//Conference. Year: Pages.
Author A. Title[A]. arXiv:XXXX.XXXXX, Year.
Author A. Title[EB/OL]. URL, Year.
```

## Key Real References to Include
- arXiv:2603.08801 — LLM-Assisted SC Qubit Experiments
- arXiv:2508.18027 — QDesignOptimizer (physics-guided SC design)
- arXiv:2510.00967 — QUASAR (quantum assembly via agentic RL)
- arXiv:2411.16354 — GNN-based scalable SC parameter design
- arXiv:2511.08493 — Google RL-based continuous calibration for QEC
- arXiv:2508.14111 — From AI for Science to Agentic Science (survey)
- arXiv:2511.08151 — SciAgent for scientific reasoning
- arXiv:2511.10479 — Quantum Design Automation (comprehensive survey)
- arXiv:2505.02484 — El Agente Q
- arXiv:2512.18847 — El Agente Cuantico

## Design Document
- `E:\work\QuantaMind\docs\QEDA\20比特可调耦合器双比特设计方案.docx`
- Key params: 12.5mm x 12.5mm, 20 qubits 1D chain, 19 tunable couplers, Qodd=5.152GHz, Qeven=4.650GHz, coupler=6.844GHz, 48 SMP pads

## QuantaMind System Design
- `E:\work\QuantaMind\docs\QuantaMind量智大脑详细设计说明书.md` — Full system design doc

## QuantaMind Source Code
- Gateway: `E:\work\QuantaMind\quantamind\server\gateway.py`
- Brain: `E:\work\QuantaMind\quantamind\server\brain.py`
- Orchestrator: `E:\work\QuantaMind\quantamind\agents\orchestrator.py`
- Hands (tools): `E:\work\QuantaMind\quantamind\server\hands.py` + 10 adapter files
- Theoretical Physicist: `E:\work\QuantaMind\quantamind\server\hands_theorist.py`
- Simulation: `E:\work\QuantaMind\quantamind\server\hands_simulation.py`
- Heartbeat: `E:\work\QuantaMind\quantamind\server\heartbeat.py`
- GDS Generator: `E:\work\QuantaMind\quantamind\server\gds_generator.py`
- Chip Designer: `E:\work\QuantaMind\quantamind\server\chip_designer_metal.py`

## Previous Generation Scripts
- `E:\work\QuantaMind\docs\run_paper_experiments.py` — runs all 6 experiments
- `E:\work\QuantaMind\docs\generate_paper_figures.py` — generates all 8 figures
- `E:\work\QuantaMind\docs\generate_paper_word_v4.py` — latest manual generation script
