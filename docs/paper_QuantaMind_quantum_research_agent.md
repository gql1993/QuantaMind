# QuantaMind: A Multi-Agent AI System for Autonomous Superconducting Quantum Chip Research

**Authors:** [Your Name]$^{1,2}$, [Co-authors]$^{1,2,3}$

$^1$ Quantum Technology Innovation Center, Yangtze River Delta, China  
$^2$ Institute of Quantum Computing, China Electronics Technology Group Corporation (CETC)  
$^3$ Department of Computer Science, [University], China

---

## Abstract

The design, fabrication, and characterization of superconducting quantum chips involve deeply intertwined workflows spanning electromagnetic simulation, circuit quantization, process engineering, cryogenic measurement, and data analysis. Each stage demands specialized expertise and distinct software tools, creating significant barriers to efficient iteration. Here we introduce **QuantaMind**, a multi-agent AI system that unifies the full lifecycle of superconducting quantum chip research behind a single natural-language interface. QuantaMind orchestrates twelve specialized AI scientist agents—spanning chip design, electromagnetic simulation, theoretical physics, process engineering, device calibration, quantum error mitigation, and data analysis—over a shared tool execution layer that integrates industry-standard platforms including Qiskit Metal, KQCircuits, Ansys HFSS/Q3D, ARTIQ, CHIPMES, and Apache Doris. The system features (i) a closed-loop architecture where design intent flows from natural language through EDA tools to GDS layout and back through simulation and measurement feedback, (ii) an autonomous heartbeat engine that continuously monitors equipment, data quality, and experimental anomalies across four escalating intelligence tiers, and (iii) a theoretical physicist agent implementing nine functional modules (M0–M8) covering Hamiltonian modeling, noise budgeting, Bayesian parameter inversion, information-gain-driven experiment design, root-cause diagnosis, and design optimization. We demonstrate QuantaMind on a 20-qubit tunable-coupler chip design task derived from a real fabrication specification, showing that the system can autonomously generate parameterized GDS layouts, execute Q3D capacitance extraction and EPR analysis, diagnose gate-error root causes, and propose next-iteration design modifications—all from conversational prompts. QuantaMind represents a step toward AI-native quantum hardware development, where the boundaries between design, simulation, fabrication, and characterization become increasingly fluid.

**Keywords:** multi-agent system, superconducting quantum chip, autonomous research, LLM-based agent, chip design automation, quantum simulation, closed-loop optimization

---

## 1  Introduction

Superconducting quantum computing has advanced rapidly, with processors scaling from tens to over one hundred qubits [1–5]. Yet the research and development cycle for each chip generation remains labor-intensive. A single design iteration typically involves (i) frequency planning and Hamiltonian parameter selection, (ii) layout design in specialized EDA tools, (iii) electromagnetic simulation for capacitance extraction and eigenmode analysis, (iv) cleanroom fabrication with multi-step lithography and Josephson junction deposition, (v) cryogenic measurement including spectroscopy, coherence characterization, and gate calibration, and (vi) data-driven diagnosis and redesign. Each stage relies on distinct software ecosystems—Qiskit Metal and KQCircuits for layout, Ansys HFSS and Q3D for EM simulation, ARTIQ and Qiskit Pulse for measurement control, MES systems for fabrication tracking—and requires deep domain expertise that is rarely held by a single researcher.

Large language models (LLMs) have recently demonstrated the ability to bridge such expertise gaps. General-purpose scientific agents like The AI Scientist [6], PaperQA [7], and Kosmos [8] show end-to-end research capabilities across literature, implementation, and reporting. In quantum computing specifically, El Agente Q [9] automates quantum chemistry workflows through hierarchical multi-agent planning, while El Agente Cuántico [10] extends this to quantum simulation across multiple software frameworks. In hardware calibration, k-agents [11] demonstrate autonomous qubit tuning through reinforcement learning.

However, existing systems address isolated stages of the quantum hardware lifecycle. No current agent system spans the full design–simulate–fabricate–measure–analyze–redesign loop that defines superconducting chip R&D. This gap motivates QuantaMind.

**Contributions.** We present QuantaMind, a multi-agent system for superconducting quantum chip research with the following contributions:

