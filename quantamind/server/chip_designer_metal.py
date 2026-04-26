"""
专业芯片设计模块 — 基于「20比特可调耦合器双比特设计方案」
关键参数:
  - 12.5mm x 12.5mm 芯片
  - 20 比特一维链结构（蛇形排布）
  - 19 个可调耦合器（相邻比特之间）
  - 每比特一个读出谐振腔
  - 48 管脚（47 可用）
  - Xmon 类型（TransmonPocket）
  - Qodd=5.152GHz, Qeven=4.650GHz, Coupler=6.844GHz
  - CPW 特征阻抗 50Ω (s=10um, w=5um 蓝宝石/w=6.5um 硅)
"""
import os
import math
import logging

_log = logging.getLogger("quantamind.chip_designer")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qiskit_metal import designs, Dict
    from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
    from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
    from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
    HAS_METAL = True
except ImportError:
    HAS_METAL = False
    _log.warning("Qiskit Metal not available")


# ── 20 比特设计方案参数（来自设计文档） ──
QUBIT_PARAMS_20BIT = [
    {"id": "Q1",  "freq": 5.152, "res_freq": 7.378, "res_len_mm": 3.666, "EC": 260.35, "EJ": 14.21},
    {"id": "Q2",  "freq": 4.650, "res_freq": 7.073, "res_len_mm": 3.834, "EC": 260.97, "EJ": 11.68},
    {"id": "Q3",  "freq": 5.152, "res_freq": 7.439, "res_len_mm": 3.630, "EC": 260.35, "EJ": 14.21},
    {"id": "Q4",  "freq": 4.650, "res_freq": 7.133, "res_len_mm": 3.795, "EC": 260.97, "EJ": 11.68},
    {"id": "Q5",  "freq": 5.152, "res_freq": 7.500, "res_len_mm": 3.594, "EC": 260.35, "EJ": 14.21},
    {"id": "Q6",  "freq": 4.650, "res_freq": 7.188, "res_len_mm": 3.756, "EC": 260.97, "EJ": 11.68},
    {"id": "Q7",  "freq": 5.152, "res_freq": 7.554, "res_len_mm": 3.559, "EC": 260.35, "EJ": 14.21},
    {"id": "Q8",  "freq": 4.650, "res_freq": 7.250, "res_len_mm": 3.717, "EC": 260.97, "EJ": 11.68},
    {"id": "Q9",  "freq": 5.152, "res_freq": 7.615, "res_len_mm": 3.524, "EC": 260.35, "EJ": 14.21},
    {"id": "Q10", "freq": 4.650, "res_freq": 7.310, "res_len_mm": 3.680, "EC": 260.97, "EJ": 11.68},
    {"id": "Q11", "freq": 5.152, "res_freq": 7.410, "res_len_mm": 3.648, "EC": 260.35, "EJ": 14.21},
    {"id": "Q12", "freq": 4.650, "res_freq": 7.104, "res_len_mm": 3.814, "EC": 260.97, "EJ": 11.68},
    {"id": "Q13", "freq": 5.152, "res_freq": 7.470, "res_len_mm": 3.612, "EC": 260.35, "EJ": 14.21},
    {"id": "Q14", "freq": 4.650, "res_freq": 7.165, "res_len_mm": 3.775, "EC": 260.97, "EJ": 11.68},
    {"id": "Q15", "freq": 5.152, "res_freq": 7.532, "res_len_mm": 3.576, "EC": 260.35, "EJ": 14.21},
    {"id": "Q16", "freq": 4.650, "res_freq": 7.223, "res_len_mm": 3.738, "EC": 260.97, "EJ": 11.68},
    {"id": "Q17", "freq": 5.152, "res_freq": 7.589, "res_len_mm": 3.543, "EC": 260.35, "EJ": 14.21},
    {"id": "Q18", "freq": 4.650, "res_freq": 7.286, "res_len_mm": 3.699, "EC": 260.97, "EJ": 11.68},
    {"id": "Q19", "freq": 5.152, "res_freq": 7.966, "res_len_mm": 3.339, "EC": 260.35, "EJ": 14.21},
    {"id": "Q20", "freq": 4.650, "res_freq": 7.660, "res_len_mm": 3.479, "EC": 260.97, "EJ": 11.68},
]


def _snake_positions(n_qubits, chip_w, chip_h, margin=1800):
    """生成蛇形一维链的比特坐标（居中于芯片）
    比特排成一条蛇形路径，从左到右再折返，匹配 CETC 参考版图"""
    cols = 10
    rows = math.ceil(n_qubits / cols)
    spacing_x = (chip_w - 2 * margin) / max(cols - 1, 1)
    spacing_y = (chip_h - 2 * margin) / max(rows - 1, 1)
    spacing_y = min(spacing_y, 2200)

    start_x = -chip_w / 2 + margin
    center_y_offset = -(rows - 1) * spacing_y / 2

    positions = []
    for i in range(n_qubits):
        row = i // cols
        col_in_row = i % cols
        if row % 2 == 0:
            x = start_x + col_in_row * spacing_x
        else:
            x = start_x + (cols - 1 - col_in_row) * spacing_x
        y = center_y_offset + row * spacing_y
        positions.append((x, y))
    return positions


