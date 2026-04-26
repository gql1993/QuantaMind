# 20比特可调耦合器量子芯片完整规格（来自设计文档 TGQ-200-000-FA09-2025 + 图纸）

CHIP_SPEC = {
    "doc_id": "TGQ-200-000-FA09-2025",
    "name": "20比特可调耦合器超导量子芯片",
    "design_team": "量子科技长三角产业创新中心 · 杨斌、刘浩宇、张国荣、郭伟贵",
    "chip_size_mm": [12.5, 12.5],
    "substrate": "蓝宝石（Sapphire）",
    "metal_film": "铝膜或钽膜，厚度 180±2 nm",
    "topology": "一维链结构（1D chain）",
    "qubit_type": "Xmon（固定频率）",
    "coupler_type": "可调耦合器（Transmon + SQUID）",
    "total_qubits": 20,
    "total_couplers": 19,
    "total_pads": 48,
    "active_pads": 47,

    # 工艺规格（来自图纸）
    "fabrication": {
        "lithography": "激光直写，精度 ±0.3 μm",
        "jj_fabrication": "双倾角蒸镀（Dolan Bridge），精度 ±2 nm",
        "jj_structure": "铝-氧化铝-铝三明治结构",
        "jj_length_nm": "200±10",
        "jj_width_nm": "200±10",
        "oxide_thickness_nm": "2±0.2",
        "film_thickness_nm": "180±2",
        "substrate_thickness_um": "430±25",
    },

    # CPW（共面波导）规格
    "cpw": {
        "sapphire": {"center_width_um": 10, "gap_um": 5, "Z0_ohm": "48.65~51.34"},
        "silicon": {"center_width_um": 10, "gap_um": 6.5, "Z0_ohm": "48.99~51.08"},
        "control_line": {"center_width_um": "10±0.3", "gap_um": "5±0.3"},
        "resonator": {"center_width_um": "8±0.3", "gap_um": "4±0.3"},
        "line_spacing_um": 100,
        "line_to_qubit_spacing_um": 100,
    },

    # 设计目标
    "targets": {
        "single_gate_fidelity": "≥99.9%",
        "two_gate_fidelity": "≥99%",
        "readout_fidelity": "≥99%",
        "T1_us": "≥20",
        "T2_us": "≥15",
        "survival_rate": "100%",
        "qubit_availability": "≥90%",
        "entangled_ratio": "≥85%",
    },

    # 全部 20 个比特参数（来自表 4-1）
    "qubits": [
        {"id": "Q1",  "freq_ghz": 4.65, "res_design_ghz": 7.30, "res_sim_ghz": 7.15131, "res_length_mm": 3.572331, "coupling_mhz": 88.33, "Ec_mhz": -230.13, "Lj_nH": 12.5, "mutual_pH": 2},
        {"id": "Q2",  "freq_ghz": 4.56, "res_design_ghz": 7.00, "res_sim_ghz": 6.85162, "res_length_mm": 3.730524, "coupling_mhz": 87.42, "Ec_mhz": -230.13, "Lj_nH": 13.0, "mutual_pH": 2},
        {"id": "Q3",  "freq_ghz": 4.65, "res_design_ghz": 7.36, "res_sim_ghz": 7.21115, "res_length_mm": 3.53617,  "coupling_mhz": 88.33, "Ec_mhz": -230.13, "Lj_nH": 12.5, "mutual_pH": 2},
        {"id": "Q4",  "freq_ghz": 4.56, "res_design_ghz": 7.06, "res_sim_ghz": 6.91338, "res_length_mm": 3.691244, "coupling_mhz": 87.42, "Ec_mhz": -230.13, "Lj_nH": 13.0, "mutual_pH": 2},
        {"id": "Q5",  "freq_ghz": 4.65, "res_design_ghz": 7.42, "res_sim_ghz": 7.27139, "res_length_mm": 3.500734, "coupling_mhz": 88.33, "Ec_mhz": -230.13, "Lj_nH": 12.5, "mutual_pH": 2},
        {"id": "Q6",  "freq_ghz": 4.56, "res_design_ghz": 7.12, "res_sim_ghz": 6.97039, "res_length_mm": 3.450609, "coupling_mhz": 87.42, "Ec_mhz": -230.13, "Lj_nH": 13.0, "mutual_pH": 2},
        {"id": "Q7",  "freq_ghz": 4.65, "res_design_ghz": 7.48, "res_sim_ghz": 7.28691, "res_length_mm": 3.288174, "coupling_mhz": 88.33, "Ec_mhz": -230.13, "Lj_nH": 12.5, "mutual_pH": 2},
        {"id": "Q8",  "freq_ghz": 4.56, "res_design_ghz": 7.18, "res_sim_ghz": 7.32849, "res_length_mm": 3.232771, "coupling_mhz": 87.42, "Ec_mhz": -230.13, "Lj_nH": 13.0, "mutual_pH": 2},
        {"id": "Q9",  "freq_ghz": 4.65, "res_design_ghz": 7.54, "res_sim_ghz": 7.38531, "res_length_mm": 3.229892, "coupling_mhz": 88.33, "Ec_mhz": -230.13, "Lj_nH": 12.5, "mutual_pH": 2},
        {"id": "Q10", "freq_ghz": 4.56, "res_design_ghz": 7.24, "res_sim_ghz": 7.08708, "res_length_mm": 3.376923, "coupling_mhz": 87.42, "Ec_mhz": -230.13, "Lj_nH": 13.0, "mutual_pH": 2},
        {"id": "Q11", "freq_ghz": 4.65, "res_design_ghz": 7.33, "res_sim_ghz": 7.18179, "res_length_mm": 3.554157, "coupling_mhz": 88.33, "Ec_mhz": -230.13, "Lj_nH": 12.5, "mutual_pH": 2},
        {"id": "Q12", "freq_ghz": 4.56, "res_design_ghz": 7.03, "res_sim_ghz": 6.8819,  "res_length_mm": 3.710779, "coupling_mhz": 87.42, "Ec_mhz": -230.13, "Lj_nH": 13.0, "mutual_pH": 2},
        {"id": "Q13", "freq_ghz": 4.65, "res_design_ghz": 7.39, "res_sim_ghz": 7.24184, "res_length_mm": 3.518364, "coupling_mhz": 88.33, "Ec_mhz": -230.13, "Lj_nH": 12.5, "mutual_pH": 2},
        {"id": "Q14", "freq_ghz": 4.56, "res_design_ghz": 7.09, "res_sim_ghz": 6.94249, "res_length_mm": 3.671911, "coupling_mhz": 87.42, "Ec_mhz": -230.13, "Lj_nH": 13.0, "mutual_pH": 2},
        {"id": "Q15", "freq_ghz": 4.65, "res_design_ghz": 7.45, "res_sim_ghz": 7.30305, "res_length_mm": 3.483276, "coupling_mhz": 88.33, "Ec_mhz": -230.13, "Lj_nH": 12.5, "mutual_pH": 2},
        {"id": "Q16", "freq_ghz": 4.56, "res_design_ghz": 7.15, "res_sim_ghz": 6.99857, "res_length_mm": 3.633831, "coupling_mhz": 87.42, "Ec_mhz": -230.13, "Lj_nH": 13.0, "mutual_pH": 2},
        {"id": "Q17", "freq_ghz": 4.65, "res_design_ghz": 7.51, "res_sim_ghz": 7.36114, "res_length_mm": 3.448853, "coupling_mhz": 88.33, "Ec_mhz": -230.13, "Lj_nH": 12.5, "mutual_pH": 2},
        {"id": "Q18", "freq_ghz": 4.56, "res_design_ghz": 7.21, "res_sim_ghz": 7.06062, "res_length_mm": 3.596494, "coupling_mhz": 87.42, "Ec_mhz": -230.13, "Lj_nH": 13.0, "mutual_pH": 2},
        {"id": "Q19", "freq_ghz": 4.65, "res_design_ghz": 7.88, "res_sim_ghz": 7.72804, "res_length_mm": 3.249305, "coupling_mhz": 88.33, "Ec_mhz": -230.13, "Lj_nH": 12.5, "mutual_pH": 2},
        {"id": "Q20", "freq_ghz": 4.56, "res_design_ghz": 7.58, "res_sim_ghz": 7.42677, "res_length_mm": 3.380394, "coupling_mhz": 87.42, "Ec_mhz": -230.13, "Lj_nH": 13.0, "mutual_pH": 2},
    ],

    # 全部 19 个可调耦合器
    "couplers": [
        {"id": f"T{i}", "freq_ghz": 6.88, "Ec_mhz": -352.87, "Lj_nH": 8.8, "mutual_pH": 2,
         "structure": "Transmon + SQUID", "connects": [f"Q{i}", f"Q{i+1}"]}
        for i in range(1, 20)
    ],

    # Q3D 仿真电容矩阵（来自表 4-2，单位 fF）
    "capacitance_matrix_fF": {
        "components": ["bus_02(比特-腔耦合)", "coupler(可调耦合器)", "cross_xmon(量子比特)", "bus_01(Z线-耦合器)"],
        "matrix": [
            [62.66, -9.786, -18.50, -0.7224],
            [-9.786, 79.44, -11.81, -21.07],
            [-18.50, -11.81, 87.71, -0.6764],
            [-0.7224, -21.07, -0.6764, 62.48],
        ],
    },

    # 封装规格
    "packaging": {
        "interface": "48 pin SMP",
        "box_material": "无氧铜",
        "xy_lines": 20,
        "z_coupler_lines": 5,
        "z_control_lines": 5,
        "readout_lines": 4,
        "resonators": 20,
        "airbridges": 20,
        "junctions": 20,
    },

    # 版图组件清单（来自图纸）
    "layout_components": [
        {"name": "量子比特", "count": 20, "drawing_id": "TG5.440.0001WX-QB"},
        {"name": "读取谐振腔", "count": 20, "drawing_id": "TG5.440.0001WX-Re"},
        {"name": "XYZ控制线", "count": 20, "drawing_id": "TG5.440.0001WX-XY"},
        {"name": "Z控制线", "count": 19, "drawing_id": "TG5.440.0001WX-Z"},
        {"name": "读取线", "count": 4, "drawing_id": "TG5.440.0001WX-RL"},
        {"name": "空气桥", "count": 20, "drawing_id": "TG5.440.0001WX-AB"},
        {"name": "约瑟夫森结", "count": 20, "drawing_id": "TG5.440.0001WX-JJ"},
        {"name": "可调耦合器", "count": 19, "drawing_id": "TG5.440.0001WX-TC"},
    ],
}
