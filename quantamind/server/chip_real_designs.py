"""
真实芯片设计资料索引
来源：E:\\work\\Quantumchipdesin
包含：单比特 V2.00、双比特可调耦合 V2.00、20比特 CT20Q V2/V3、105比特 FT105Q V2
"""

REAL_DESIGNS_ROOT = r"E:\work\Quantumchipdesin"

# ── 单比特 1bitV2.00 ──
CHIP_1BIT = {
    "name": "单比特芯片 V2.00",
    "doc_id": "1bitV2.00",
    "version": "V2.00",
    "chip_size_mm": [10, 10],
    "total_qubits": 5,
    "total_resonators": 4,
    "topology": "standalone_qubits",
    "substrate": "sapphire",
    "qubit_type": "Xmon",
    "qubits": [
        {"id": "Q1", "freq_ghz": 4.5, "res_design_ghz": 7.22, "res_sim_ghz": 7.21978, "res_qe": 12325.7, "C_qubit_fF": 71.90373, "C_coupling_fF": 2.76993, "L_nH": 15.49},
        {"id": "Q2", "freq_ghz": 4.5, "res_design_ghz": 7.255, "res_sim_ghz": 7.25505, "res_qe": 12224.5, "C_qubit_fF": 71.90373, "C_coupling_fF": 2.76993, "L_nH": 15.49},
        {"id": "Q3", "freq_ghz": 4.5, "res_design_ghz": 7.285, "res_sim_ghz": 7.28524, "res_qe": 12126.6, "C_qubit_fF": 71.90373, "C_coupling_fF": 2.76993, "L_nH": 15.49},
        {"id": "Q4", "freq_ghz": 4.5, "res_design_ghz": 7.32, "res_sim_ghz": 7.32277, "res_qe": 15480.6, "C_qubit_fF": 71.90373, "C_coupling_fF": 2.76993, "L_nH": 15.49},
        {"id": "Q5", "freq_ghz": 4.5, "res_design_ghz": 7.35, "res_sim_ghz": 7.35295, "res_qe": 15407.5, "C_qubit_fF": 71.90373, "C_coupling_fF": 2.76993, "L_nH": 15.49},
    ],
    "q3d_capacitance_matrix": {
        "components": ["resonator", "ground", "Pad2", "Pad1", "readout"],
        "matrix_fF": [
            [653.01, -640.64, -0.65, -6.19, -4.13],
            [-640.64, 1037.19, -79.77, -80.36, -148.50],
            [-0.65, -79.77, 116.13, -31.72, -0.08],
            [-6.19, -80.36, -31.72, 121.67, -0.12],
            [-4.13, -148.50, -0.08, -0.12, 153.93],
        ],
    },
    "files": {
        "gds": r"E:\work\Quantumchipdesin\单比特\1bitV2.00\1bitV2.00.gds",
        "q3d_data": r"E:\work\Quantumchipdesin\单比特\1bitV2.00\1bitV2.00_Q1__Q3D.xlsx",
        "params_xlsx": r"E:\work\Quantumchipdesin\单比特\1bitV2.00\1bitV2.00_参数汇总.xlsx",
        "design_doc": r"E:\work\Quantumchipdesin\单比特\1bitV2.00\1bitV2.00_工艺文档.docx",
        "summary_ppt": r"E:\work\Quantumchipdesin\单比特\1bitV2.00\1bitV2.00_数据汇总.pptx",
    },
}

