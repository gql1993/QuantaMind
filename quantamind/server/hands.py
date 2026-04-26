# QuantumHands — 工具执行层（六大平台 API 占位 + 通用工具）

from typing import Any, Callable, Dict, List, Optional

# 工具注册表：name -> (description, callable)
TOOL_REGISTRY: Dict[str, tuple] = {}


def register_tool(name: str, description: str, func: Callable[..., Any]) -> None:
    TOOL_REGISTRY[name] = (description, func)


def list_tools() -> List[Dict[str, str]]:
    return [{"name": k, "description": v[0]} for k, v in TOOL_REGISTRY.items()]


async def run_tool(tool_name: str, **kwargs: Any) -> Any:
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool: {tool_name}"}
    _, func = TOOL_REGISTRY[tool_name]
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return await func(**kwargs)
    return await asyncio.to_thread(func, **kwargs)


# ——— 内置通用工具（Phase 1） ———
def _tool_echo(text: str) -> Dict[str, str]:
    return {"result": text}


def _tool_search_knowledge(query: str) -> Dict[str, Any]:
    """从设计文档知识库中检索相关内容"""
    from quantamind.server import knowledge_base as kb
    results = kb.search(query, max_results=5)
    return {"query": query, "results": results, "count": len(results)}


register_tool("echo", "Echo back the input text.", _tool_echo)
register_tool("search_knowledge", "Search QuantaMind knowledge base.", _tool_search_knowledge)


# ——— Qiskit Metal 工具（Q-EDA 设计 + 分析） ———
from quantamind.server import hands_qiskit_metal as _metal

register_tool("metal_create_design", "Qiskit Metal: 创建平面芯片设计（DesignPlanar）", _metal.create_design)
register_tool("metal_add_transmon", "Qiskit Metal: 添加 Transmon 量子比特（TransmonPocket / TransmonCross）", _metal.add_transmon)
register_tool("metal_add_route", "Qiskit Metal: 添加 CPW 路由（RouteMeander / Straight / Pathfinder）", _metal.add_route)
register_tool("metal_list_components", "Qiskit Metal: 列出设计中的所有组件", _metal.list_components)
register_tool("metal_export_gds", "Qiskit Metal: 导出设计为 GDS 文件", _metal.export_gds)
register_tool("metal_analyze_lom", "Qiskit Metal: LOM 分析 — 电容矩阵提取", _metal.analyze_lom)
register_tool("metal_analyze_epr", "Qiskit Metal: EPR 分析 — 本征模频率与耦合", _metal.analyze_epr)
register_tool("metal_available_components", "Qiskit Metal: 列出可用组件与分析类型", _metal.get_available_components)


# ——— KQCircuits 工具（版图设计 + 仿真导出 + 制造） ———
from quantamind.server import hands_kqcircuits as _kqc

register_tool("kqc_create_chip", "KQCircuits: 创建芯片布局", _kqc.create_chip)
register_tool("kqc_add_swissmon", "KQCircuits: 添加 Swissmon 量子比特（IQM 四臂 Transmon）", _kqc.add_swissmon)
register_tool("kqc_add_element", "KQCircuits: 添加通用元件（coupler/airbridge/flux_line/marker/junction 等）", _kqc.add_element)
register_tool("kqc_list_elements", "KQCircuits: 列出芯片中所有元件", _kqc.list_elements)
register_tool("kqc_export_ansys", "KQCircuits: 导出仿真到 Ansys HFSS/Q3D", _kqc.export_ansys)
register_tool("kqc_export_sonnet", "KQCircuits: 导出仿真到 Sonnet", _kqc.export_sonnet)
register_tool("kqc_export_gds", "KQCircuits: 导出 GDS/OAS 版图", _kqc.export_gds)
register_tool("kqc_export_mask", "KQCircuits: 导出制造掩膜（光学 + EBL）", _kqc.export_mask)
register_tool("kqc_available_elements", "KQCircuits: 列出可用元件与导出能力", _kqc.get_available_elements)


# ——— secsgem 工具（设备 SECS/GEM 通信） ———
from quantamind.server import hands_secsgem as _secs