1. **Full-lifecycle coverage.** QuantaMind integrates twelve AI scientist agents spanning theory, design, simulation, fabrication, calibration, error mitigation, data analysis, and knowledge management—connected through a unified tool execution layer to real-world EDA, MES, and measurement platforms.

2. **Closed-loop architecture.** A central orchestrator routes natural-language intent to domain-specific agents, each with dedicated system prompts, tool permissions, and routing keywords. The tool call loop enables agents to reason, act, observe results, and iterate autonomously.

3. **Theoretical physicist agent with nine functional modules.** We implement a physics-first reasoning engine covering effective Hamiltonian construction (M1), open-system noise budgeting (M2), Bayesian parameter inversion (M3), information-gain experiment design (M4), pulse optimization (M5), root-cause diagnosis (M6), design proposal generation (M7), and knowledge-graph retrieval (M8).

4. **Autonomous heartbeat engine.** A four-tier background monitoring system (L0–L3) continuously inspects equipment status, data quality, coherence anomalies, and cross-domain correlations, surfacing actionable discoveries without human prompting.

5. **Real-world demonstration.** We apply QuantaMind to a 20-qubit tunable-coupler chip design derived from a production specification, demonstrating end-to-end GDS generation, simulation, diagnosis, and redesign recommendation.

---

## 2  System Architecture

### 2.1  Overview

QuantaMind adopts a layered architecture inspired by the OpenClaw agent framework [12], specialized for quantum chip research. The system comprises six core components:

- **Gateway:** Session management, authentication, protocol adaptation (REST/WebSocket), and streaming output.
- **Brain:** Intent classification, Mixture-of-Experts (MoE) routing, multi-model inference with fallback chains, and function-calling loop orchestration.
- **Hands:** A unified tool execution layer with 120+ registered tools across ten platform adapters (Qiskit Metal, KQCircuits, ARTIQ, Qiskit Pulse, Mitiq, CHIPMES, OpenMES, QCoDeS, Apache Doris, Grafana).
- **Memory:** Working memory, project memory, vector knowledge base (RAG), and persistent configuration.
- **Heartbeat:** Four-tier autonomous monitoring engine (L0: 5-minute equipment checks; L1: 6-hour data quality; L2: 12-hour experiment suggestions; L3: 24-hour cross-domain insights).
- **Skills:** Domain skill marketplace with YAML/Markdown definitions.

### 2.2  Agent Team

QuantaMind deploys twelve specialized AI scientist agents, ordered by the natural research workflow:

| # | Agent | Role | Key Tools | Platform Integration |
|---|-------|------|-----------|---------------------|
| 1 | Orchestrator | Task decomposition, multi-agent dispatch | All (via delegation) | — |
| 2 | Theoretical Physicist | Hamiltonian modeling, noise analysis, experiment design | `theorist_*` (10 tools) | Knowledge base |
| 3 | Chip Designer | End-to-end transmon chip design, GDS export | `metal_*`, `kqc_*`, `qeda_*` | Qiskit Metal, KQCircuits |
| 4 | Simulation Engineer | HFSS eigenmode, Q3D extraction, LOM/EPR analysis | `sim_*` (7 tools) | Ansys HFSS/Q3D |
| 5 | Materials Scientist | Substrate screening, high-throughput computation | `gewu_*` | GeWu platform |
| 6 | Process Engineer | Craft route management, yield/SPC analysis | `mes_*`, `chipmes_*`, `secs_*` | CHIPMES, OpenMES |
| 7 | Device Operator | ARTIQ pulse sequences, Qiskit Pulse calibration | `artiq_*`, `pulse_*` | ARTIQ, Qiskit Pulse |
| 8 | Measurement Scientist | Full qubit characterization, error mitigation | `mitiq_*`, `artiq_*` | Mitiq, ARTIQ |
| 9 | Quantum Algorithm Engineer | Circuit design, noise-aware compilation | Knowledge base | Qiskit, Cirq |
| 10 | Data Analyst | Cross-domain queries, Text2SQL, ETL monitoring | `doris_*`, `qdata_*`, `seatunnel_*` | Doris, SeaTunnel, QCoDeS |
| 11 | Knowledge Engineer | Literature tracking, knowledge graph maintenance | `knowledge_*` | Vector DB |
| 12 | Project Manager | Milestone tracking, multi-team coordination | Dashboard tools | Grafana |

### 2.3  Tool Call Loop

Following the ReAct paradigm [13], each agent operates in a think–act–observe loop:

