"""
运行论文所需的 6 组实验，收集数据并保存为 JSON
"""
import sys, os, json
sys.path.insert(0, r"E:\work\QuantaMind")
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from quantamind.server import hands_theorist as th
from quantamind.server import hands_simulation as sim

results = {}

# Exp 1: Hamiltonian Model
print("=== Exp 1: Hamiltonian Model ===")
dg = th.build_device_graph(
    chip_id="TG5.440.0001WX",
    qubits=[f"Q{i+1}" for i in range(20)],
    jj_params={"EJ_GHz": 14.21, "EC_GHz": 0.260, "type": "Manhattan_SQUID"},
    chip_size_mm=[12.5, 12.5],
)
ham = th.build_hamiltonian(dg["graph_id"], quantization_method="EPR", truncation_dim=4)
results["exp1_hamiltonian"] = ham
print(f"  Qubits: {len(ham['qubit_params'])}, Couplers: {len(ham['coupler_params'])}")

# Exp 2: Noise Budget
print("=== Exp 2: Noise Budget ===")
noise = th.compute_noise_budget(ham["model_id"], t1_measured_us=45.0, t2_measured_us=30.0, temperature_mK=15.0)
results["exp2_noise"] = noise
print(f"  Dominant: {noise['dominant_noise_ranking'][0]['mechanism']}")

# Exp 3: Root-Cause Diagnosis
print("=== Exp 3: Root-Cause Diagnosis ===")
diag_gate = th.diagnose_root_cause("gate_error_high", {"fidelity_pct": 98.5})
diag_t1 = th.diagnose_root_cause("t1_degradation", {"T1_us": 25})
diag_freq = th.diagnose_root_cause("frequency_drift", {"drift_MHz_per_hour": 0.5})
diag_read = th.diagnose_root_cause("readout_error_high", {"readout_fidelity_pct": 96.5})
results["exp3_diagnosis"] = {
    "gate_error": diag_gate,
    "t1_degradation": diag_t1,
    "frequency_drift": diag_freq,
    "readout_error": diag_read,
}
print(f"  Gate top cause: {diag_gate['root_cause_ranking'][0]['root_cause']}")

# Exp 4: Experiment Design
print("=== Exp 4: Experiment Design ===")
plan_noise = th.plan_experiment(objective="identify_dominant_noise", budget_hours=8.0)
plan_gate = th.plan_experiment(objective="gate_error_diagnosis", budget_hours=6.0)
plan_readout = th.plan_experiment(objective="readout_optimization", budget_hours=3.0)
results["exp4_plans"] = {
    "noise": plan_noise,
    "gate": plan_gate,
    "readout": plan_readout,
}
print(f"  Noise plan: {len(plan_noise['scheduled_experiments'])} experiments, {plan_noise['total_duration_hours']}h")

# Exp 5: Full Chip Simulation (Q1-Q5)
print("=== Exp 5: Full Chip Simulation ===")
full_sim = sim.run_full_chip_simulation(chip_name="20bit_tunable_coupler", qubit_ids=["Q1","Q2","Q3","Q4","Q5"])
results["exp5_simulation"] = full_sim
print(f"  Simulated {len(full_sim['simulations'])} qubits")

# Exp 6: Pulse Optimization + Design Proposal
print("=== Exp 6: Pulse + Design Proposal ===")
pulse_x = th.optimize_control_pulse(ham["model_id"], gate_type="single_qubit_X", optimization_method="DRAG")
pulse_cz = th.optimize_control_pulse(ham["model_id"], gate_type="CZ", optimization_method="GRAPE")
proposal = th.generate_design_proposal(target_gate_fidelity=0.999, target_t1_us=80)
results["exp6_optimization"] = {
    "pulse_X": pulse_x,
    "pulse_CZ": pulse_cz,
    "design_proposal": proposal,
}
print(f"  X gate fidelity: {pulse_x['predicted_fidelity']}")
print(f"  CZ gate fidelity: {pulse_cz['predicted_fidelity']}")

# Save all results
out_file = r"E:\work\QuantaMind\docs\paper_experiment_data.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
print(f"\nAll experiment data saved: {out_file}")
print(f"File size: {os.path.getsize(out_file):,} bytes")