register_tool("secs_connect", "secsgem: HSMS 连接半导体设备", _secs.connect_equipment)
register_tool("secs_equipment_status", "secsgem: 查询设备状态", _secs.get_equipment_status)
register_tool("secs_list_equipment", "secsgem: 列出所有设备及状态", _secs.list_equipment)
register_tool("secs_remote_command", "secsgem: 发送远程命令（START/STOP/PAUSE）", _secs.send_remote_command)
register_tool("secs_subscribe_event", "secsgem: 订阅 Collection Event", _secs.subscribe_collection_event)
register_tool("secs_list_alarms", "secsgem: 查询设备告警", _secs.list_alarms)
register_tool("secs_get_recipes", "secsgem: 查询设备配方列表", _secs.get_process_programs)
register_tool("secs_upload_recipe", "secsgem: 上传配方到设备", _secs.upload_recipe)
register_tool("secs_go_online", "secsgem: 设备上线", _secs.go_online)
register_tool("secs_capabilities", "secsgem: 查询 SECS/GEM 协议能力", _secs.get_capabilities)


# ——— OpenMES 工具（MES 业务层） ———
from quantamind.server import hands_openmes as _mes

register_tool("mes_list_routes", "OpenMES: 查询工艺路线列表", _mes.list_process_routes)
register_tool("mes_get_route", "OpenMES: 查询工艺路线详情", _mes.get_process_route)
register_tool("mes_list_lots", "OpenMES: 查询批次列表", _mes.list_lots)
register_tool("mes_get_lot", "OpenMES: 查询批次详情", _mes.get_lot)
register_tool("mes_list_work_orders", "OpenMES: 查询工单列表", _mes.list_work_orders)
register_tool("mes_query_yield", "OpenMES: 查询良率数据", _mes.query_yield)
register_tool("mes_query_spc", "OpenMES: SPC 统计过程控制查询", _mes.query_spc)
register_tool("mes_dispatch", "OpenMES: 批次派工", _mes.dispatch_lot)
register_tool("mes_report_work", "OpenMES: 报工", _mes.report_work)
register_tool("mes_capabilities", "OpenMES: 查询 MES 业务能力", _mes.get_capabilities)


# ——— CHIPMES 真实 MES 系统工具 ———
from quantamind.server import hands_chipmes as _chipmes

register_tool("chipmes_info", "CHIPMES: 获取系统信息（版本/模块/状态）", _chipmes.get_system_info)
register_tool("chipmes_api_docs", "CHIPMES: 获取 Swagger API 文档", _chipmes.get_api_docs)
register_tool("chipmes_orders", "CHIPMES: 查询生产订单", _chipmes.query_orders)
register_tool("chipmes_craft_routes", "CHIPMES: 查询工艺路线", _chipmes.query_craft_routes)
register_tool("chipmes_equipment", "CHIPMES: 查询设备列表", _chipmes.query_equipment)
register_tool("chipmes_yield", "CHIPMES: 查询良率统计", _chipmes.query_yield_stats)
register_tool("chipmes_start", "CHIPMES: 获取启动命令", _chipmes.start_chipmes)
register_tool("chipmes_capabilities", "CHIPMES: 查询系统能力", _chipmes.get_capabilities)
register_tool("chipmes_db_schema", "CHIPMES: 获取完整数据库表结构（401张表）", _chipmes.get_db_schema)
register_tool("chipmes_table_detail", "CHIPMES: 查询指定表的详细结构", _chipmes.query_table_structure)


# ——— Grafana 工具（可视化大屏） ———
from quantamind.server import hands_grafana as _grafana

register_tool("grafana_list_dashboards", "Grafana: 查询看板列表", _grafana.list_dashboards)
register_tool("grafana_get_dashboard", "Grafana: 查询看板详情", _grafana.get_dashboard)
register_tool("grafana_embed_url", "Grafana: 生成看板嵌入 URL", _grafana.get_embed_url)
register_tool("grafana_list_datasources", "Grafana: 查询数据源", _grafana.list_datasources)
register_tool("grafana_query", "Grafana: 查询数据源数据", _grafana.query_datasource)
register_tool("grafana_create_equipment_dashboard", "Grafana: 为设备创建监控看板", _grafana.create_equipment_dashboard)
register_tool("grafana_capabilities", "Grafana: 查询可视化能力", _grafana.get_capabilities)