# ── 双比特可调耦合 2bits_coupler_V2_00 ──
CHIP_2BIT = {
    "name": "双比特可调耦合器芯片 V2.00",
    "doc_id": "2bits_coupler_V2_00",
    "version": "V2.00",
    "chip_size_mm": [10, 10],
    "total_qubits": 4,
    "total_couplers": 2,
    "total_resonators": 9,
    "topology": "dual_pair_with_tunable_coupler",
    "substrate": "sapphire",
    "qubit_type": "Xmon",
    "design_goals": [
        "实现高保真度CZ门",
        "测试大失谐下的ZZ耦合开关比",
        "测试可调耦合器的关断状态",
    ],
    "qubits": [
        {"id": "Q1", "freq_ghz": 4.69, "res_design_ghz": 7.4, "res_sim_ghz": 7.39477, "res_qe": 15209.4, "res_len_um": 4035.31, "C_qubit_fF": 71.39, "C_coupling_fF": 4.22, "L_nH": 14.38, "xy_cap_aF": 77},
        {"id": "Q2", "freq_ghz": 5.204, "res_design_ghz": 7.6, "res_sim_ghz": 7.59606, "res_qe": 14876.6, "res_len_um": 3918.53, "C_qubit_fF": 71.40, "C_coupling_fF": 3.90, "L_nH": 11.78, "xy_cap_aF": 77},
        {"id": "T1", "freq_ghz": 7.123, "type": "tunable_coupler", "res_design_ghz": 7.8, "res_sim_ghz": 7.80148, "res_qe": 13402, "C_qubit_fF": 61.24, "C_coupling_fF": 1.53, "L_nH": 7.5, "xy_cap_aF": 123, "z_mutual_pH": 2},
        {"id": "Q3", "freq_ghz": 4.684, "res_design_ghz": 6.8, "res_sim_ghz": 6.79963, "res_qe": 20275.4, "res_len_um": 4419.09, "C_qubit_fF": 71.39, "C_coupling_fF": 4.22, "L_nH": 14.38, "xy_cap_aF": 77},
        {"id": "Q4", "freq_ghz": 5.204, "res_design_ghz": 7.0, "res_sim_ghz": 6.99833, "res_qe": 17207.2, "res_len_um": 4285.59, "C_qubit_fF": 71.40, "C_coupling_fF": 3.90, "L_nH": 11.78, "xy_cap_aF": 77},
        {"id": "T2", "freq_ghz": 7.123, "type": "tunable_coupler", "res_design_ghz": 7.5, "res_sim_ghz": 7.50523, "res_qe": 17000.7, "C_qubit_fF": 61.24, "C_coupling_fF": 1.53, "L_nH": 7.5, "xy_cap_aF": 123, "z_mutual_pH": 2},
    ],
    "layout_code": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\layout_2bits_coupler_V2_00.py",
    "files": {
        "gds": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\output\2bits_coupler_V2_00.gds",
        "json_params": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\output\2bits_coupler_V2_00.json",
        "params_xlsx": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\2bits_coupler_V2_00_参数汇总.xlsx",
        "design_doc": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\output\参考：可调耦合器双比特设计文档 V2.docx",
        "process_doc": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\双比特可调耦合V2.00工艺文档 .docx",
        "layout_code": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\layout_2bits_coupler_V2_00.py",
        "notebook": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\2bits_coupler_V2_00.ipynb",
        "q3d_csv": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\output\2bits_coupler_V2_00_Eigen_Test03_Redo_Q1_C12_Q2_q3d.csv",
        "resonator_fitting": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\output\2bits_coupler_V2_00-谐振腔长度拟合.ipynb",
        "sim_data_processing": r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\output\2bits_couplerV2_00_仿真数据计算处理.ipynb",
    },
}

# ── 20 比特 CT20Q ──
CHIP_CT20Q = {
    "name": "20 比特可调耦合器芯片 CT20Q",
    "doc_id": "CT20Q",
    "versions": ["V2.01 (2026-01-30)", "V3.00 (2026-02-10)"],
    "chip_size_mm": [12.5, 12.5],
    "total_qubits": 20,
    "total_couplers": 19,
    "total_pads": 48,
    "topology": "1D_chain_tunable_coupler",
    "substrate": "sapphire",
    "qubit_type": "Xmon",
    "cpw": {"s_um": 10, "w_um": 5, "Z0_ohm": 50},
    "Qodd_freq_ghz": 5.152,
    "Qeven_freq_ghz": 4.650,
    "coupler_freq_ghz": 6.844,
    "files": {
        "gds_v2": r"E:\work\Quantumchipdesin\CT20Q\CT20QV2_01_12.5mm_20260130.zip",
        "gds_v3": r"E:\work\Quantumchipdesin\CT20Q\CT20QV3_00_12.5mm_20260210.zip",
        "design_doc": r"E:\work\QuantaMind\docs\QEDA\20比特可调耦合器双比特设计方案.docx",
    },
}

# ── 105 比特 FT105Q ──
CHIP_105BIT = {
    "name": "105 比特可调耦合器芯片 FT105Q V2",
    "doc_id": "FT105QV2",
    "version": "V2.00 (2026-03-17)",
    "total_qubits": 105,
    "topology": "2D_grid_tunable_coupler",
    "gds_stats": {"cells": 18, "layers": 10, "shapes": 95238},
    "files": {
        "gds": r"E:\work\Quantumchipdesin\105比特\FT105QV2_00_20260317.gds",
        "design_doc": r"E:\work\QuantaMind\docs\QEDA\105比特可调耦合器量子芯片设计方案0120.docx",
    },
}

# ── 封装测试片 ──
CHIP_TEST = {
    "name": "倒装焊测试片",
    "doc_id": "test_InR_V7",
    "files": {
        "oas": r"E:\work\Quantumchipdesin\倒装焊测试片\test_InR_V7.oas",
    },
}

ALL_REAL_DESIGNS = {
    "1bit": CHIP_1BIT,
    "2bit": CHIP_2BIT,
    "20bit_ct20q": CHIP_CT20Q,
    "105bit": CHIP_105BIT,
    "test_chip": CHIP_TEST,
}
