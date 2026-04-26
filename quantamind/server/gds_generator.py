"""
GDS Generator — 专业量子芯片版图生成器（参照 CETC 风格）
用 gdstk 直接生成标准 GDS，包含：
  - TransmonCross 量子比特（十字形）
  - 蛇形读出谐振腔
  - CPW 共面波导走线（蛇形布线至边缘）
  - 四周线键合焊盘（Launchpad）带编号
  - 四角对准标记
  - 接地平面（含间隙开孔）
"""
import math
from typing import List, Tuple, Dict, Optional

try:
    import gdstk
    HAS_GDSTK = True
except ImportError:
    HAS_GDSTK = False

# ── 层定义（与工艺对应） ──
LY_GROUND = (0, 0)    # 接地平面
LY_METAL  = (1, 0)    # 金属层（Nb 超导层）
LY_GAP    = (2, 0)    # 间隙/刻蚀开孔
LY_JJ     = (3, 0)    # 约瑟夫森结层
LY_PAD    = (4, 0)    # 焊盘层
LY_FRAME  = (1, 10)   # 芯片边框
LY_LABEL  = (10, 0)   # 文字标签
LY_ALIGN  = (11, 0)   # 对准标记

REFERENCE_20BIT_RESONATOR_MM = [
    3.66606, 3.83451, 3.62997, 3.79495, 3.59394,
    3.75559, 3.55890, 3.71705, 3.52400, 3.67971,
    3.64760, 3.81445, 3.61167, 3.77498, 3.57600,
    3.73756, 3.54273, 3.69851, 3.33889, 3.47900,
]


def _transmon_cross(
    cell, cx: float, cy: float,
    arm_length: float = 160,
    arm_width: float = 30,
    gap: float = 20,
    jj_w: float = 1.5,
    jj_h: float = 12,
):
    """
    绘制 TransmonCross（十字形 Transmon）：
    四臂十字 + 中心约瑟夫森结 + 间隙开孔
    返回四个方向的连接点
    """
    hw = arm_width / 2
    pins = {}

    for angle, label in [(0, "E"), (90, "N"), (180, "W"), (270, "S")]:
        rad = math.radians(angle)
        dx, dy = math.cos(rad), math.sin(rad)

        x1 = cx + dx * hw - dy * hw
        y1 = cy + dy * hw + dx * hw
        x2 = cx + dx * arm_length + dy * hw
        y2 = cy + dy * arm_length - dx * hw
        x3 = cx + dx * arm_length - dy * hw
        y3 = cy + dy * arm_length + dx * hw
        x4 = cx + dx * hw + dy * hw
        y4 = cy + dy * hw - dx * hw

        arm = gdstk.Polygon(
            [(x1, y1), (x2, y2), (x3, y3), (x4, y4)],
            layer=LY_METAL[0], datatype=LY_METAL[1]
        )
        cell.add(arm)

        gap_ext = gap
        gx1 = cx + dx * (hw - gap_ext) - dy * (hw + gap_ext)
        gy1 = cy + dy * (hw - gap_ext) + dx * (hw + gap_ext)
        gx2 = cx + dx * (arm_length + gap_ext) + dy * (hw + gap_ext)
        gy2 = cy + dy * (arm_length + gap_ext) - dx * (hw + gap_ext)
        gx3 = cx + dx * (arm_length + gap_ext) - dy * (hw + gap_ext)
        gy3 = cy + dy * (arm_length + gap_ext) + dx * (hw + gap_ext)
        gx4 = cx + dx * (hw - gap_ext) + dy * (hw + gap_ext)
        gy4 = cy + dy * (hw - gap_ext) - dx * (hw + gap_ext)

        gap_poly = gdstk.Polygon(
            [(gx1, gy1), (gx2, gy2), (gx3, gy3), (gx4, gy4)],
            layer=LY_GAP[0], datatype=LY_GAP[1]
        )
        cell.add(gap_poly)

        pins[label] = (cx + dx * arm_length, cy + dy * arm_length)

    # 中心方块
    cell.add(gdstk.rectangle(
        (cx - hw, cy - hw), (cx + hw, cy + hw),
        layer=LY_METAL[0], datatype=LY_METAL[1]
    ))
    # 中心间隙
    cell.add(gdstk.rectangle(
        (cx - hw - gap, cy - hw - gap), (cx + hw + gap, cy + hw + gap),
        layer=LY_GAP[0], datatype=LY_GAP[1]
    ))
    # 约瑟夫森结
    cell.add(gdstk.rectangle(
        (cx - jj_w / 2, cy - jj_h / 2), (cx + jj_w / 2, cy + jj_h / 2),
        layer=LY_JJ[0], datatype=LY_JJ[1]
    ))

    return pins