# ——— ARTIQ 工具（实时测控） ———
from quantamind.server import hands_artiq as _artiq

register_tool("artiq_list_devices", "ARTIQ: 列出硬件设备（DDS/TTL/DAC/core）", _artiq.list_devices)
register_tool("artiq_run_pulse", "ARTIQ: 执行脉冲序列（Rabi/T1/T2/光谱/读出优化）", _artiq.run_pulse_sequence)
register_tool("artiq_run_scan", "ARTIQ: 执行参数扫描", _artiq.run_scan)
register_tool("artiq_get_dataset", "ARTIQ: 查询实验数据集", _artiq.get_dataset)
register_tool("artiq_schedule", "ARTIQ: 提交实验到调度器", _artiq.schedule_experiment)
register_tool("artiq_capabilities", "ARTIQ: 查询实时测控能力", _artiq.get_capabilities)


# ——— Qiskit Pulse 工具（校准） ———
from quantamind.server import hands_qiskit_pulse as _pulse

register_tool("pulse_build_gate", "Qiskit Pulse: 构建量子门脉冲调度", _pulse.build_gate_schedule)
register_tool("pulse_cal_amplitude", "Qiskit Pulse: 校准门振幅（Rabi）", _pulse.calibrate_amplitude)
register_tool("pulse_cal_drag", "Qiskit Pulse: 校准 DRAG 参数", _pulse.calibrate_drag)
register_tool("pulse_cal_frequency", "Qiskit Pulse: 精确校准频率（Ramsey）", _pulse.calibrate_frequency)
register_tool("pulse_cal_readout", "Qiskit Pulse: 校准读出参数", _pulse.calibrate_readout)
register_tool("pulse_full_calibration", "Qiskit Pulse: 全套自动校准", _pulse.run_full_calibration)
register_tool("pulse_get_calibrations", "Qiskit Pulse: 查询已校准参数", _pulse.get_calibration_values)
register_tool("pulse_get_calibration_history", "Qiskit Pulse: 查询校准历史", _pulse.get_calibration_history)
register_tool("pulse_capabilities", "Qiskit Pulse: 查询校准能力", _pulse.get_capabilities)


# ——— Qiskit Experiments 工具（标准实验与分析层） ———
from quantamind.server import hands_qiskit_experiments as _qexp

register_tool("qexp_t1", "Qiskit Experiments: T1 标准实验与自动分析", _qexp.run_t1_experiment)
register_tool("qexp_ramsey", "Qiskit Experiments: RamseyXY 标准实验与自动分析", _qexp.run_ramsey_experiment)
register_tool("qexp_rabi", "Qiskit Experiments: Rabi 标准实验与自动分析", _qexp.run_rabi_experiment)
register_tool("qexp_readout", "Qiskit Experiments: ReadoutAngle 标准实验与自动分析", _qexp.run_readout_experiment)
register_tool("qexp_drag", "Qiskit Experiments: DragCal 标准实验与自动分析", _qexp.run_drag_experiment)
register_tool("qexp_batch_characterization", "Qiskit Experiments: 批量标准表征流水线", _qexp.run_batch_characterization)
register_tool("qexp_capabilities", "Qiskit Experiments: 查询标准实验层能力", _qexp.get_capabilities)


# ——— Mitiq 工具（错误缓解） ———
from quantamind.server import hands_mitiq as _mitiq

register_tool("mitiq_zne", "Mitiq: 零噪声外推（ZNE）", _mitiq.apply_zne)
register_tool("mitiq_pec", "Mitiq: 概率错误消除（PEC）", _mitiq.apply_pec)
register_tool("mitiq_cdr", "Mitiq: Clifford 数据回归（CDR）", _mitiq.apply_cdr)
register_tool("mitiq_dd", "Mitiq: 动力学去耦（DD）", _mitiq.apply_dynamical_decoupling)
register_tool("mitiq_benchmark", "Mitiq: 对比纠错技术并推荐", _mitiq.benchmark_techniques)
register_tool("mitiq_capabilities", "Mitiq: 查询错误缓解能力", _mitiq.get_capabilities)


# ——— QCoDeS 工具（量子测量数据） ———
from quantamind.server import hands_qcodes as _qcodes