def design_20bit_chain(
    output_gds: str = "TG5.440.0001WX_20bit.gds",
    chip_size_mm: float = 12.5,
) -> dict:
    """按参考图生成 20 比特专用版图。"""
    chip_um = chip_size_mm * 1000
    output_dir = os.path.dirname(output_gds)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        from quantamind.server.gds_generator import generate_reference_20bit_gds

        generate_reference_20bit_gds(
            output_gds,
            chip_name="TG5.440.0001WX_20bit",
            chip_size=chip_um,
            with_labels=True,
        )
        file_size = os.path.getsize(output_gds)
        _log.info("20 比特参考版图导出成功: %s (%s bytes)", output_gds, f"{file_size:,}")
        export_ok = True
    except Exception as e:
        _log.error("20 比特参考版图生成失败: %s", e)
        export_ok = False
        file_size = 0

    return {
        "success": export_ok,
        "gds_file": output_gds,
        "file_size_bytes": file_size,
        "chip_size_mm": [chip_size_mm, chip_size_mm],
        "topology": "reference-like diagonal chain",
        "total_qubits": 20,
        "qubit_type": "Xmon-like reference layout",
        "total_couplers": 19,
        "total_pads": 48,
        "readout_groups": 5,
        "backend": "gdstk_reference_generator",
        "reference_doc": "20比特可调耦合器双比特设计方案.docx",
        "target_image": "用户提供的 20 比特参考版图",
    }


def design_NxM_chip(
    N_x: int = 5, N_y: int = 4,
    output_gds: str = "chip_design.gds",
    chip_size_x_mm: float = None, chip_size_y_mm: float = None,
    qubit_spacing_um: float = 2200,
    cpw_length_mm: float = 7.0, readout_length_mm: float = 6.0,
    with_readout_pads: bool = True,
) -> dict:
    """通用 NxM 网格芯片设计（保留向后兼容）"""
    total = N_x * N_y
    if total == 20 and chip_size_x_mm in (None, 12.5) and chip_size_y_mm in (None, 12.5):
        return design_20bit_chain(output_gds)
    # 其他规格仍用网格布局
    return _design_grid(N_x, N_y, output_gds, chip_size_x_mm, chip_size_y_mm,
                        qubit_spacing_um, cpw_length_mm, readout_length_mm, with_readout_pads)


def _design_grid(N_x, N_y, output_gds, chip_size_x_mm, chip_size_y_mm,
                 qubit_spacing_um, cpw_length_mm, readout_length_mm, with_readout_pads):
    """NxM 网格布局（用于 100 比特等）"""
    if not HAS_METAL:
        return {"error": "Qiskit Metal not installed"}
    total_qubits = N_x * N_y
    if chip_size_x_mm is None:
        chip_size_x_mm = max(9, (N_x - 1) * (qubit_spacing_um / 1000) + 5)
    if chip_size_y_mm is None:
        chip_size_y_mm = max(9, (N_y - 1) * (qubit_spacing_um / 1000) + 5)

    design = designs.DesignPlanar()
    design.overwrite_enabled = True
    design.chips.main.size.size_x = f'{chip_size_x_mm}mm'
    design.chips.main.size.size_y = f'{chip_size_y_mm}mm'
    design.variables['cpw_width'] = '10 um'
    design.variables['cpw_gap'] = '6 um'

    grid_w = (N_x - 1) * qubit_spacing_um
    grid_h = (N_y - 1) * qubit_spacing_um
    ox = -grid_w / 2
    oy = -grid_h / 2

    conn_pads = dict(
        B0=dict(loc_W=-1, loc_H=-1, pad_width='75um'),
        B1=dict(loc_W=-1, loc_H=+1, pad_width='120um'),
        B2=dict(loc_W=+1, loc_H=-1, pad_width='120um'),
        B3=dict(loc_W=+1, loc_H=+1, pad_width='90um'),
    )
    for ix in range(N_x):
        for iy in range(N_y):
            TransmonPocket(design, f"Q_{ix}_{iy}", options=dict(
                pos_x=f'{ox + ix * qubit_spacing_um}um',
                pos_y=f'{oy + iy * qubit_spacing_um}um',
                orientation='-90', connection_pads=conn_pads))
    design.rebuild()

    cpw_count = 0
    fillet = '99um'
    for ix in range(N_x):
        for iy in range(N_y):
            if iy < N_y - 1:
                try:
                    RouteMeander(design, f'CU_{ix}_{iy}', options=dict(
                        total_length=f'{cpw_length_mm + (iy % 2) * 0.3}mm', fillet=fillet,
                        lead=dict(start_straight='0.4mm', end_straight='0.2mm'),
                        meander=dict(asymmetry='-500um'),
                        pin_inputs=dict(start_pin=dict(component=f'Q_{ix}_{iy}', pin='B0'),
                                        end_pin=dict(component=f'Q_{ix}_{iy+1}', pin='B3'))))
                    cpw_count += 1
                except Exception:
                    pass
            if ix < N_x - 1:
                try:
                    RouteMeander(design, f'CS_{ix}_{iy}', options=dict(
                        total_length=f'{cpw_length_mm - 0.5 + (iy % 2) * 0.3}mm', fillet=fillet,
                        lead=dict(start_straight='0.3mm', end_straight='0.2mm'),
                        meander=dict(asymmetry='-200um'),
                        pin_inputs=dict(start_pin=dict(component=f'Q_{ix}_{iy}', pin='B1'),
                                        end_pin=dict(component=f'Q_{ix+1}_{iy}', pin='B2'))))
                    cpw_count += 1
                except Exception:
                    pass
    design.rebuild()

    try:
        gds = design.renderers.gds
        gds.options['no_cheese']['buffer'] = '50um'
        gds.options.cheese.view_in_file = Dict(main={1: False})
        gds.options.no_cheese.view_in_file = Dict(main={1: True})
        gds.export_to_gds(output_gds)
        file_size = os.path.getsize(output_gds)
        ok = True
    except Exception:
        ok = False
        file_size = 0

    return {"success": ok, "gds_file": output_gds, "file_size_bytes": file_size,
            "grid": f"{N_x}x{N_y}", "total_qubits": total_qubits,
            "total_cpw_routes": cpw_count, "backend": "qiskit_metal"}
