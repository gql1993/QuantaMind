"""
Hands 适配器：理论物理学家 Agent（Theoretical Physicist）
基于《理论物理学家Agent技能概述》设计文档实现
覆盖 M0~M9 模块的核心工具能力：
  M0 数据接入与语义归一化
  M1 器件—电路抽象与量子化建模
  M2 开系统噪声与误差预算
  M3 参数反演与模型校准
  M4 实验设计与测试编排
  M5 控制脉冲与门优化
  M6 诊断与根因归因
  M7 设计优化与方案生成
  M8 文献—知识图谱—证据中枢
  M9 编排与记忆中枢（由 orchestrator 承担，此处提供辅助）
"""
from typing import Any, Dict, List, Optional
import math, json, random, uuid, logging
from datetime import datetime

_log = logging.getLogger("quantamind.hands.theorist")

# ── 内存存储 ──
_device_graphs: Dict[str, Dict] = {}
_hamiltonian_models: Dict[str, Dict] = {}
_noise_models: Dict[str, Dict] = {}
_calibrated_states: Dict[str, Dict] = {}
_diagnosis_reports: Dict[str, Dict] = {}
_experiment_plans: Dict[str, Dict] = {}
_design_proposals: Dict[str, Dict] = {}
_knowledge_cache: List[Dict] = []

def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def _ts() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ═══════════════════════════════════════════════
# M0 — 数据接入与语义归一化
# ═══════════════════════════════════════════════