register_tool("qcodes_list_instruments", "QCoDeS: 列出仪器", _qcodes.list_instruments)
register_tool("qcodes_list_experiments", "QCoDeS: 列出实验", _qcodes.list_experiments)
register_tool("qcodes_list_runs", "QCoDeS: 列出测量 Run", _qcodes.list_runs)
register_tool("qcodes_get_run_data", "QCoDeS: 获取 Run 数据", _qcodes.get_run_data)
register_tool("qcodes_export_dataset", "QCoDeS: 导出数据集（CSV/NetCDF）", _qcodes.export_dataset)
register_tool("qcodes_query_metadata", "QCoDeS: 按元数据查询", _qcodes.query_by_metadata)
register_tool("qcodes_capabilities", "QCoDeS: 查询能力", _qcodes.get_capabilities)


# ——— SeaTunnel 工具（ETL 管道） ———
from quantamind.server import hands_seatunnel as _st

register_tool("seatunnel_list_jobs", "SeaTunnel: 列出同步任务（REST 优先）", _st.list_jobs)
register_tool("seatunnel_get_job", "SeaTunnel: 查询任务详情", _st.get_job)
register_tool("seatunnel_submit_job", "SeaTunnel: 提交同步任务", _st.submit_sync_job)
register_tool("seatunnel_sync_qcodes", "SeaTunnel: QCoDeS→OLAP 同步", _st.sync_qcodes_to_warehouse)
register_tool("seatunnel_sync_mes", "SeaTunnel: OpenMES→OLAP 同步", _st.sync_mes_to_warehouse)
register_tool("seatunnel_sync_design", "SeaTunnel: 设计元数据→OLAP 同步", _st.sync_design_to_warehouse)
register_tool("seatunnel_pipeline_status", "SeaTunnel: 管道汇总状态", _st.get_pipeline_status)
register_tool("seatunnel_capabilities", "SeaTunnel: 查询能力", _st.get_capabilities)


# ——— OLAP 数据仓库（warehouse_* 推荐；doris_* 为兼容别名） ———
from quantamind.server import hands_warehouse as _wh

register_tool("warehouse_list_domains", "数据中台: 列出数据域", _wh.list_domains)
register_tool("warehouse_list_tables", "数据中台: 列出数据表", _wh.list_tables)
register_tool("warehouse_query_sql", "数据中台: 执行 SQL", _wh.query_sql)
register_tool("warehouse_query_qubit", "数据中台: 查询比特表征数据", _wh.query_qubit_characterization)
register_tool("warehouse_query_yield", "数据中台: 查询良率趋势", _wh.query_yield_trend)
register_tool("warehouse_query_design", "数据中台: 查询设计仿真摘要", _wh.query_design_simulation_summary)
register_tool("warehouse_cross_domain", "数据中台: 跨域关联查询", _wh.cross_domain_query)
register_tool("warehouse_capabilities", "数据中台: 查询能力", _wh.get_capabilities)
register_tool("warehouse_save_pipeline", "数据中台: 保存流水线运行记录", _wh.save_pipeline_run)
register_tool("warehouse_save_steps", "数据中台: 保存流水线步骤记录", _wh.save_pipeline_steps)
register_tool("warehouse_save_design_params", "数据中台: 保存芯片设计参数", _wh.save_design_params)
register_tool("warehouse_save_measurements", "数据中台: 保存测量结果", _wh.save_measurement_results)
register_tool("warehouse_query_pipeline_history", "数据中台: 查询流水线历史", _wh.query_pipeline_history)
register_tool("warehouse_query_step_records", "数据中台: 查询步骤记录", _wh.query_step_records)
register_tool("warehouse_export_training_data", "数据中台: 导出 AI 训练数据集", _wh.export_training_dataset)

from quantamind.server import hands_doris as _doris