def _meander_path(
    p_start: Tuple[float, float],
    p_end: Tuple[float, float],
    meander_width: float = 120,
    meander_spacing: float = 40,
    min_segments: int = 4,
) -> List[Tuple[float, float]]:
    """
    生成蛇形（meander）路径点列表：从 p_start 到 p_end
    主要沿水平方向蜿蜒，垂直逐步前进
    """
    x1, y1 = p_start
    x2, y2 = p_end
    pts = [(x1, y1)]

    dx = x2 - x1
    dy = y2 - y1
    dist = math.sqrt(dx * dx + dy * dy)

    if dist < meander_width * 2:
        mx = (x1 + x2) / 2
        pts.append((mx, y1))
        pts.append((mx, y2))
        pts.append((x2, y2))
        return pts

    if abs(dy) > abs(dx):
        step_y = meander_spacing if dy > 0 else -meander_spacing
        n_meanders = max(min_segments, int(abs(dy) / abs(meander_spacing)) - 1)
        actual_step = dy / n_meanders

        cx = x1
        cy = y1
        direction = 1 if x2 > x1 else -1
        half_w = meander_width / 2

        for i in range(n_meanders):
            cy += actual_step
            if i % 2 == 0:
                pts.append((cx + direction * half_w, pts[-1][1]))
                pts.append((cx + direction * half_w, cy))
            else:
                pts.append((cx - direction * half_w, pts[-1][1]))
                pts.append((cx - direction * half_w, cy))

        pts.append((x2, cy))
        pts.append((x2, y2))
    else:
        step_x = meander_spacing if dx > 0 else -meander_spacing
        n_meanders = max(min_segments, int(abs(dx) / abs(meander_spacing)) - 1)
        actual_step = dx / n_meanders

        cx = x1
        cy = y1
        direction = 1 if y2 > y1 else -1
        half_w = meander_width / 2

        for i in range(n_meanders):
            cx += actual_step
            if i % 2 == 0:
                pts.append((pts[-1][0], cy + direction * half_w))
                pts.append((cx, cy + direction * half_w))
            else:
                pts.append((pts[-1][0], cy - direction * half_w))
                pts.append((cx, cy - direction * half_w))

        pts.append((cx, y2))
        pts.append((x2, y2))

    return pts


def _cpw_flexpath(cell, points, cpw_w=10, cpw_gap=6):
    """绘制 CPW：中心导体 + 间隙"""
    cell.add(gdstk.FlexPath(points, cpw_w,
                            layer=LY_METAL[0], datatype=LY_METAL[1]))
    cell.add(gdstk.FlexPath(points, cpw_w + 2 * cpw_gap,
                            layer=LY_GAP[0], datatype=LY_GAP[1]))


def _launchpad(cell, cx, cy, orientation="S",
               pad_w=180, pad_h=220, taper_len=120, cpw_w=10):
    """
    绘制线键合焊盘（Launchpad）：
    大矩形焊盘 + 渐变至 CPW 宽度
    返回 CPW 连接点
    """
    hw = pad_w / 2
    if orientation == "S":
        cell.add(gdstk.rectangle((cx - hw, cy - pad_h), (cx + hw, cy), layer=LY_PAD[0], datatype=LY_PAD[1]))
        cell.add(gdstk.rectangle((cx - hw - 30, cy - pad_h - 30), (cx + hw + 30, cy + 30), layer=LY_GAP[0], datatype=LY_GAP[1]))
        taper = gdstk.Polygon([
            (cx - hw, cy), (cx + hw, cy),
            (cx + cpw_w / 2, cy + taper_len), (cx - cpw_w / 2, cy + taper_len)
        ], layer=LY_METAL[0], datatype=LY_METAL[1])
        cell.add(taper)
        return (cx, cy + taper_len)
    elif orientation == "N":
        cell.add(gdstk.rectangle((cx - hw, cy), (cx + hw, cy + pad_h), layer=LY_PAD[0], datatype=LY_PAD[1]))
        cell.add(gdstk.rectangle((cx - hw - 30, cy - 30), (cx + hw + 30, cy + pad_h + 30), layer=LY_GAP[0], datatype=LY_GAP[1]))
        taper = gdstk.Polygon([
            (cx - hw, cy), (cx + hw, cy),
            (cx + cpw_w / 2, cy - taper_len), (cx - cpw_w / 2, cy - taper_len)
        ], layer=LY_METAL[0], datatype=LY_METAL[1])
        cell.add(taper)
        return (cx, cy - taper_len)
    elif orientation == "W":
        cell.add(gdstk.rectangle((cx - pad_h, cy - hw), (cx, cy + hw), layer=LY_PAD[0], datatype=LY_PAD[1]))
        cell.add(gdstk.rectangle((cx - pad_h - 30, cy - hw - 30), (cx + 30, cy + hw + 30), layer=LY_GAP[0], datatype=LY_GAP[1]))
        taper = gdstk.Polygon([
            (cx, cy - hw), (cx, cy + hw),
            (cx + taper_len, cy + cpw_w / 2), (cx + taper_len, cy - cpw_w / 2)
        ], layer=LY_METAL[0], datatype=LY_METAL[1])
        cell.add(taper)
        return (cx + taper_len, cy)
    else:  # E
        cell.add(gdstk.rectangle((cx, cy - hw), (cx + pad_h, cy + hw), layer=LY_PAD[0], datatype=LY_PAD[1]))
        cell.add(gdstk.rectangle((cx - 30, cy - hw - 30), (cx + pad_h + 30, cy + hw + 30), layer=LY_GAP[0], datatype=LY_GAP[1]))
        taper = gdstk.Polygon([
            (cx, cy - hw), (cx, cy + hw),
            (cx - taper_len, cy + cpw_w / 2), (cx - taper_len, cy - cpw_w / 2)
        ], layer=LY_METAL[0], datatype=LY_METAL[1])
        cell.add(taper)
        return (cx - taper_len, cy)