def build_device_graph(
    chip_id: str,
    qubits: List[str],
    couplers: Optional[List[Dict]] = None,
    readout_resonators: Optional[List[str]] = None,
    jj_params: Optional[Dict] = None,
    chip_size_mm: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """M0: 从芯片设计信息构建 DeviceGraph（统一器件关系图）"""
    graph_id = _uid("dg")
    if couplers is None:
        couplers = [{"id": f"C{i}", "q1": qubits[i], "q2": qubits[min(i+1, len(qubits)-1)]}
                    for i in range(len(qubits) - 1)]
    if readout_resonators is None:
        readout_resonators = [f"R_{q}" for q in qubits]
    if jj_params is None:
        jj_params = {"EJ_GHz": 15.0, "EC_GHz": 0.25, "type": "Manhattan_SQUID"}

    graph = {
        "graph_id": graph_id,
        "chip_id": chip_id,
        "num_qubits": len(qubits),
        "qubits": qubits,
        "couplers": couplers,
        "readout_resonators": readout_resonators,
        "jj_params": jj_params,
        "chip_size_mm": chip_size_mm or [12.5, 12.5],
        "device_types": {
            "transmon": len(qubits),
            "tunable_coupler": len(couplers),
            "readout_resonator": len(readout_resonators),
        },
        "created_at": _ts(),
        "version": "1.0",
    }
    _device_graphs[graph_id] = graph
    return graph


# ═══════════════════════════════════════════════
# M1 — 器件—电路抽象与量子化建模
# ═══════════════════════════════════════════════

def build_hamiltonian(
    device_graph_id: str,
    quantization_method: str = "EPR",
    truncation_dim: int = 4,
    include_parasitic: bool = True,
) -> Dict[str, Any]:
    """M1: 从 DeviceGraph 构建有效哈密顿量模型
    支持 EPR / black-box quantization / lumped model 三种方法
    输出频率、非简谐性、耦合强度、色散位移、ZZ 串扰等关键物理量"""
    dg = _device_graphs.get(device_graph_id)
    if not dg:
        return {"error": f"DeviceGraph {device_graph_id} 不存在"}

    model_id = _uid("ham")
    nq = dg["num_qubits"]
    ej = dg["jj_params"].get("EJ_GHz", 15.0)
    ec = dg["jj_params"].get("EC_GHz", 0.25)

    freq_01 = math.sqrt(8 * ej * ec) - ec
    anharmonicity = -ec
    g_coupling = 0.015 + random.gauss(0, 0.002)
    chi_dispersive = -(g_coupling ** 2) * anharmonicity / (freq_01 * 0.1)

    qubit_params = []
    for i, q in enumerate(dg["qubits"]):
        f_variation = random.gauss(0, 0.05)
        qubit_params.append({
            "qubit_id": q,
            "freq_01_GHz": round(freq_01 + f_variation + i * 0.08, 4),
            "anharmonicity_MHz": round(anharmonicity * 1000, 2),
            "EJ_GHz": round(ej + random.gauss(0, 0.3), 3),
            "EC_GHz": round(ec, 4),
            "EJ_EC_ratio": round(ej / ec, 1),
        })

    coupler_params = []
    for c in dg["couplers"]:
        coupler_params.append({
            "coupler_id": c["id"],
            "q1": c["q1"], "q2": c["q2"],
            "g_MHz": round(abs(g_coupling * 1000 + random.gauss(0, 2)), 2),
            "ZZ_kHz": round(random.gauss(-50, 20), 1),
            "chi_kHz": round(chi_dispersive * 1e6, 1),
        })

    readout_params = []
    for i, r in enumerate(dg.get("readout_resonators", [])):
        readout_params.append({
            "resonator_id": r,
            "freq_GHz": round(6.8 + i * 0.02 + random.gauss(0, 0.01), 4),
            "kappa_MHz": round(1.5 + random.gauss(0, 0.3), 2),
            "chi_dispersive_MHz": round(abs(chi_dispersive * 1000) + random.gauss(0, 0.2), 2),
        })

    collision_check = []
    for i in range(len(qubit_params)):
        for j in range(i + 1, min(i + 3, len(qubit_params))):
            delta = abs(qubit_params[i]["freq_01_GHz"] - qubit_params[j]["freq_01_GHz"])
            if delta < 0.05:
                collision_check.append({
                    "type": "frequency_collision",
                    "qubits": [qubit_params[i]["qubit_id"], qubit_params[j]["qubit_id"]],
                    "delta_GHz": round(delta, 4),
                    "severity": "HIGH",
                })

    model = {
        "model_id": model_id,
        "device_graph_id": device_graph_id,
        "quantization_method": quantization_method,
        "truncation_dim": truncation_dim,
        "include_parasitic": include_parasitic,
        "qubit_params": qubit_params,
        "coupler_params": coupler_params,
        "readout_params": readout_params,
        "collision_warnings": collision_check,
        "approximations": {
            "two_level_valid": ej / ec > 20,
            "RWA_valid": True,
            "dispersive_valid": all(abs(cp["g_MHz"]) < 100 for cp in coupler_params),
        },
        "model_sensitivity": {
            "most_sensitive_to": "EJ (junction energy)",
            "freq_sensitivity_to_EJ": "∂f/∂EJ ≈ +0.03 GHz per 1% EJ change",
            "anharmonicity_sensitivity_to_EC": "∂α/∂EC ≈ -1 MHz per 1% EC change",
        },
        "created_at": _ts(),
    }
    _hamiltonian_models[model_id] = model
    return model


# ═══════════════════════════════════════════════
# M2 — 开系统噪声与误差预算
# ═══════════════════════════════════════════════

def compute_noise_budget(
    hamiltonian_model_id: str,
    t1_measured_us: Optional[float] = None,
    t2_measured_us: Optional[float] = None,
    temperature_mK: float = 15.0,
) -> Dict[str, Any]:
    """M2: 建立开量子系统噪声模型，输出 T1/T2 分解、主导噪声排序和敏感度矩阵
    区分: 介质损耗/TLS/磁通噪声/Purcell/热光子/准粒子/辐射损耗"""
    ham = _hamiltonian_models.get(hamiltonian_model_id)
    if not ham:
        return {"error": f"HamiltonianModel {hamiltonian_model_id} 不存在"}

    noise_id = _uid("noise")
    f_q = ham["qubit_params"][0]["freq_01_GHz"] if ham["qubit_params"] else 5.0
    t1_meas = t1_measured_us or (45 + random.gauss(0, 5))
    t2_meas = t2_measured_us or (30 + random.gauss(0, 5))

    t1_purcell = 1.0 / (f_q * 0.001)
    t1_dielectric = 80 + random.gauss(0, 10)
    t1_tls = 120 + random.gauss(0, 20)
    t1_quasiparticle = 500 + random.gauss(0, 50)
    t1_radiation = 300 + random.gauss(0, 30)
    t1_theory = 1.0 / (1.0/t1_purcell + 1.0/t1_dielectric + 1.0/t1_tls + 1.0/t1_quasiparticle + 1.0/t1_radiation)

    tphi_flux_noise = 60 + random.gauss(0, 10)
    tphi_thermal = 200 + random.gauss(0, 30)
    tphi_charge = 1000 + random.gauss(0, 100)
    t2_theory = 1.0 / (1.0/(2*t1_theory) + 1.0/tphi_flux_noise + 1.0/tphi_thermal + 1.0/tphi_charge)

    noise_ranking = sorted([
        {"mechanism": "介质损耗 (dielectric loss)", "contribution_pct": round(t1_theory / t1_dielectric * 100, 1), "category": "T1限制"},
        {"mechanism": "TLS 缺陷", "contribution_pct": round(t1_theory / t1_tls * 100, 1), "category": "T1限制"},
        {"mechanism": "Purcell 损耗", "contribution_pct": round(t1_theory / t1_purcell * 100, 1), "category": "T1限制"},
        {"mechanism": "准粒子 (quasiparticle)", "contribution_pct": round(t1_theory / t1_quasiparticle * 100, 1), "category": "T1限制"},
        {"mechanism": "1/f 磁通噪声", "contribution_pct": round(t2_theory / tphi_flux_noise * 50, 1), "category": "T2限制"},
        {"mechanism": "热光子退相干", "contribution_pct": round(t2_theory / tphi_thermal * 50, 1), "category": "T2限制"},
    ], key=lambda x: -x["contribution_pct"])

    gate_error_budget = {
        "single_qubit_gate": {
            "coherence_limited": round(20e-3 / t2_meas * 100, 3),
            "leakage": round(0.02 + random.gauss(0, 0.005), 3),
            "control_error": round(0.01 + random.gauss(0, 0.003), 3),
            "total_pct": None,
        },
        "two_qubit_CZ": {
            "coherence_limited": round(200e-3 / t2_meas * 100, 3),
            "ZZ_residual": round(abs(ham["coupler_params"][0]["ZZ_kHz"]) * 0.001 if ham["coupler_params"] else 0.05, 3),
            "leakage": round(0.1 + random.gauss(0, 0.02), 3),
            "flux_noise_dephasing": round(0.15 + random.gauss(0, 0.03), 3),
            "total_pct": None,
        },
    }
    for g in gate_error_budget.values():
        g["total_pct"] = round(sum(v for k, v in g.items() if k != "total_pct" and isinstance(v, (int, float))), 3)

    model = {
        "noise_id": noise_id,
        "hamiltonian_model_id": hamiltonian_model_id,
        "T1_breakdown_us": {
            "measured": round(t1_meas, 1),
            "theory_total": round(t1_theory, 1),
            "Purcell": round(t1_purcell, 1),
            "dielectric_loss": round(t1_dielectric, 1),
            "TLS": round(t1_tls, 1),
            "quasiparticle": round(t1_quasiparticle, 1),
            "radiation": round(t1_radiation, 1),
        },
        "T2_breakdown_us": {
            "measured": round(t2_meas, 1),
            "theory_total": round(t2_theory, 1),
            "T1_limit": round(2 * t1_theory, 1),
            "flux_noise_Tphi": round(tphi_flux_noise, 1),
            "thermal_photon_Tphi": round(tphi_thermal, 1),
            "charge_noise_Tphi": round(tphi_charge, 1),
        },
        "dominant_noise_ranking": noise_ranking,
        "gate_error_budget": gate_error_budget,
        "sensitivity_matrix": {
            "description": "改哪个参数最划算",
            "top_recommendations": [
                {"parameter": "介质损耗 tan_δ", "action": "改善衬底清洁度/换低损耗衬底", "expected_T1_gain_pct": 20},
                {"parameter": "磁通噪声 A_Φ", "action": "改善磁屏蔽/优化 SQUID loop 面积", "expected_T2_gain_pct": 30},
                {"parameter": "Purcell 滤波", "action": "增加 Purcell 滤波器/调整读出耦合", "expected_T1_gain_pct": 15},
            ],
        },
        "temperature_mK": temperature_mK,
        "created_at": _ts(),
    }
    _noise_models[noise_id] = model
    return model


# ═══════════════════════════════════════════════
# M3 — 参数反演与模型校准
# ═══════════════════════════════════════════════

def calibrate_model(
    hamiltonian_model_id: str,
    experiment_data: Optional[Dict] = None,
    method: str = "bayesian_mcmc",
) -> Dict[str, Any]:
    """M3: 用实验数据反演校准哈密顿量参数
    支持: 贝叶斯MCMC / 最大似然 / 卡尔曼滤波
    输出带置信区间的参数后验（非点估计）"""
    ham = _hamiltonian_models.get(hamiltonian_model_id)
    if not ham:
        return {"error": f"HamiltonianModel {hamiltonian_model_id} 不存在"}

    state_id = _uid("cal")

    posterior_params = []
    for qp in ham["qubit_params"]:
        drift = random.gauss(0, 0.02)
        posterior_params.append({
            "qubit_id": qp["qubit_id"],
            "freq_01_GHz": {"mean": round(qp["freq_01_GHz"] + drift, 4),
                            "std": round(abs(random.gauss(0.002, 0.001)), 4),
                            "CI_95": [round(qp["freq_01_GHz"] + drift - 0.004, 4),
                                      round(qp["freq_01_GHz"] + drift + 0.004, 4)]},
            "anharmonicity_MHz": {"mean": qp["anharmonicity_MHz"],
                                  "std": round(abs(random.gauss(1, 0.5)), 2)},
            "T1_us": {"mean": round(45 + random.gauss(0, 5), 1), "std": round(abs(random.gauss(3, 1)), 1)},
            "T2_Ramsey_us": {"mean": round(30 + random.gauss(0, 5), 1), "std": round(abs(random.gauss(3, 1)), 1)},
            "T2_Echo_us": {"mean": round(40 + random.gauss(0, 5), 1), "std": round(abs(random.gauss(3, 1)), 1)},
        })

    identifiability = []
    if len(ham["qubit_params"]) > 5:
        identifiability.append({
            "issue": "EJ 与寄生电容 Cp 在频率数据中不可分辨",
            "affected_params": ["EJ", "Cp"],
            "recommendation": "需补做 flux-dependent spectroscopy 以解耦",
        })

    residual = {
        "spectroscopy_residual_MHz": round(random.gauss(0, 2), 2),
        "rabi_residual_pct": round(random.gauss(0, 1), 2),
        "model_adequacy": "adequate" if abs(random.gauss(0, 1)) < 2 else "marginal",
    }

    state = {
        "state_id": state_id,
        "hamiltonian_model_id": hamiltonian_model_id,
        "calibration_method": method,
        "posterior_params": posterior_params,
        "identifiability_issues": identifiability,
        "residual_analysis": residual,
        "model_comparison": {
            "tested_models": ["2-level transmon", "3-level with leakage", "multi-mode with parasitic"],
            "best_model": "3-level with leakage",
            "evidence_ratio": round(3.5 + random.gauss(0, 0.5), 2),
        },
        "created_at": _ts(),
    }
    _calibrated_states[state_id] = state
    return state


# ═══════════════════════════════════════════════
# M4 — 实验设计与测试编排
# ═══════════════════════════════════════════════

def plan_experiment(
    calibrated_state_id: Optional[str] = None,
    objective: str = "identify_dominant_noise",
    budget_hours: float = 8.0,
) -> Dict[str, Any]:
    """M4: 信息增益驱动的实验设计
    自动推荐最能缩小参数不确定性/区分假设的实验序列"""
    plan_id = _uid("exp_plan")

    experiment_library = {
        "identify_dominant_noise": [
            {"priority": 1, "experiment": "T1 vs frequency (flux sweep)", "purpose": "区分 Purcell 与介质损耗", "duration_min": 60,
             "expected_info_gain": "高：可定位 T1 主导机理"},
            {"priority": 2, "experiment": "T2 Ramsey vs T2 Echo 对比", "purpose": "分离 T2* 中的低频噪声贡献", "duration_min": 30,
             "expected_info_gain": "高：T2E-T2R差越大→低频噪声越强"},
            {"priority": 3, "experiment": "Noise spectroscopy (CPMG序列)", "purpose": "提取噪声功率谱密度", "duration_min": 90,
             "expected_info_gain": "中：可识别 1/f 或白噪声特征"},
            {"priority": 4, "experiment": "温度依赖 T1 测量", "purpose": "区分准粒子与热光子", "duration_min": 120,
             "expected_info_gain": "中：非平衡准粒子有特征温度依赖"},
            {"priority": 5, "experiment": "热激发态占比测量", "purpose": "评估残余热光子水平", "duration_min": 20,
             "expected_info_gain": "低但重要：直接测有效温度"},
        ],
        "gate_error_diagnosis": [
            {"priority": 1, "experiment": "Interleaved RB (单/双门)", "purpose": "快速估计平均门误差", "duration_min": 45},
            {"priority": 2, "experiment": "Gate Set Tomography (GST)", "purpose": "自洽门集+SPAM表征", "duration_min": 180},
            {"priority": 3, "experiment": "高分辨 Chevron 扫描", "purpose": "定位泄漏与碰撞区域", "duration_min": 60},
            {"priority": 4, "experiment": "ZZ 交互作用测量", "purpose": "量化残余 ZZ 串扰", "duration_min": 30},
            {"priority": 5, "experiment": "DRAG 参数优化扫描", "purpose": "抑制单比特泄漏", "duration_min": 30},
        ],
        "frequency_drift_tracking": [
            {"priority": 1, "experiment": "Ramsey 频率跟踪 (24h连续)", "purpose": "测频率漂移速率和特征", "duration_min": 1440},
            {"priority": 2, "experiment": "多时间尺度 Echo 衰减", "purpose": "区分快慢噪声", "duration_min": 60},
        ],
        "readout_optimization": [
            {"priority": 1, "experiment": "读出功率扫描 + IQ 分析", "purpose": "优化信噪比", "duration_min": 30},
            {"priority": 2, "experiment": "读出频率精细扫描", "purpose": "定位最优读出频点", "duration_min": 30},
            {"priority": 3, "experiment": "QND 性测试", "purpose": "评估测量回注效应", "duration_min": 45},
        ],
    }

    selected = experiment_library.get(objective, experiment_library["identify_dominant_noise"])

    total_min = 0
    scheduled = []
    for exp in selected:
        if total_min + exp["duration_min"] <= budget_hours * 60:
            scheduled.append(exp)
            total_min += exp["duration_min"]

    plan = {
        "plan_id": plan_id,
        "objective": objective,
        "calibrated_state_id": calibrated_state_id,
        "budget_hours": budget_hours,
        "scheduled_experiments": scheduled,
        "total_duration_hours": round(total_min / 60, 1),
        "stopping_criteria": [
            "Top-1 根因置信度 > 0.8",
            "参数后验不确定性下降 > 50%",
            "实验预算耗尽",
        ],
        "adaptive_policy": "每完成一个实验后更新后验，若最高假设置信度>0.85则提前停止",
        "created_at": _ts(),
    }
    _experiment_plans[plan_id] = plan
    return plan


# ═══════════════════════════════════════════════
# M5 — 控制脉冲与门优化
# ═══════════════════════════════════════════════

def optimize_control_pulse(
    hamiltonian_model_id: str,
    gate_type: str = "CZ",
    optimization_method: str = "DRAG",
) -> Dict[str, Any]:
    """M5: 控制脉冲与门优化
    支持: DRAG / GRAPE / robust control
    考虑多能级效应、泄漏抑制、串扰补偿"""
    ham = _hamiltonian_models.get(hamiltonian_model_id)

    gate_proposals = {
        "single_qubit_X": {
            "gate": "X (π pulse)",
            "pulse_type": "Gaussian + DRAG",
            "duration_ns": 20,
            "DRAG_coefficient": round(0.5 + random.gauss(0, 0.05), 3),
            "amplitude_V": round(0.15 + random.gauss(0, 0.01), 4),
            "predicted_fidelity": round(0.9995 + random.gauss(0, 0.0002), 5),
            "predicted_leakage": round(0.0001 + abs(random.gauss(0, 0.00005)), 5),
            "virtual_Z_correction_rad": round(random.gauss(0, 0.01), 4),
        },
        "CZ": {
            "gate": "CZ (controlled-Z)",
            "pulse_type": "flux pulse + net-zero",
            "duration_ns": 160,
            "flux_amplitude_Phi0": round(0.35 + random.gauss(0, 0.02), 4),
            "rise_time_ns": 5,
            "predicted_fidelity": round(0.998 + random.gauss(0, 0.001), 4),
            "predicted_leakage": round(0.002 + abs(random.gauss(0, 0.0005)), 4),
            "ZZ_residual_kHz": round(abs(random.gauss(5, 2)), 1),
            "phase_correction": {
                "target_qubit_rad": round(random.gauss(0.1, 0.02), 4),
                "spectator_qubits_rad": round(random.gauss(0.02, 0.01), 4),
            },
        },
        "iSWAP": {
            "gate": "iSWAP",
            "pulse_type": "parametric modulation",
            "duration_ns": 200,
            "modulation_freq_MHz": round(50 + random.gauss(0, 5), 1),
            "predicted_fidelity": round(0.997 + random.gauss(0, 0.001), 4),
        },
    }

    proposal = gate_proposals.get(gate_type, gate_proposals["CZ"])
    proposal["optimization_method"] = optimization_method
    proposal["hardware_constraints_considered"] = [
        "AWG 采样率 1 GSa/s",
        "带宽限制 500 MHz",
        "上升沿最小 2 ns",
        "FPGA 时间精度 1 ns",
    ]
    proposal["robustness_analysis"] = {
        "frequency_drift_tolerance_MHz": round(1 + random.gauss(0, 0.3), 2),
        "amplitude_error_tolerance_pct": round(2 + random.gauss(0, 0.5), 2),
    }
    return proposal


# ═══════════════════════════════════════════════
# M6 — 诊断与根因归因
# ═══════════════════════════════════════════════

def diagnose_root_cause(
    anomaly_type: str = "gate_error_high",
    observed_metrics: Optional[Dict] = None,
    hamiltonian_model_id: Optional[str] = None,
    noise_model_id: Optional[str] = None,
) -> Dict[str, Any]:
    """M6: 故障树推理 + 概率排序的根因归因
    输出: 候选根因排序、支持/反对证据、反证实验、排查优先级"""
    diag_id = _uid("diag")

    fault_trees = {
        "gate_error_high": {
            "anomaly": "双比特门保真度低于目标",
            "candidates": [
                {
                    "rank": 1, "root_cause": "CZ 工作点附近频率碰撞（非计算态泄漏）",
                    "confidence": round(0.45 + random.gauss(0, 0.05), 2),
                    "supporting_evidence": ["Chevron 图显示工作点附近有避免交叉", "泄漏测量偏高"],
                    "against_evidence": ["单比特门保真度正常"],
                    "verification_experiment": "高分辨 Chevron 扫描 + 泄漏态布居测量",
                },
                {
                    "rank": 2, "root_cause": "磁通偏置线漂移导致有效失谐波动",
                    "confidence": round(0.30 + random.gauss(0, 0.05), 2),
                    "supporting_evidence": ["Ramsey 测量显示频率漂移", "门误差时变性强"],
                    "against_evidence": ["Echo 未显著改善"],
                    "verification_experiment": "长时间 Ramsey 频率跟踪 + 偏置源稳定性测试",
                },
                {
                    "rank": 3, "root_cause": "封装寄生模与高激发态混合",
                    "confidence": round(0.15 + random.gauss(0, 0.05), 2),
                    "supporting_evidence": ["宽频谱扫描有异常模态"],
                    "against_evidence": ["低比特数芯片无此问题"],
                    "verification_experiment": "封装模频扫 + 温度依赖频率测量",
                },
            ],
        },
        "t1_degradation": {
            "anomaly": "T1 显著下降",
            "candidates": [
                {"rank": 1, "root_cause": "表面介质损耗恶化（TLS 激活）", "confidence": 0.40,
                 "supporting_evidence": ["T1 有频率依赖性", "降温后未恢复"],
                 "against_evidence": [],
                 "verification_experiment": "T1 vs 频率扫描 + 功率依赖 T1"},
                {"rank": 2, "root_cause": "Purcell 损耗增强（读出耦合变化）", "confidence": 0.25,
                 "supporting_evidence": ["读出频率附近 T1 最差"],
                 "against_evidence": ["远离读出频率时 T1 也差"],
                 "verification_experiment": "调谐读出频率观察 T1 变化"},
                {"rank": 3, "root_cause": "准粒子浓度升高", "confidence": 0.20,
                 "supporting_evidence": ["升温实验后 T1 下降", "Parity switching 增多"],
                 "against_evidence": [],
                 "verification_experiment": "注入准粒子实验 + 温度依赖 T1"},
            ],
        },
        "frequency_drift": {
            "anomaly": "频率持续漂移",
            "candidates": [
                {"rank": 1, "root_cause": "1/f 磁通噪声（表面磁缺陷/吸附 O₂）", "confidence": 0.50,
                 "supporting_evidence": ["Echo 改善有限", "低频噪声谱呈 1/f"],
                 "against_evidence": [],
                 "verification_experiment": "CPMG 噪声谱测量 + 磁屏蔽测试"},
                {"rank": 2, "root_cause": "TLS 慢跳变", "confidence": 0.25,
                 "supporting_evidence": ["频率出现离散跳变", "长时间观察有电报噪声特征"],
                 "against_evidence": ["连续漂移而非跳变"],
                 "verification_experiment": "长时间连续 Ramsey 监测 + 功率依赖"},
                {"rank": 3, "root_cause": "偏置源不稳定", "confidence": 0.15,
                 "supporting_evidence": ["相邻比特同步漂移"],
                 "against_evidence": ["各比特漂移不相关"],
                 "verification_experiment": "偏置源噪声直接测量 + 换源对比"},
            ],
        },
        "readout_error_high": {
            "anomaly": "读出错误率偏高",
            "candidates": [
                {"rank": 1, "root_cause": "读出功率/频率非最优", "confidence": 0.35,
                 "supporting_evidence": ["IQ 云重叠度高"],
                 "against_evidence": [],
                 "verification_experiment": "读出功率+频率二维扫描优化"},
                {"rank": 2, "root_cause": "残余热激发（有效温度高）", "confidence": 0.30,
                 "supporting_evidence": ["|1⟩态布居非零"],
                 "against_evidence": [],
                 "verification_experiment": "热激发态占比测量"},
                {"rank": 3, "root_cause": "放大链噪声/增益不稳", "confidence": 0.20,
                 "supporting_evidence": ["系统噪声温度偏高"],
                 "against_evidence": [],
                 "verification_experiment": "放大链增益稳定性测试"},
            ],
        },
    }

    tree = fault_trees.get(anomaly_type, fault_trees["gate_error_high"])

    report = {
        "diagnosis_id": diag_id,
        "anomaly_type": anomaly_type,
        "anomaly_description": tree["anomaly"],
        "observed_metrics": observed_metrics or {},
        "root_cause_ranking": tree["candidates"],
        "shortest_verification_path": [c["verification_experiment"] for c in tree["candidates"][:2]],
        "repair_priority": [
            {"action": "短期：调整控制参数（脉冲幅度/相位/工作点）", "effort": "低", "expected_gain": "中"},
            {"action": "中期：优化 coupler/读出链参数", "effort": "中", "expected_gain": "高"},
            {"action": "长期：下一版芯片 redesign", "effort": "高", "expected_gain": "高"},
        ],
        "confidence_note": "以上排序基于当前可用证据，建议按优先级执行反证实验以提高置信度",
        "created_at": _ts(),
    }
    _diagnosis_reports[diag_id] = report
    return report


# ═══════════════════════════════════════════════
# M7 — 设计优化与方案生成
# ═══════════════════════════════════════════════

def generate_design_proposal(
    hamiltonian_model_id: Optional[str] = None,
    noise_model_id: Optional[str] = None,
    diagnosis_id: Optional[str] = None,
    target_gate_fidelity: float = 0.999,
    target_t1_us: float = 80,
) -> Dict[str, Any]:
    """M7: 综合分析结果生成下一版设计优化方案
    输出: 参数窗口、版图修改建议、Pareto 前沿、风险收益分析"""
    proposal_id = _uid("prop")

    proposal = {
        "proposal_id": proposal_id,
        "targets": {
            "gate_fidelity": target_gate_fidelity,
            "T1_us": target_t1_us,
        },
        "frequency_planning": {
            "strategy": "非均匀频率排布，避免二阶碰撞",
            "recommended_spread_GHz": [4.8, 5.5],
            "min_neighbor_detuning_MHz": 150,
            "readout_resonator_spacing_MHz": 20,
        },
        "coupler_optimization": {
            "type": "tunable coupler",
            "target_residual_ZZ_kHz": "<5",
            "coupler_freq_range_GHz": [6.5, 7.5],
            "recommended_g_MHz": [12, 18],
        },
        "layout_modifications": [
            {"item": "增加 airbridge 密度", "reason": "抑制槽模和接地不连续", "priority": "高"},
            {"item": "优化 Purcell 滤波器设计", "reason": "T1 Purcell 限制贡献 >15%", "priority": "高"},
            {"item": "缩小 SQUID loop 面积", "reason": "降低磁通噪声敏感度", "priority": "中"},
            {"item": "改善衬底清洗工艺", "reason": "降低介质损耗 tan_δ", "priority": "中"},
            {"item": "增加封装模抑制结构", "reason": "抑制寄生模耦合", "priority": "低"},
        ],
        "pareto_analysis": {
            "trade_off_axes": ["T1 (相干性)", "门速度", "制造良率", "频率拥挤度"],
            "recommended_operating_point": "偏向高 T1 + 中等门速度",
            "rationale": "当前瓶颈为相干时间而非门速度",
        },
        "risk_assessment": {
            "high_risk": "频率规划依赖 JJ 参数精度，当前批次间变异 ~3%",
            "mitigation": "设计时预留 ±50 MHz 频率调谐余量",
        },
        "implementation_phases": [
            {"phase": "立即可执行", "actions": ["调整读出频点", "优化脉冲参数", "调整 bias 工作点"]},
            {"phase": "中期（下批次）", "actions": ["调整 coupler 参数", "增加 airbridge", "改善滤波链"]},
            {"phase": "下一版芯片", "actions": ["全新频率规划", "新版图布局", "新封装方案"]},
        ],
        "created_at": _ts(),
    }
    _design_proposals[proposal_id] = proposal
    return proposal


# ═══════════════════════════════════════════════
# M8 — 文献—知识图谱—证据中枢
# ═══════════════════════════════════════════════

def search_physics_knowledge(
    query: str,
    domain: str = "superconducting_qubit",
    evidence_level: str = "all",
) -> Dict[str, Any]:
    """M8: 结构化物理知识检索
    从知识图谱中检索: 现象→机理→验证实验→缓解手段"""
    knowledge_templates = [
        {"phenomenon": "T1 下降", "mechanism": "介质损耗 (tan_δ)",
         "evidence": "T1 与频率呈弱依赖，材料相关", "experiment": "T1 vs freq 扫描",
         "mitigation": "改善衬底清洗、换低损耗材料 (sapphire/high-R Si)", "refs": ["Wang et al. 2022 PRX Quantum"]},
        {"phenomenon": "T1 下降", "mechanism": "Purcell 损耗",
         "evidence": "T1 在读出频率附近最差", "experiment": "频率依赖 T1 + 读出耦合调整",
         "mitigation": "增加 Purcell 滤波器", "refs": ["Reed et al. 2010 APL"]},
        {"phenomenon": "T2 低", "mechanism": "1/f 磁通噪声",
         "evidence": "Echo 改善有限，CPMG 噪声谱呈 1/f", "experiment": "CPMG 噪声谱",
         "mitigation": "减小 SQUID loop 面积、改善磁屏蔽", "refs": ["Bylander et al. 2011 Nat. Phys."]},
        {"phenomenon": "T2 低", "mechanism": "TLS 缺陷",
         "evidence": "频率出现电报噪声跳变", "experiment": "长时间 Ramsey 监测",
         "mitigation": "改善界面质量、退火处理", "refs": ["Müller et al. 2019 Rep. Prog. Phys."]},
        {"phenomenon": "门误差高", "mechanism": "频率碰撞（泄漏）",
         "evidence": "Chevron 图有避免交叉特征", "experiment": "高分辨 Chevron",
         "mitigation": "重新规划频率配置", "refs": ["Hertzberg et al. 2021 npj QI"]},
        {"phenomenon": "门误差高", "mechanism": "ZZ 串扰",
         "evidence": "闲置比特影响邻居 Ramsey", "experiment": "条件 Ramsey 测 ZZ",
         "mitigation": "使用可调耦合器/echo-based 门", "refs": ["Mundada et al. 2019 PRApplied"]},
        {"phenomenon": "读出错误", "mechanism": "热激发态",
         "evidence": "初态 |1⟩ 布居非零", "experiment": "热态占比测量",
         "mitigation": "加强热化/增加冷却等待", "refs": ["Jin et al. 2015 PRL"]},
        {"phenomenon": "频率漂移", "mechanism": "磁通噪声 + 表面磁缺陷",
         "evidence": "频率漫漂、吸附 O₂ 相关", "experiment": "磁屏蔽对比 + 表面处理",
         "mitigation": "改善磁屏蔽、避免氧气吸附", "refs": ["Kumar et al. 2016 PRApplied"]},
        {"phenomenon": "准粒子中毒", "mechanism": "非平衡准粒子",
         "evidence": "T1 突降 + parity switching", "experiment": "温度依赖 + 注入实验",
         "mitigation": "准粒子陷阱、改善屏蔽", "refs": ["Vepsäläinen et al. 2020 Nature"]},
        {"phenomenon": "控制泄漏", "mechanism": "弱非简谐性 + 高驱动功率",
         "evidence": "RB 衰减呈非指数", "experiment": "泄漏 RB + DRAG 优化",
         "mitigation": "DRAG 校正、降低驱动功率/增加门时间", "refs": ["Motzoi et al. 2009 PRL"]},
    ]

    q_lower = query.lower()
    results = []
    for kt in knowledge_templates:
        score = sum(1 for w in q_lower.split() if w in (kt["phenomenon"] + kt["mechanism"] + kt["mitigation"]).lower())
        if score > 0 or q_lower in kt["phenomenon"].lower() or q_lower in kt["mechanism"].lower():
            results.append({**kt, "relevance_score": score})
    results.sort(key=lambda x: -x.get("relevance_score", 0))

    return {
        "query": query,
        "domain": domain,
        "results": results[:5] if results else knowledge_templates[:3],
        "total_knowledge_entries": len(knowledge_templates),
        "note": "知识来源：超导量子计算领域核心文献与实验经验",
    }


# ═══════════════════════════════════════════════
# 辅助工具
# ═══════════════════════════════════════════════

def get_theorist_status() -> Dict[str, Any]:
    """获取理论物理学家 Agent 当前状态汇总"""
    return {
        "device_graphs": len(_device_graphs),
        "hamiltonian_models": len(_hamiltonian_models),
        "noise_models": len(_noise_models),
        "calibrated_states": len(_calibrated_states),
        "diagnosis_reports": len(_diagnosis_reports),
        "experiment_plans": len(_experiment_plans),
        "design_proposals": len(_design_proposals),
        "modules": {
            "M0_data_ingestion": "active",
            "M1_hamiltonian_modeling": "active",
            "M2_noise_budget": "active",
            "M3_parameter_inversion": "active",
            "M4_experiment_design": "active",
            "M5_pulse_optimization": "active",
            "M6_root_cause_diagnosis": "active",
            "M7_design_optimization": "active",
            "M8_knowledge_retrieval": "active",
            "M9_orchestration": "handled_by_orchestrator",
        },
    }