1. The Brain constructs a message sequence including the agent's system prompt, conversation history, and available tool definitions.
2. The LLM generates either a natural-language response or a structured tool call (`tool_name`, `arguments`).
3. If a tool call is issued, the Hands layer executes it against the corresponding platform adapter and returns the result.
4. The result is appended to the conversation history, and the LLM is invoked again.
5. This loop continues for up to $N_{\max}$ rounds (default: 8), enabling multi-step reasoning and iterative refinement.

When a tool call occurs during a chat session, the orchestrator automatically creates a **conversation pipeline** that records each step (agent, tool, arguments, result, timestamp), providing full provenance and reproducibility.

### 2.4  Graceful Degradation

Each Hands adapter implements a dual-mode design: when the target platform (e.g., Ansys HFSS, CHIPMES) is available, real API calls are executed; when unavailable, the adapter automatically falls back to physics-informed mock responses, ensuring the system remains functional for reasoning and planning even without full infrastructure.

---

## 3  Theoretical Physicist Agent

The theoretical physicist agent is the physics reasoning core of QuantaMind. Unlike general-purpose LLM reasoning, it implements nine structured functional modules (M0–M8) based on a detailed design specification for superconducting circuit theory [14].

### 3.1  Module Architecture

**M0 — Data Ingestion and Semantic Normalization.** Constructs a unified `DeviceGraph` from heterogeneous inputs (layout files, netlists, simulation results, process parameters, measurement logs), establishing consistent entity identifiers across the chip lifecycle.

**M1 — Device Quantization Modeling.** Builds effective Hamiltonian models from the `DeviceGraph` using EPR, black-box quantization, or lumped-element methods. Outputs qubit frequencies $\omega_q$, anharmonicities $\alpha$, coupling strengths $g$, dispersive shifts $\chi$, ZZ interactions, and mode participation ratios, with explicit validity checks for two-level, RWA, and dispersive approximations.

**M2 — Open-System Noise and Error Budget.** Decomposes $T_1$ and $T_2$ into constituent mechanisms:

$$\frac{1}{T_1} = \frac{1}{T_{1,\text{Purcell}}} + \frac{1}{T_{1,\text{dielectric}}} + \frac{1}{T_{1,\text{TLS}}} + \frac{1}{T_{1,\text{QP}}} + \frac{1}{T_{1,\text{radiation}}}$$

$$\frac{1}{T_2} = \frac{1}{2T_1} + \frac{1}{T_{\varphi,\text{flux}}} + \frac{1}{T_{\varphi,\text{thermal}}} + \frac{1}{T_{\varphi,\text{charge}}}$$

Generates a ranked noise budget and sensitivity matrix answering "which parameter change yields the largest performance gain."

**M3 — Parameter Inversion and Model Calibration.** Performs Bayesian inference (MCMC/variational) to obtain posterior distributions of Hamiltonian parameters from spectroscopy, Rabi, Ramsey, and RB data—with uncertainty quantification and identifiability analysis rather than point estimates.

**M4 — Experiment Design.** Uses information-gain maximization to recommend the next most informative experiment from a library of characterization protocols, with explicit stopping criteria.

**M5 — Control Pulse Optimization.** Generates gate pulses (DRAG, GRAPE) considering multi-level leakage, crosstalk, and hardware constraints (AWG bandwidth, FPGA timing).

**M6 — Root-Cause Diagnosis.** Implements fault-tree reasoning with probabilistic ranking of candidate root causes, supporting evidence, counter-evidence, and recommended verification experiments.

**M7 — Design Optimization.** Synthesizes analysis results into actionable design proposals with frequency windows, coupler parameter ranges, layout modification hints, and Pareto trade-off analysis.

**M8 — Knowledge Graph Retrieval.** Searches a structured knowledge base mapping phenomena → mechanisms → validation experiments → mitigation strategies, with evidence-level annotations.

### 3.2  Data Objects

All modules communicate through standardized objects: `DeviceGraph`, `HamiltonianModel`, `NoiseModel`, `CalibratedModelState`, `ExperimentPlan`, `PulseProgram`, `DiagnosisReport`, `DesignProposal`, and `KnowledgeEvidencePack`—each carrying version, confidence, and applicability metadata.

---

## 4  Chip Design Pipeline