def _alignment_mark(cell, cx, cy, size=200):
    """四角对准标记：十字 + 方框"""
    hw = size / 2
    bar_w = size / 10
    # 十字
    cell.add(gdstk.rectangle((cx - hw, cy - bar_w / 2), (cx + hw, cy + bar_w / 2),
                             layer=LY_ALIGN[0], datatype=LY_ALIGN[1]))
    cell.add(gdstk.rectangle((cx - bar_w / 2, cy - hw), (cx + bar_w / 2, cy + hw),
                             layer=LY_ALIGN[0], datatype=LY_ALIGN[1]))
    # 外框
    cell.add(gdstk.rectangle((cx - hw, cy - hw), (cx + hw, cy + hw),
                             layer=LY_ALIGN[0], datatype=LY_ALIGN[1]))
    inner = hw * 0.6
    cell.add(gdstk.rectangle((cx - inner, cy - inner), (cx + inner, cy + inner),
                             layer=LY_ALIGN[0], datatype=LY_ALIGN[1]))


def _manhattan_single_jj(cell, cx, cy, angle=45, size=18):
    """单结 Manhattan JJ 标记。"""
    bar1 = gdstk.rectangle((cx - size, cy - 1.1), (cx + size, cy + 1.1), layer=LY_JJ[0], datatype=LY_JJ[1])
    bar2 = gdstk.rectangle((cx - 1.1, cy - size), (cx + 1.1, cy + size), layer=LY_JJ[0], datatype=LY_JJ[1])
    bar1.rotate(math.radians(angle), (cx, cy))
    bar2.rotate(math.radians(angle), (cx, cy))
    cell.add(bar1)
    cell.add(bar2)


def _manhattan_squid(cell, cx, cy, angle=45, loop_w=26, loop_h=18, gap=6):
    """双结 SQUID 结构简化图。"""
    outer = gdstk.rectangle((cx - loop_w / 2, cy - loop_h / 2), (cx + loop_w / 2, cy + loop_h / 2),
                            layer=LY_METAL[0], datatype=LY_METAL[1])
    inner = gdstk.rectangle((cx - loop_w / 2 + gap, cy - loop_h / 2 + gap),
                            (cx + loop_w / 2 - gap, cy + loop_h / 2 - gap),
                            layer=LY_GAP[0], datatype=LY_GAP[1])
    outer.rotate(math.radians(angle), (cx, cy))
    inner.rotate(math.radians(angle), (cx, cy))
    cell.add(outer)
    cell.add(inner)
    _manhattan_single_jj(cell, cx - 6, cy, angle=angle, size=7)
    _manhattan_single_jj(cell, cx + 6, cy, angle=angle, size=7)


def _xmon_qubit_reference(cell, cx, cy, angle=45, arm_len=112, arm_w=34, gap=16, label=None, jj_variant="default"):
    """
    更接近参考图的 Xmon 量子比特：
    - 对角十字电容臂
    - 中心岛
    - Manhattan JJ 标记
    """
    bars = [
        gdstk.rectangle((cx - arm_len, cy - arm_w / 2), (cx + arm_len, cy + arm_w / 2),
                        layer=LY_METAL[0], datatype=LY_METAL[1]),
        gdstk.rectangle((cx - arm_w / 2, cy - arm_len), (cx + arm_w / 2, cy + arm_len),
                        layer=LY_METAL[0], datatype=LY_METAL[1]),
    ]
    gaps = [
        gdstk.rectangle((cx - arm_len - gap, cy - arm_w / 2 - gap), (cx + arm_len + gap, cy + arm_w / 2 + gap),
                        layer=LY_GAP[0], datatype=LY_GAP[1]),
        gdstk.rectangle((cx - arm_w / 2 - gap, cy - arm_len - gap), (cx + arm_w / 2 + gap, cy + arm_len + gap),
                        layer=LY_GAP[0], datatype=LY_GAP[1]),
    ]
    for poly in bars:
        poly.rotate(math.radians(angle), (cx, cy))
        cell.add(poly)
    for poly in gaps:
        poly.rotate(math.radians(angle), (cx, cy))
        cell.add(poly)

    center_island = gdstk.ellipse((cx, cy), 28, layer=LY_METAL[0], datatype=LY_METAL[1])
    cell.add(center_island)

    if jj_variant == "single_manhattan":
        _manhattan_single_jj(cell, cx, cy, angle=angle, size=11)
    else:
        _manhattan_single_jj(cell, cx, cy, angle=angle, size=9)

    rt2 = math.sqrt(2.0)
    u = (1.0 / rt2, 1.0 / rt2)
    v = (-1.0 / rt2, 1.0 / rt2)
    return {
        "upper": (cx + v[0] * 150, cy + v[1] * 150),
        "lower": (cx - v[0] * 150, cy - v[1] * 150),
        "forward": (cx + u[0] * 150, cy + u[1] * 150),
        "back": (cx - u[0] * 150, cy - u[1] * 150),
        "center": (cx, cy),
    }