register_tool("doris_list_domains", "兼容别名 doris_*：列出数据域（同 warehouse_*）", _doris.list_domains)
register_tool("doris_list_tables", "兼容别名 doris_*：列出数据表（同 warehouse_*）", _doris.list_tables)
register_tool("doris_query_sql", "兼容别名 doris_*：执行 SQL（同 warehouse_*）", _doris.query_sql)
register_tool("doris_query_qubit", "兼容别名 doris_*：查询比特表征（同 warehouse_*）", _doris.query_qubit_characterization)
register_tool("doris_query_yield", "兼容别名 doris_*：查询良率趋势（同 warehouse_*）", _doris.query_yield_trend)
register_tool("doris_query_design", "兼容别名 doris_*：查询设计仿真摘要（同 warehouse_*）", _doris.query_design_simulation_summary)
register_tool("doris_cross_domain", "兼容别名 doris_*：跨域关联查询（同 warehouse_*）", _doris.cross_domain_query)
register_tool("doris_capabilities", "兼容别名 doris_*：查询能力（同 warehouse_*）", _doris.get_capabilities)
register_tool("doris_save_pipeline", "兼容别名 doris_*：保存流水线运行记录", _doris.save_pipeline_run)
register_tool("doris_save_steps", "兼容别名 doris_*：保存流水线步骤记录", _doris.save_pipeline_steps)
register_tool("doris_save_design_params", "兼容别名 doris_*：保存芯片设计参数", _doris.save_design_params)
register_tool("doris_save_measurements", "兼容别名 doris_*：保存测量结果", _doris.save_measurement_results)
register_tool("doris_query_pipeline_history", "兼容别名 doris_*：查询流水线历史", _doris.query_pipeline_history)
register_tool("doris_query_step_records", "兼容别名 doris_*：查询步骤记录", _doris.query_step_records)
register_tool("doris_export_training_data", "兼容别名 doris_*：导出 AI 训练数据集", _doris.export_training_dataset)


# ——— qData 工具（数据治理） ———
from quantamind.server import hands_qdata as _qdata

register_tool("qdata_list_assets", "qData: 列出数据资产", _qdata.list_data_assets)
register_tool("qdata_get_asset", "qData: 查询资产详情", _qdata.get_data_asset)
register_tool("qdata_list_standards", "qData: 列出数据标准", _qdata.list_data_standards)
register_tool("qdata_quality_check", "qData: 执行数据质量检查", _qdata.run_quality_check)
register_tool("qdata_text2sql", "qData: 自然语言转 SQL（Text2SQL）", _qdata.text2sql)
register_tool("qdata_create_service", "qData: 创建数据服务 API", _qdata.create_data_service)
register_tool("qdata_lineage", "qData: 数据血缘追溯", _qdata.get_lineage)
register_tool("qdata_capabilities", "qData: 查询能力", _qdata.get_capabilities)


# ——— 情报工具（arXiv / 日报 / 飞书） ———
from quantamind.server import hands_intel as _intel

register_tool("intel_run_daily_digest", "情报: 执行 arXiv 每日检索、摘要、入库与推送", _intel.run_daily_digest)
register_tool("intel_list_recent_papers", "情报: 列出近期检索到的论文", _intel.list_recent_papers)
register_tool("intel_list_reports", "情报: 列出历史情报日报", _intel.list_reports)
register_tool("intel_capabilities", "情报: 查询情报员能力", _intel.capabilities)


# ——— 项目资料库工具 ———
from quantamind.server import project_library as _lib

register_tool("library_list_files", "资料库: 列出项目文件", _lib.list_files)
register_tool("library_search", "资料库: 搜索文件（按名称/类型/内容）", _lib.search_files)
register_tool("library_stats", "资料库: 统计信息", _lib.get_stats)


# ——— QEDA 团队设计代码工具 ———
from quantamind.server import hands_qeda_code as _qeda

register_tool("qeda_junction_params", "QEDA: 获取约瑟夫森结设计参数（曼哈顿/SQUID）", _qeda.get_junction_params)
register_tool("qeda_list_chips", "QEDA: 列出可用芯片规格（20bit/105bit）", _qeda.list_chip_specs)
register_tool("qeda_get_chip", "QEDA: 获取芯片完整规格", _qeda.get_chip_spec)
register_tool("qeda_get_qubit", "QEDA: 查询比特设计参数", _qeda.get_qubit_params)
register_tool("qeda_list_code", "QEDA: 列出设计团队所有文件", _qeda.list_qeda_code_files)
register_tool("qeda_catalog", "QEDA: 获取芯片设计团队资料目录（含每份文件的内容说明）", _qeda.get_qeda_catalog)
register_tool("qeda_real_design", "QEDA: 获取真实芯片设计资料（1bit/2bit/20bit_ct20q/105bit/test_chip）", _qeda.get_real_design)