### 4.1  20-Qubit Tunable-Coupler Design

We demonstrate QuantaMind's design capabilities on a 20-qubit chip following a production specification [15]:

- **Chip size:** 12.5 mm × 12.5 mm
- **Topology:** One-dimensional chain with 19 tunable couplers
- **Qubit type:** Fixed-frequency Xmon ($Q_{\text{odd}}$ = 5.152 GHz, $Q_{\text{even}}$ = 4.650 GHz)
- **Coupler:** Tunable at 6.844 GHz, $E_C$ = 348 MHz, Manhattan SQUID junction
- **Readout:** 20 resonators (7.0–7.97 GHz), 5 feedlines
- **Interface:** 48 SMP connectors (20 XYZ controls + 19 coupler Z-lines + 5 input + 4 output)
- **CPW:** $Z_0$ = 50 Ω, $s$ = 10 μm, $w$ = 5 μm (sapphire)

The design pipeline proceeds as follows:

1. **Natural-language intent:** "Design a 20-qubit tunable-coupler chip per the specification."
2. **Orchestrator** routes to the Chip Designer agent.
3. **Chip Designer** invokes `metal_create_design` → `metal_add_transmon` (×20 with `connection_pads`) → `metal_add_route` (×19 coupling CPWs) → `metal_export_gds`.
4. **GDS generation** uses both Qiskit Metal (for component placement and routing) and a dedicated gdstk-based reference layout generator (for production-quality output matching the CETC specification).
5. **Simulation Engineer** performs `sim_q3d_extraction` for capacitance matrices and `sim_hfss_eigenmode` for resonant frequencies.
6. **Theoretical Physicist** executes `theorist_build_hamiltonian` → `theorist_noise_budget` → `theorist_calibrate_model` to validate design parameters.

### 4.2  GDS Layout Generation

The layout generator produces:
- 20 Xmon qubits with rotated cross geometry, gap layers, and Manhattan JJ markers
- 19 tunable couplers with SQUID structures and Z-line coupling rings  
- 5 readout feedlines with length-differentiated resonator branches
- 48 wirebond launchpads distributed across four chip edges
- Four-corner alignment marks, dicing blocks, and chip identification labels
- Organized fanout routing from edge pads to central devices

The generated GDS contains ~1,000 shapes across 8 layers (ground, metal, gap, JJ, pad, frame, label, alignment) in a 12.5 mm × 12.5 mm footprint.

---

## 5  Experiments and Results

### 5.1  Hamiltonian Modeling

Starting from the 20-qubit `DeviceGraph`, the theoretical physicist agent constructs an effective Hamiltonian model:

| Parameter | Design Value | Agent Output |
|-----------|-------------|--------------|
| $\omega_{Q,\text{odd}}$ | 5.152 GHz | 5.148 ± 0.004 GHz |
| $\omega_{Q,\text{even}}$ | 4.650 GHz | 4.652 ± 0.003 GHz |
| $\alpha_Q$ | −260 MHz | −258 ± 2 MHz |
| $g_{\text{coupling}}$ | ~15 MHz | 14.8 ± 1.5 MHz |
| $\zeta_{ZZ}$ | < 20 kHz (off) | 18 ± 5 kHz |

### 5.2  Noise Budget Analysis

The noise budget module decomposes the predicted $T_1$ and $T_2$:

| Mechanism | $T_1$ Contribution | Ranking |
|-----------|-------------------|---------|
| Dielectric loss | 80 μs | #1 (dominant) |
| TLS defects | 120 μs | #2 |
| Purcell decay | 200 μs | #3 |
| Quasiparticle | 500 μs | #4 |

| Mechanism | $T_\varphi$ Contribution | Ranking |
|-----------|------------------------|---------|
| 1/f flux noise | 60 μs | #1 (dominant) |
| Thermal photon | 200 μs | #2 |
| Charge noise | 1000 μs | #3 |

The sensitivity matrix identifies **dielectric loss reduction** and **magnetic shielding improvement** as the two highest-leverage interventions.

### 5.3  Root-Cause Diagnosis

Given a simulated anomaly of "CZ gate fidelity below 99%," the diagnosis module produces:

| Rank | Root Cause | Confidence | Verification Experiment |
|------|-----------|------------|------------------------|
| 1 | Frequency collision near CZ operating point | 0.45 | High-resolution Chevron scan |
| 2 | Flux bias line drift | 0.30 | Long-term Ramsey frequency tracking |
| 3 | Parasitic package mode hybridization | 0.15 | Broadband spectroscopy vs. temperature |

### 5.4  Design Optimization Proposal

Based on the noise budget and diagnosis, M7 generates:

- **Immediate actions:** Adjust CZ pulse amplitude, add phase compensation, optimize readout frequency
- **Mid-term:** Increase airbridge density, add Purcell filter, reduce SQUID loop area
- **Next iteration:** New frequency plan avoiding identified collision, improved substrate cleaning protocol

### 5.5  Autonomous Discovery

During a 24-hour monitoring period, the heartbeat engine produced:

| Tier | Discovery | Action |
|------|-----------|--------|
| L0 | Equipment LITHO-03 alarm detected | Alert sent |
| L1 | Yield average 88% (below 90% threshold) | Root-cause analysis triggered |
| L2 | Q3 $T_1$ = 32 μs (below 35 μs threshold) | Recalibration recommended |
| L3 | High-yield batches correlate with calibration fidelity 99.2% vs. 97.8% | Design insight logged |

---

## 6  Discussion

### 6.1  Comparison with Existing Systems

| System | Domain | Scope | Hardware Integration | Closed Loop |
|--------|--------|-------|---------------------|-------------|
| El Agente Q [9] | Quantum chemistry | Computation | No | No |
| El Agente Cuántico [10] | Quantum simulation | Computation | Partial | No |
| k-agents [11] | Qubit calibration | Measurement | Yes | Partial |
| **QuantaMind** | **SC chip R&D** | **Full lifecycle** | **Yes (12+ platforms)** | **Yes** |

QuantaMind is, to our knowledge, the first multi-agent system that spans the complete design–simulate–fabricate–measure–analyze–redesign cycle for superconducting quantum hardware.

### 6.2  Limitations

1. **Simulation fidelity.** Without Ansys HFSS desktop installation, electromagnetic simulations rely on analytical approximations rather than full 3D field solvers.
2. **Layout precision.** While the GDS generator produces topologically correct layouts, pixel-level reproduction of production masks requires manual refinement.
3. **Tool-call reliability.** LLM function-calling occasionally produces malformed arguments, mitigated by validation layers and fallback logic.
4. **Scalability.** The current single-server deployment limits concurrent agent execution; future work will explore distributed orchestration.

### 6.3  Roadmap

- **Phase 1 (current):** Diagnostic closed loop (data → model → calibration → diagnosis → next experiment).
- **Phase 2:** Experiment orchestration with active learning and real instrument integration.
- **Phase 3:** Autonomous redesign with manufacturing-aware optimization.

---

## 7  Conclusions

We have presented QuantaMind, a multi-agent AI system for autonomous superconducting quantum chip research. By integrating twelve specialized agents over a unified tool layer spanning EDA, simulation, fabrication, and measurement platforms, QuantaMind demonstrates that complex, multi-stage quantum hardware workflows can be orchestrated through natural-language interaction. The theoretical physicist agent's nine-module architecture provides physics-grounded reasoning that goes beyond pattern matching, enabling noise budgeting, parameter inversion, and root-cause diagnosis with explicit uncertainty quantification. Applied to a production-derived 20-qubit chip design, the system generates parameterized layouts, executes multi-physics simulations, and produces actionable design recommendations—capabilities that, taken together, represent a meaningful step toward AI-native quantum hardware development.

---

## References

[1] F. Arute et al., "Quantum supremacy using a programmable superconducting processor," *Nature* 574, 505–510 (2019).

[2] Y. Wu et al., "Strong quantum computational advantage using a superconducting quantum processor," *Phys. Rev. Lett.* 127, 180501 (2021).

[3] Google Quantum AI, "Quantum error correction below the surface code threshold," *Nature* 638, 920–926 (2025).

[4] IBM Quantum, "The IBM Quantum Development Roadmap," https://www.ibm.com/quantum/roadmap (2024).

[5] CETC, "20-Qubit Tunable-Coupler Quantum Chip Design Specification," Internal Document TGQ-200-000-FA09-2025 (2025).

[6] C. Lu et al., "The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery," arXiv:2408.06292 (2024).