def _tunable_coupler_reference(cell, cx, cy, angle=45):
    """
    更接近参考图的可调耦合器：
    - 主耦合导体（蛇形）
    - 中心岛
    - SQUID 环
    - Z 线耦合环近端
    """
    rt2 = math.sqrt(2.0)
    u = (1.0 / rt2, 1.0 / rt2)
    v = (-1.0 / rt2, 1.0 / rt2)
    p1 = (cx - u[0] * 110, cy - u[1] * 110)
    p2 = (cx + u[0] * 110, cy + u[1] * 110)
    _cpw_flexpath(cell, _zigzag_local(p1, p2, amp=24, turns=7), cpw_w=8, cpw_gap=5)
    cell.add(gdstk.ellipse((cx, cy), 20, layer=LY_METAL[0], datatype=LY_METAL[1]))
    squid_c = (cx + v[0] * 34, cy + v[1] * 34)
    _manhattan_squid(cell, squid_c[0], squid_c[1], angle=angle, loop_w=28, loop_h=18, gap=6)
    ring_c = (cx + v[0] * 90, cy + v[1] * 90)
    cell.add(gdstk.ellipse(ring_c, 18, inner_radius=10, layer=LY_METAL[0], datatype=LY_METAL[1]))
    return {"center": (cx, cy), "bias_pick": (ring_c[0] + v[0] * 30, ring_c[1] + v[1] * 30)}


def _zigzag_local(p1, p2, amp=24, turns=7):
    dx = (p2[0] - p1[0]) / (turns + 1)
    dy = (p2[1] - p1[1]) / (turns + 1)
    nv = (-dy, dx)
    nlen = math.hypot(nv[0], nv[1]) or 1
    nv = (nv[0] / nlen, nv[1] / nlen)
    pts = [p1]
    for i in range(1, turns + 1):
        base = (p1[0] + dx * i, p1[1] + dy * i)
        sign = 1 if i % 2 else -1
        pts.append((base[0] + nv[0] * amp * sign, base[1] + nv[1] * amp * sign))
    pts.append(p2)
    return pts


def _route_qubit_to_edge(cell, q_pin, edge_point, edge_side,
                         qubit_idx, total_on_edge, cpw_w=10, cpw_gap=6):
    """从 qubit pin 到边缘焊盘的蛇形布线"""
    pts = _meander_path(q_pin, edge_point, meander_width=80, meander_spacing=30)
    _cpw_flexpath(cell, pts, cpw_w, cpw_gap)


