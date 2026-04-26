# 105比特可调耦合器量子芯片规格（自动从设计文档提取）

CHIP_105BIT_SPEC = {
  "doc_id": "GJQ-200-000-FA09-2025",
  "name": "105比特可调耦合器超导量子芯片",
  "total_qubits": 105,
  "total_couplers": 1,
  "topology": "二维网格结构（2D grid）",
  "qubit_type": "Xmon（固定频率）",
  "coupler_type": "可调耦合器（Transmon + SQUID）",
  "targets": {
    "qubit_count": 105,
    "coupler_count": "≥180",
    "single_gate_fidelity": "99%（≥70比特）",
    "two_gate_fidelity": "99%（≥70比特）",
    "readout_fidelity": "95%（≥70比特）",
    "T1_avg_us": "≥50",
    "T2_avg_us": "≥30",
    "freq_error": "≤3%",
    "resonator_freq_error": "≤3%",
    "film": "钽膜 Tc≥1.2K"
  },
  "qubits": [
    {
      "id": "Q001",
      "bit_id": "B01-01",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.0,
      "res_q": "21653.6",
      "target_freq_ghz": 7.0,
      "sim_freq_ghz": 7.0007,
      "q_value": 21653.6,
      "total_length_um": 4900.01
    },
    {
      "id": "Q002",
      "bit_id": "B01-02",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.48,
      "res_q": "19878.3",
      "target_freq_ghz": 7.48,
      "sim_freq_ghz": 7.48125,
      "q_value": 19878.3,
      "total_length_um": 4573.28
    },
    {
      "id": "Q003",
      "bit_id": "B01-03",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.04,
      "res_q": "23221.5",
      "target_freq_ghz": 7.04,
      "sim_freq_ghz": 7.03967,
      "q_value": 23221.5,
      "total_length_um": 4871.13
    },
    {
      "id": "Q004",
      "bit_id": "B01-04",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.44,
      "res_q": "19472.4",
      "target_freq_ghz": 7.44,
      "sim_freq_ghz": 7.4406,
      "q_value": 19472.4,
      "total_length_um": 4598.85
    },
    {
      "id": "Q005",
      "bit_id": "B01-05",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.08,
      "res_q": "21576.7",
      "target_freq_ghz": 7.08,
      "sim_freq_ghz": 7.07703,
      "q_value": 21576.7,
      "total_length_um": 4842.55
    },
    {
      "id": "Q006",
      "bit_id": "B01-06",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21304.8",
      "target_freq_ghz": 7.4,
      "sim_freq_ghz": 7.40028,
      "q_value": 21304.8,
      "total_length_um": 4624.73
    },
    {
      "id": "Q007",
      "bit_id": "B01-07",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.12,
      "res_q": "21865.3",
      "target_freq_ghz": 7.12,
      "sim_freq_ghz": 7.11891,
      "q_value": 21865.3,
      "total_length_um": 4814.27
    },
    {
      "id": "Q008",
      "bit_id": "B02-01",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.42,
      "res_q": "21653.6"
    },
    {
      "id": "Q009",
      "bit_id": "B02-02",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.1,
      "res_q": "19878.3"
    },
    {
      "id": "Q010",
      "bit_id": "B02-03",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.46,
      "res_q": "23221.5"
    },
    {
      "id": "Q011",
      "bit_id": "B02-04",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.06,
      "res_q": "19472.4"
    },
    {
      "id": "Q012",
      "bit_id": "B02-05",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21576.7"
    },
    {
      "id": "Q013",
      "bit_id": "B02-06",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.02,
      "res_q": "21304.8"
    },
    {
      "id": "Q014",
      "bit_id": "B02-07",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.54,
      "res_q": "21865.3"
    },
    {
      "id": "Q015",
      "bit_id": "B03-01",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.0,
      "res_q": "21653.6"
    },
    {
      "id": "Q016",
      "bit_id": "B03-02",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.48,
      "res_q": "19878.3"
    },
    {
      "id": "Q017",
      "bit_id": "B03-03",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.04,
      "res_q": "23221.5"
    },
    {
      "id": "Q018",
      "bit_id": "B03-04",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.44,
      "res_q": "19472.4"
    },
    {
      "id": "Q019",
      "bit_id": "B03-05",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.08,
      "res_q": "21576.7"
    },
    {
      "id": "Q020",
      "bit_id": "B03-06",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21304.8"
    },
    {
      "id": "Q021",
      "bit_id": "B03-07",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.12,
      "res_q": "21865.3"
    },
    {
      "id": "Q022",
      "bit_id": "B04-01",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.42,
      "res_q": "21653.6"
    },
    {
      "id": "Q023",
      "bit_id": "B04-02",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.1,
      "res_q": "19878.3"
    },
    {
      "id": "Q024",
      "bit_id": "B04-03",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.46,
      "res_q": "23221.5"
    },
    {
      "id": "Q025",
      "bit_id": "B04-04",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.06,
      "res_q": "19472.4"
    },
    {
      "id": "Q026",
      "bit_id": "B04-05",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21576.7"
    },
    {
      "id": "Q027",
      "bit_id": "B04-06",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.02,
      "res_q": "21304.8"
    },
    {
      "id": "Q028",
      "bit_id": "B04-07",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.54,
      "res_q": "21865.3"
    },
    {
      "id": "Q029",
      "bit_id": "B05-01",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.0,
      "res_q": "21653.6"
    },
    {
      "id": "Q030",
      "bit_id": "B05-02",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.48,
      "res_q": "19878.3"
    },
    {
      "id": "Q031",
      "bit_id": "B05-03",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.04,
      "res_q": "23221.5"
    },
    {
      "id": "Q032",
      "bit_id": "B05-04",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.44,
      "res_q": "19472.4"
    },
    {
      "id": "Q033",
      "bit_id": "B05-05",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.08,
      "res_q": "21576.7"
    },
    {
      "id": "Q034",
      "bit_id": "B05-06",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21304.8"
    },
    {
      "id": "Q035",
      "bit_id": "B05-07",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.12,
      "res_q": "21865.3"
    },
    {
      "id": "Q036",
      "bit_id": "B06-01",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.42,
      "res_q": "21653.6"
    },
    {
      "id": "Q037",
      "bit_id": "B06-02",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.1,
      "res_q": "19878.3"
    },
    {
      "id": "Q038",
      "bit_id": "B06-03",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.46,
      "res_q": "23221.5"
    },
    {
      "id": "Q039",
      "bit_id": "B06-04",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.06,
      "res_q": "19472.4"
    },
    {
      "id": "Q040",
      "bit_id": "B06-05",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21576.7"
    },
    {
      "id": "Q041",
      "bit_id": "B06-06",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.02,
      "res_q": "21304.8"
    },
    {
      "id": "Q042",
      "bit_id": "B06-07",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.54,
      "res_q": "21865.3"
    },
    {
      "id": "Q043",
      "bit_id": "B07-01",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.0,
      "res_q": "21653.6"
    },
    {
      "id": "Q044",
      "bit_id": "B07-02",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.48,
      "res_q": "19878.3"
    },
    {
      "id": "Q045",
      "bit_id": "B07-03",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.04,
      "res_q": "23221.5"
    },
    {
      "id": "Q046",
      "bit_id": "B07-04",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.44,
      "res_q": "19472.4"
    },
    {
      "id": "Q047",
      "bit_id": "B07-05",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.08,
      "res_q": "21576.7"
    },
    {
      "id": "Q048",
      "bit_id": "B07-06",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21304.8"
    },
    {
      "id": "Q049",
      "bit_id": "B07-07",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.12,
      "res_q": "21865.3"
    },
    {
      "id": "Q050",
      "bit_id": "B08-01",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.42,
      "res_q": "21653.6"
    },
    {
      "id": "Q051",
      "bit_id": "B08-02",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.1,
      "res_q": "19878.3"
    },
    {
      "id": "Q052",
      "bit_id": "B08-03",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.46,
      "res_q": "23221.5"
    },
    {
      "id": "Q053",
      "bit_id": "B08-04",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.06,
      "res_q": "19472.4"
    },
    {
      "id": "Q054",
      "bit_id": "B08-05",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21576.7"
    },
    {
      "id": "Q055",
      "bit_id": "B08-06",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.02,
      "res_q": "21304.8"
    },
    {
      "id": "Q056",
      "bit_id": "B08-07",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.54,
      "res_q": "21865.3"
    },
    {
      "id": "Q057",
      "bit_id": "B09-01",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.0,
      "res_q": "21653.6"
    },
    {
      "id": "Q058",
      "bit_id": "B09-02",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.48,
      "res_q": "19878.3"
    },
    {
      "id": "Q059",
      "bit_id": "B09-03",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.04,
      "res_q": "23221.5"
    },
    {
      "id": "Q060",
      "bit_id": "B09-04",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.44,
      "res_q": "19472.4"
    },
    {
      "id": "Q061",
      "bit_id": "B09-05",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.08,
      "res_q": "21576.7"
    },
    {
      "id": "Q062",
      "bit_id": "B09-06",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21304.8"
    },
    {
      "id": "Q063",
      "bit_id": "B09-07",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.12,
      "res_q": "21865.3"
    },
    {
      "id": "Q064",
      "bit_id": "B10-01",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.42,
      "res_q": "21653.6"
    },
    {
      "id": "Q065",
      "bit_id": "B10-02",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.1,
      "res_q": "19878.3"
    },
    {
      "id": "Q066",
      "bit_id": "B10-03",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.46,
      "res_q": "23221.5"
    },
    {
      "id": "Q067",
      "bit_id": "B10-04",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.06,
      "res_q": "19472.4"
    },
    {
      "id": "Q068",
      "bit_id": "B10-05",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21576.7"
    },
    {
      "id": "Q069",
      "bit_id": "B10-06",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.02,
      "res_q": "21304.8"
    },
    {
      "id": "Q070",
      "bit_id": "B10-07",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.54,
      "res_q": "21865.3"
    },
    {
      "id": "Q071",
      "bit_id": "B11-01",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.0,
      "res_q": "21653.6"
    },
    {
      "id": "Q072",
      "bit_id": "B11-02",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.48,
      "res_q": "19878.3"
    },
    {
      "id": "Q073",
      "bit_id": "B11-03",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.04,
      "res_q": "23221.5"
    },
    {
      "id": "Q074",
      "bit_id": "B11-04",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.44,
      "res_q": "19472.4"
    },
    {
      "id": "Q075",
      "bit_id": "B11-05",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.08,
      "res_q": "21576.7"
    },
    {
      "id": "Q076",
      "bit_id": "B11-06",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21304.8"
    },
    {
      "id": "Q077",
      "bit_id": "B11-07",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.12,
      "res_q": "21865.3"
    },
    {
      "id": "Q078",
      "bit_id": "B12-01",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.42,
      "res_q": "21653.6"
    },
    {
      "id": "Q079",
      "bit_id": "B12-02",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.1,
      "res_q": "19878.3"
    },
    {
      "id": "Q080",
      "bit_id": "B12-03",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.46,
      "res_q": "23221.5"
    },
    {
      "id": "Q081",
      "bit_id": "B12-04",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.06,
      "res_q": "19472.4"
    },
    {
      "id": "Q082",
      "bit_id": "B12-05",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21576.7"
    },
    {
      "id": "Q083",
      "bit_id": "B12-06",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.02,
      "res_q": "21304.8"
    },
    {
      "id": "Q084",
      "bit_id": "B12-07",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.54,
      "res_q": "21865.3"
    },
    {
      "id": "Q085",
      "bit_id": "B13-01",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.0,
      "res_q": "21653.6"
    },
    {
      "id": "Q086",
      "bit_id": "B13-02",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.48,
      "res_q": "19878.3"
    },
    {
      "id": "Q087",
      "bit_id": "B13-03",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.04,
      "res_q": "23221.5"
    },
    {
      "id": "Q088",
      "bit_id": "B13-04",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.44,
      "res_q": "19472.4"
    },
    {
      "id": "Q089",
      "bit_id": "B13-05",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.08,
      "res_q": "21576.7"
    },
    {
      "id": "Q090",
      "bit_id": "B13-06",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21304.8"
    },
    {
      "id": "Q091",
      "bit_id": "B13-07",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.12,
      "res_q": "21865.3"
    },
    {
      "id": "Q092",
      "bit_id": "B14-01",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.42,
      "res_q": "21653.6"
    },
    {
      "id": "Q093",
      "bit_id": "B14-02",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.1,
      "res_q": "19878.3"
    },
    {
      "id": "Q094",
      "bit_id": "B14-03",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.46,
      "res_q": "23221.5"
    },
    {
      "id": "Q095",
      "bit_id": "B14-04",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.06,
      "res_q": "19472.4"
    },
    {
      "id": "Q096",
      "bit_id": "B14-05",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21576.7"
    },
    {
      "id": "Q097",
      "bit_id": "B14-06",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.02,
      "res_q": "21304.8"
    },
    {
      "id": "Q098",
      "bit_id": "B14-07",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.54,
      "res_q": "21865.3"
    },
    {
      "id": "Q099",
      "bit_id": "B15-01",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.0,
      "res_q": "21653.6"
    },
    {
      "id": "Q100",
      "bit_id": "B15-02",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.48,
      "res_q": "19878.3"
    },
    {
      "id": "Q101",
      "bit_id": "B15-03",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.04,
      "res_q": "23221.5"
    },
    {
      "id": "Q102",
      "bit_id": "B15-04",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.44,
      "res_q": "19472.4"
    },
    {
      "id": "Q103",
      "bit_id": "B15-05",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.08,
      "res_q": "21576.7"
    },
    {
      "id": "Q104",
      "bit_id": "B15-06",
      "freq_ghz": 4.8,
      "res_freq_ghz": 7.4,
      "res_q": "21304.8"
    },
    {
      "id": "Q105",
      "bit_id": "B15-07",
      "freq_ghz": 4.396,
      "res_freq_ghz": 7.12,
      "res_q": "21865.3"
    }
  ],
  "couplers": [
    {
      "id": "耦合器",
      "freq_ghz": 6.66
    }
  ]
}