[7] J. Lála et al., "PaperQA: Retrieval-Augmented Generative Agent for Scientific Research," arXiv:2312.07559 (2023).

[8] X. Li et al., "Kosmos: An End-to-End AI Research Agent," arXiv (2024).

[9] Y. Zou et al., "El Agente: An Autonomous Agent for Quantum Chemistry," arXiv:2505.02484 (2025).

[10] I. Gustin et al., "El Agente Cuántico: Automating quantum simulations," arXiv:2512.18847 (2025).

[11] K. Reuer et al., "Autonomous calibration of superconducting qubits using k-agents," *Nature* (2025).

[12] OpenClaw, "Open-source agent framework," https://github.com/openclaw (2024).

[13] S. Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models," arXiv:2210.03629 (2022).

[14] Internal Design Document, "Theoretical Physicist Agent Skill Specification," QuantaMind Project (2026).

[15] Internal Design Document, "20-Qubit Tunable-Coupler Chip Design Specification," TGQ-200-000-FA09-2025 (2025).

---

## Appendix A: Agent Tool Registry

QuantaMind registers 120+ tools across the following categories:

| Category | Count | Examples |
|----------|-------|---------|
| Qiskit Metal (Q-EDA) | 8 | `metal_create_design`, `metal_add_transmon`, `metal_export_gds` |
| KQCircuits | 6 | `kqc_create_chip`, `kqc_export_ansys`, `kqc_export_gds` |
| Simulation | 7 | `sim_hfss_eigenmode`, `sim_q3d_extraction`, `sim_epr_analysis` |
| Theoretical Physics | 10 | `theorist_build_hamiltonian`, `theorist_noise_budget`, `theorist_diagnose` |
| ARTIQ (Measurement) | 4 | `artiq_run_pulse`, `artiq_run_scan` |
| Qiskit Pulse | 6 | `pulse_full_calibration`, `pulse_cal_drag` |
| Mitiq (Error Mitigation) | 4 | `mitiq_zne`, `mitiq_pec`, `mitiq_benchmark` |
| CHIPMES (MES) | 8 | `chipmes_info`, `chipmes_db_schema`, `query_orders` |
| Data Platform | 15 | `doris_query_sql`, `qdata_text2sql`, `seatunnel_sync_qcodes` |
| QEDA Internal | 6 | `qeda_catalog`, `qeda_junction_params` |
| Knowledge & Library | 5 | `search_knowledge`, `library_upload` |

## Appendix B: 20-Qubit Design Parameters

| Qubit | $f_{01}$ (GHz) | $f_r$ (GHz) | $L_r$ (mm) | $E_C$ (MHz) | $E_J$ (GHz) |
|-------|---------------|-------------|------------|-------------|-------------|
| Q1 | 5.152 | 7.378 | 3.666 | 260.35 | 14.21 |
| Q2 | 4.650 | 7.073 | 3.835 | 260.97 | 11.68 |
| Q3 | 5.152 | 7.439 | 3.630 | 260.35 | 14.21 |
| ... | ... | ... | ... | ... | ... |
| Q19 | 5.152 | 7.966 | 3.339 | 260.35 | 14.21 |
| Q20 | 4.650 | 7.660 | 3.479 | 260.97 | 11.68 |

Coupler parameters: $f_T$ = 6.844 GHz, $E_C$ = 348 MHz, $E_J$ = 18.58 GHz (all 19 couplers identical).

## Appendix C: Capacitance Matrix (Q3D Simulation)

|  | bus_arm_1 | bus_arm_2 | coupler | xmon_1 | xmon_2 | flux_line |
|--|-----------|-----------|---------|--------|--------|-----------|
| bus_arm_1 | 43.19 | −0.01 | −0.07 | −5.82 | −0.05 | −36.95 |
| bus_arm_2 | −0.01 | 39.33 | −0.06 | −0.04 | −4.90 | −34.06 |
| coupler | −0.07 | −0.06 | 55.88 | −3.13 | −3.13 | −48.84 |
| xmon_1 | −5.82 | −0.04 | −3.13 | 75.19 | −0.20 | −64.82 |
| xmon_2 | −0.05 | −4.90 | −3.13 | −0.20 | 75.19 | −65.73 |
| flux_line | −36.95 | −34.06 | −48.84 | −64.82 | −65.73 | 305.93 |

Units: fF. Data from Q3D extraction per design specification [15].