def generate_chip_gds(
    filename: str,
    num_qubits: int = 20,
    chip_name: str = "QuantumChip",
    chip_size_x: float = 12500,
    chip_size_y: float = 12500,
    with_readout: bool = True,
    with_labels: bool = True,
) -> str:
    """
    生成专业量子芯片 GDS 版图

    Args:
        filename: 输出文件路径
        num_qubits: 量子比特数量
        chip_name: 芯片名称
        chip_size_x/y: 芯片尺寸 (um)
    Returns:
        输出文件路径
    """
    if not HAS_GDSTK:
        raise RuntimeError("gdstk not installed")

    lib = gdstk.Library(name=chip_name, unit=1e-6, precision=1e-9)
    top = lib.new_cell("TOP")

    hx = chip_size_x / 2
    hy = chip_size_y / 2

    # ── 1. 接地平面（芯片衬底） ──
    top.add(gdstk.rectangle((-hx, -hy), (hx, hy), layer=LY_GROUND[0], datatype=LY_GROUND[1]))

    # ── 2. 芯片边框（双线框） ──
    frame_w = 30
    top.add(gdstk.rectangle((-hx, -hy), (hx, hy), layer=LY_FRAME[0], datatype=LY_FRAME[1]))
    m = 100
    top.add(gdstk.rectangle((-hx + m, -hy + m), (hx - m, hy - m), layer=LY_FRAME[0], datatype=LY_FRAME[1]))

    # ── 3. 四角对准标记 ──
    am = 350
    for sx, sy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        _alignment_mark(top, sx * (hx - am), sy * (hy - am), size=200)

    # ── 4. 量子比特网格 ──
    cols = math.ceil(math.sqrt(num_qubits * (chip_size_x / chip_size_y)))
    rows = math.ceil(num_qubits / cols)

    qubit_area_x = chip_size_x * 0.45
    qubit_area_y = chip_size_y * 0.45
    spacing_x = qubit_area_x / max(cols - 1, 1) if cols > 1 else 0
    spacing_y = qubit_area_y / max(rows - 1, 1) if rows > 1 else 0

    start_x = -qubit_area_x / 2
    start_y = -qubit_area_y / 2

    qubits = []
    idx = 0
    for row in range(rows):
        for col in range(cols):
            if idx >= num_qubits:
                break
            qx = start_x + col * spacing_x
            qy = start_y + row * spacing_y
            qname = f"Q{idx + 1}" if num_qubits < 100 else f"Q{idx + 1:03d}"

            arm_len = max(60, min(140, spacing_x * 0.18, spacing_y * 0.18)) if (spacing_x > 0 and spacing_y > 0) else 100

            pins = _transmon_cross(top, qx, qy, arm_length=arm_len, arm_width=max(16, arm_len * 0.2))
            qubits.append({"name": qname, "x": qx, "y": qy, "pins": pins, "row": row, "col": col})

            if with_labels:
                top.add(gdstk.Label(qname, (qx, qy - arm_len - 40), layer=LY_LABEL[0]))

            idx += 1

    # ── 5. 比特间 CPW 耦合走线 ──
    for i, q in enumerate(qubits):
        row, col = q["row"], q["col"]
        # 右邻居
        right = next((qq for qq in qubits if qq["row"] == row and qq["col"] == col + 1), None)
        if right:
            p1 = q["pins"]["E"]
            p2 = right["pins"]["W"]
            _cpw_flexpath(top, [p1, p2], cpw_w=10, cpw_gap=6)

        # 上邻居
        upper = next((qq for qq in qubits if qq["row"] == row + 1 and qq["col"] == col), None)
        if upper:
            p1 = q["pins"]["N"]
            p2 = upper["pins"]["S"]
            _cpw_flexpath(top, [p1, p2], cpw_w=10, cpw_gap=6)

    # ── 6. 四周焊盘 + 读出走线 ──
    pad_margin = 500
    pad_zone_start = -hx + pad_margin + 400
    pad_zone_end = hx - pad_margin - 400

    num_pads_per_side = max(num_qubits, 12)
    pads_top, pads_bottom, pads_left, pads_right = [], [], [], []
    n_per_edge = math.ceil(num_pads_per_side / 4)

    for i in range(n_per_edge):
        frac = i / max(n_per_edge - 1, 1)
        px = pad_zone_start + frac * (pad_zone_end - pad_zone_start)

        # 顶部焊盘
        cp = _launchpad(top, px, hy - pad_margin, "N")
        pads_top.append(cp)
        if with_labels:
            top.add(gdstk.Label(str(i + 1), (px, hy - pad_margin + 260), layer=LY_LABEL[0]))

        # 底部焊盘
        cp = _launchpad(top, px, -hy + pad_margin, "S")
        pads_bottom.append(cp)
        if with_labels:
            top.add(gdstk.Label(str(n_per_edge * 3 + n_per_edge - i), (px, -hy + pad_margin - 260), layer=LY_LABEL[0]))

    for i in range(n_per_edge):
        frac = i / max(n_per_edge - 1, 1)
        py = pad_zone_start + frac * (pad_zone_end - pad_zone_start)

        # 左侧焊盘
        cp = _launchpad(top, -hx + pad_margin, py, "W")
        pads_left.append(cp)
        if with_labels:
            top.add(gdstk.Label(str(n_per_edge * 3 + 1 - i), (-hx + pad_margin - 260, py), layer=LY_LABEL[0]))

        # 右侧焊盘
        cp = _launchpad(top, hx - pad_margin, py, "E")
        pads_right.append(cp)
        if with_labels:
            top.add(gdstk.Label(str(n_per_edge + i + 1), (hx - pad_margin + 260, py), layer=LY_LABEL[0]))

    # ── 7. 读出谐振腔 + 走线到焊盘 ──
    all_pads = []
    for q_idx, q in enumerate(qubits):
        edge_idx = q_idx % 4
        pad_idx_in_edge = q_idx // 4

        if edge_idx == 0 and pad_idx_in_edge < len(pads_top):
            target = pads_top[pad_idx_in_edge]
            pin = q["pins"]["N"]
        elif edge_idx == 1 and pad_idx_in_edge < len(pads_right):
            target = pads_right[pad_idx_in_edge]
            pin = q["pins"]["E"]
        elif edge_idx == 2 and pad_idx_in_edge < len(pads_bottom):
            target = pads_bottom[pad_idx_in_edge]
            pin = q["pins"]["S"]
        elif edge_idx == 3 and pad_idx_in_edge < len(pads_left):
            target = pads_left[pad_idx_in_edge]
            pin = q["pins"]["W"]
        else:
            continue

        pts = _meander_path(pin, target, meander_width=60, meander_spacing=25)
        _cpw_flexpath(top, pts, cpw_w=10, cpw_gap=6)

    # ── 8. 芯片标签 ──
    if with_labels:
        top.add(gdstk.Label(chip_name, (-hx + 300, hy - 200), layer=LY_LABEL[0]))
        info_text = f"{num_qubits}Q Transmon | {chip_size_x/1000:.1f}x{chip_size_y/1000:.1f}mm"
        top.add(gdstk.Label(info_text, (hx - 300, -hy + 200), layer=LY_LABEL[0]))

    lib.write_gds(filename)
    return filename