# ── 真实芯片版图生成 ──
from quantamind.server import real_chip_builder as _rcb
register_tool("build_ct20q_real", "QEDA: 部署团队真实20比特CT20Q工业级GDS（24888 shapes, 9.6MB）", _rcb.build_ct20q_real)
register_tool("build_real_chip", "QEDA: 部署团队真实芯片GDS（1bit/2bit/20bit/105bit, 工业级版图）", _rcb.build_real_chip)
register_tool("build_100bit_reference", "QEDA: 生成100比特参考级GDS（10x10网格, 含Xmon+耦合器+谐振腔+焊盘）", _rcb.build_100bit_reference)
register_tool("generate_ct20q_live", "QEDA: 实时运行团队版图代码生成工业级20比特GDS（NoopGUI+SafeRoutePathfinder）", _rcb.generate_ct20q_live)

from quantamind.server import open_metal_gui as _mgui
register_tool("open_metal_gui", "QEDA: 打开 MetalGUI 可视化窗口查看芯片版图设计", _mgui.open_gui_with_design)

# ── 理论物理学家 Agent 工具（M0~M8）──
from quantamind.server import hands_theorist as _theorist

register_tool("theorist_build_device_graph", "理论物理: M0 构建器件关系图（DeviceGraph）", _theorist.build_device_graph)
register_tool("theorist_build_hamiltonian", "理论物理: M1 构建有效哈密顿量模型（EPR/BBQ/Lumped）", _theorist.build_hamiltonian)
register_tool("theorist_noise_budget", "理论物理: M2 开系统噪声与误差预算（T1/T2分解+门误差预算）", _theorist.compute_noise_budget)
register_tool("theorist_calibrate_model", "理论物理: M3 参数反演与模型校准（贝叶斯后验+可辨识性）", _theorist.calibrate_model)
register_tool("theorist_plan_experiment", "理论物理: M4 信息增益驱动的实验设计（主动学习）", _theorist.plan_experiment)
register_tool("theorist_optimize_pulse", "理论物理: M5 控制脉冲与门优化（DRAG/GRAPE/鲁棒控制）", _theorist.optimize_control_pulse)
register_tool("theorist_diagnose", "理论物理: M6 根因归因与故障树推理", _theorist.diagnose_root_cause)
register_tool("theorist_design_proposal", "理论物理: M7 设计优化方案生成（Pareto前沿+风险评估）", _theorist.generate_design_proposal)
register_tool("theorist_knowledge_search", "理论物理: M8 物理知识图谱检索（现象→机理→实验→缓解）", _theorist.search_physics_knowledge)
register_tool("theorist_status", "理论物理: 获取Agent模块状态汇总", _theorist.get_theorist_status)

# ── 仿真引擎工具（HFSS / Q3D / LOM / EPR）──
from quantamind.server import hands_simulation as _sim

register_tool("sim_status", "仿真: 获取仿真环境状态（Ansys/pyaedt/引擎）", _sim.get_simulation_status)
register_tool("sim_hfss_eigenmode", "仿真: HFSS 本征模仿真（谐振频率+Q值+模态）", _sim.run_hfss_eigenmode)
register_tool("sim_q3d_extraction", "仿真: Q3D 电容矩阵提取（组件间电容耦合）", _sim.run_q3d_extraction)
register_tool("sim_lom_analysis", "仿真: LOM 集总模型分析（EJ/EC→频率/非谐）", _sim.run_lom_analysis)
register_tool("sim_epr_analysis", "仿真: EPR 能量参与比分析（场分布→量子化）", _sim.run_epr_analysis)
register_tool("sim_export_hfss", "仿真: 导出 Ansys HFSS 项目文件（.aedt+脚本）", _sim.export_to_hfss_project)
register_tool("sim_full_chip", "仿真: 完整芯片仿真流程（Q3D+LOM+EPR+Eigen）", _sim.run_full_chip_simulation)

# ── QEDA 工程模型桥（EDA-Q-main 迁移的占位工具注册表）──
from quantamind.server import hands_qeda_bridge as _qeda_bridge

_qeda_bridge.register_qeda_bridge_tools()