def generate_reference_20bit_gds(
    filename: str,
    chip_name: str = "TG5.440.0001WX_20bit",
    chip_size: float = 12500,
    with_labels: bool = True,
) -> str:
    """
    20 比特“参考图复刻版图”。
    这一版不再做自动布局，而是采用固定模板：
    - Q1~Q20: 手工坐标的对角主链
    - T1~T19: 手工偏置的耦合器带
    - 5 组总线: 固定中心和长度
    - 48 pads: 固定边界位置
    - 扇出线: 四边各自汇聚到本侧局部目标，不再穿越中心
    """
    if not HAS_GDSTK:
        raise RuntimeError("gdstk not installed")

    lib = gdstk.Library(name=chip_name, unit=1e-6, precision=1e-9)
    top = lib.new_cell("TOP")

    hx = chip_size / 2
    hy = chip_size / 2

    # Chip outline and marks
    top.add(gdstk.rectangle((-hx, -hy), (hx, hy), layer=LY_GROUND[0], datatype=LY_GROUND[1]))
    top.add(gdstk.rectangle((-hx, -hy), (hx, hy), layer=LY_FRAME[0], datatype=LY_FRAME[1]))
    top.add(gdstk.rectangle((-hx + 120, -hy + 120), (hx - 120, hy - 120), layer=LY_FRAME[0], datatype=LY_FRAME[1]))
    for sx, sy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        _alignment_mark(top, sx * (hx - 260), sy * (hy - 260), size=180)

    # Corner dicing boxes / checker blocks to mimic reference
    for cx, cy in [(-hx + 650, hy - 650), (hx - 650, hy - 650), (-hx + 650, -hy + 650)]:
        for ix in range(4):
            for iy in range(4):
                top.add(gdstk.rectangle(
                    (cx + ix * 80, cy + iy * 80),
                    (cx + ix * 80 + 55, cy + iy * 80 + 55),
                    layer=LY_METAL[0], datatype=LY_METAL[1],
                ))

    if with_labels:
        top.add(gdstk.Label("CETC", (-hx + 450, hy - 420), layer=LY_LABEL[0]))
        top.add(gdstk.Label("TG5.440.0001WX", (hx - 1700, -hy + 250), layer=LY_LABEL[0]))

    rt2 = math.sqrt(2.0)
    u = (1.0 / rt2, 1.0 / rt2)
    v = (-1.0 / rt2, 1.0 / rt2)

    def addp(p, q):
        return (p[0] + q[0], p[1] + q[1])

    def mul(vec, scale):
        return (vec[0] * scale, vec[1] * scale)

    def _route(points, cpw_w=10, cpw_gap=6):
        _cpw_flexpath(top, points, cpw_w=cpw_w, cpw_gap=cpw_gap)

    # 手工固定的 Q1~Q20 中心坐标
    q_centers = [
        (-1500, -2050), (-1320, -1870), (-1140, -1695), (-960, -1520),
        (-775, -1340), (-595, -1160), (-410, -980), (-225, -800),
        (-35, -620), (160, -435), (355, -245), (550, -55),
        (745, 135), (940, 325), (1135, 515), (1330, 705),
        (1525, 895), (1720, 1085), (1910, 1270), (2090, 1450),
    ]
    qubits = []
    for i, center in enumerate(q_centers):
        jj_variant = "single_manhattan" if i + 1 in (2, 5) else "default"
        pins = _xmon_qubit_reference(
            top,
            center[0],
            center[1],
            angle=45,
            arm_len=112 if i not in (9, 10) else 118,
            arm_w=34,
            gap=16,
            jj_variant=jj_variant,
        )
        qubits.append({"id": f"Q{i+1}", "center": center, "pins": pins})
        if with_labels:
            top.add(gdstk.Label(f"Q{i+1}", (center[0] - 110, center[1] - 145), layer=LY_LABEL[0]))

    # 手工固定的 T1~T19 耦合器中心
    coupler_points = [
        (-1430, -1870), (-1248, -1692), (-1065, -1512), (-882, -1335), (-698, -1152),
        (-516, -972), (-332, -790), (-145, -607), (42, -422),
        (238, -235), (434, -46), (630, 142), (826, 330), (1022, 520),
        (1218, 710), (1414, 900), (1610, 1090), (1805, 1278), (1994, 1465),
    ]
    for i, c in enumerate(coupler_points):
        coupler = _tunable_coupler_reference(top, c[0], c[1], angle=45)
        p1 = addp(c, mul(u, -108))
        p2 = addp(c, mul(u, 108))
        _route([qubits[i]["pins"]["upper"], p1], cpw_w=7, cpw_gap=5)
        _route([qubits[i + 1]["pins"]["upper"], p2], cpw_w=7, cpw_gap=5)
        if with_labels:
            top.add(gdstk.Label(f"T{i+1}", (c[0] - 105, c[1] + 95), layer=LY_LABEL[0]))

    # 手工固定的 5 组总线
    bus_specs = [
        {"center": (-955, -1010), "len": 1320, "side": -1},
        {"center": (-245, -315), "len": 1180, "side": -1},
        {"center": (455, 365), "len": 1020, "side": -1},
        {"center": (1165, 1055), "len": 1180, "side": 1},
        {"center": (1765, 1650), "len": 1320, "side": 1},
    ]
    readout_bus_anchors = [spec["center"] for spec in bus_specs]
    for g, spec in enumerate(bus_specs):
        bus_center = spec["center"]
        side = spec["side"]
        half_len = spec["len"] / 2
        p1 = addp(bus_center, mul(u, -half_len))
        p2 = addp(bus_center, mul(u, half_len))
        _route([p1, p2], cpw_w=18, cpw_gap=8)
        q_group = qubits[g * 4:(g + 1) * 4]
        for j, q in enumerate(q_group):
            tap = addp(bus_center, mul(u, -365 + j * 245))
            side_pin = q["pins"]["lower"] if side < 0 else q["pins"]["upper"]
            nominal_len = REFERENCE_20BIT_RESONATOR_MM[g * 4 + j] * 1000
            branch = [side_pin, addp(side_pin, mul(v, side * 165)), addp(tap, mul(v, -side * 120)), tap]
            _route(branch, cpw_w=9, cpw_gap=6)
            # 追加少量蛇形，体现不同谐振腔长度排序
            end_dir = mul(u, 1 if g % 2 == 0 else -1)
            meander_start = tap
            meander_end = addp(tap, mul(end_dir, min(420, max(180, nominal_len * 0.08))))
            _route(_zigzag_local(meander_start, meander_end, amp=20, turns=5), cpw_w=9, cpw_gap=6)

    # 48 pads around edges
    pads = []
    pad_margin = 430
    edge_margin = 960
    top_xs = [(-hx + edge_margin) + i * ((2 * (hx - edge_margin)) / 11) for i in range(12)]
    right_ys = [(hy - edge_margin) - i * ((2 * (hy - edge_margin)) / 11) for i in range(12)]
    bottom_xs = [(hx - edge_margin) - i * ((2 * (hx - edge_margin)) / 11) for i in range(12)]
    left_ys = [(-hy + edge_margin) + i * ((2 * (hy - edge_margin)) / 11) for i in range(12)]
    pad_no = 1
    for x in top_xs:
        pads.append({"id": pad_no, "pt": _launchpad(top, x, hy - pad_margin, "N"), "side": "top"})
        if with_labels:
            top.add(gdstk.Label(str(pad_no), (x, hy - 205), layer=LY_LABEL[0]))
        pad_no += 1
    for y in right_ys:
        pads.append({"id": pad_no, "pt": _launchpad(top, hx - pad_margin, y, "E"), "side": "right"})
        if with_labels:
            top.add(gdstk.Label(str(pad_no), (hx - 170, y), layer=LY_LABEL[0]))
        pad_no += 1
    for x in bottom_xs:
        pads.append({"id": pad_no, "pt": _launchpad(top, x, -hy + pad_margin, "S"), "side": "bottom"})
        if with_labels:
            top.add(gdstk.Label(str(pad_no), (x, -hy + 165), layer=LY_LABEL[0]))
        pad_no += 1
    for y in left_ys:
        pads.append({"id": pad_no, "pt": _launchpad(top, -hx + pad_margin, y, "W"), "side": "left"})
        if with_labels:
            top.add(gdstk.Label(str(pad_no), (-hx + 160, y), layer=LY_LABEL[0]))
        pad_no += 1

    # 手工导引点：四边各自局部汇聚，不穿越中心
    top_guides = [(-2620 + i * 240, 2250 - i * 115) for i in range(12)]
    right_guides = [(2270 - i * 120, 2440 - i * 220) for i in range(12)]
    bottom_guides = [(2280 - i * 240, -2250 + i * 115) for i in range(12)]
    left_guides = [(-2280 + i * 120, -2440 + i * 220) for i in range(12)]

    # pad -> guide 先形成四束平行线
    for i, pad in enumerate(pads[0:12]):
        guide = top_guides[i]
        _route([pad["pt"], (pad["pt"][0], hy - 1300), guide], cpw_w=10, cpw_gap=6)
    for i, pad in enumerate(pads[12:24]):
        guide = right_guides[i]
        _route([pad["pt"], (hx - 1300, pad["pt"][1]), guide], cpw_w=10, cpw_gap=6)
    for i, pad in enumerate(pads[24:36]):
        guide = bottom_guides[i]
        _route([pad["pt"], (pad["pt"][0], -hy + 1300), guide], cpw_w=10, cpw_gap=6)
    for i, pad in enumerate(pads[36:48]):
        guide = left_guides[i]
        _route([pad["pt"], (-hx + 1300, pad["pt"][1]), guide], cpw_w=10, cpw_gap=6)

    # 四边各自使用固定模板目标点，避免全部缠绕到中心
    top_targets = [
        (-2050, 1320), (-1780, 1260), (-1510, 1200), (-1240, 1140),
        (-260, 1680), (40, 1620), (340, 1560), (640, 1500),
        (930, 1440), (1220, 1380), (1510, 1320), (1800, 1260),
    ]
    right_targets = [
        (2050, 1650), (1920, 1460), (1790, 1270), (1660, 1080),
        (1530, 890), (1400, 700), (1270, 510), (1140, 320),
        (1010, 130), (880, -60), (750, -250), (620, -440),
    ]
    bottom_targets = [
        (1740, -1680), (1480, -1620), (1220, -1560), (960, -1500),
        (700, -1440), (440, -1380), (180, -1320), (-80, -1260),
        (-340, -1200), (-600, -1140), (-860, -1080), (-1120, -1020),
    ]
    left_targets = [
        (-2040, -1620), (-1910, -1430), (-1780, -1240), (-1650, -1050),
        (-1520, -860), (-1390, -670), (-1260, -480), (-1130, -290),
        (-1000, -100), (-870, 90), (-740, 280), (-610, 470),
    ]

    for guide, target in zip(top_guides, top_targets):
        _route([guide, (guide[0], target[1]), target], cpw_w=9, cpw_gap=6)
    for guide, target in zip(right_guides, right_targets):
        _route([guide, (target[0], guide[1]), target], cpw_w=9, cpw_gap=6)
    for guide, target in zip(bottom_guides, bottom_targets):
        _route([guide, (guide[0], target[1]), target], cpw_w=9, cpw_gap=6)
    for guide, target in zip(left_guides, left_targets):
        _route([guide, (target[0], guide[1]), target], cpw_w=9, cpw_gap=6)

    # 少量局部短连接，把模板目标点连接到实际器件/总线附近
    local_links = [
        (top_targets[0], (qubits[15]["center"][0] + 120, qubits[15]["center"][1] + 120)),
        (top_targets[1], (qubits[16]["center"][0] + 120, qubits[16]["center"][1] + 120)),
        (top_targets[2], (qubits[17]["center"][0] + 120, qubits[17]["center"][1] + 120)),
        (top_targets[3], (qubits[18]["center"][0] + 120, qubits[18]["center"][1] + 120)),
        (top_targets[8], addp(readout_bus_anchors[4], mul(u, -580))),
        (top_targets[9], addp(readout_bus_anchors[4], mul(u, 580))),
        (right_targets[0], (qubits[19]["center"][0] + 120, qubits[19]["center"][1] + 120)),
        (right_targets[1], (coupler_points[18][0] + 70, coupler_points[18][1] + 100)),
        (right_targets[4], (qubits[14]["center"][0] + 120, qubits[14]["center"][1] + 120)),
        (right_targets[8], addp(readout_bus_anchors[3], mul(u, 520))),
        (bottom_targets[0], addp(readout_bus_anchors[0], mul(u, 580))),
        (bottom_targets[1], addp(readout_bus_anchors[0], mul(u, -580))),
        (bottom_targets[4], (qubits[4]["center"][0] - 120, qubits[4]["center"][1] - 120)),
        (bottom_targets[8], (qubits[0]["center"][0] - 120, qubits[0]["center"][1] - 120)),
        (left_targets[0], (coupler_points[0][0] - 70, coupler_points[0][1] + 100)),
        (left_targets[1], (qubits[1]["center"][0] - 120, qubits[1]["center"][1] - 120)),
        (left_targets[4], (qubits[5]["center"][0] - 120, qubits[5]["center"][1] - 120)),
        (left_targets[8], addp(readout_bus_anchors[1], mul(u, -520))),
    ]
    for p1, p2 in local_links:
        _route([p1, p2], cpw_w=8, cpw_gap=5)

    lib.write_gds(filename)
    return filename
