# -*- coding: utf-8 -*-

# This code is customized by Bin Yang
#
# (C) Copyright 量子科技长三角产业创新中心 2024.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import math
from qiskit_metal.qlibrary.user_components.my_qcomponent import MyCoupledLineTee
from qiskit_metal import Dict
from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder


def get_launchpad_data(n_width, n_height, spacing, length, width, angle_deg):
    """
    计算长方形四条边上 launchpad 的坐标及朝向角度

    参数:
      n_width:   长度边（上下边）上的 pad 个数
      n_height:  宽度边（左右边）上的 pad 个数
      spacing:   设定的 pad 间距
      length:    长方形的长度
      width:     长方形的宽度
      angle_deg: 长方形整体旋转角度

    返回:
      [(x, y, angle), ...] 列表
    """

    # 1. 间距校验逻辑（取设定值与物理最大值的较小者）
    max_spacing_l = length / (n_width - 1) if n_width > 1 else 0
    actual_spacing_l = min(spacing, max_spacing_l)

    max_spacing_w = width / (n_height - 1) if n_height > 1 else 0
    actual_spacing_w = min(spacing, max_spacing_w)

    results = []

    # 预计算旋转矩阵所需的数值
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    # 辅助函数：旋转坐标并计算最终角度
    def add_pad(raw_x, raw_y, base_angle):
        # 坐标旋转 (标准 2D 旋转公式)
        rot_x = raw_x * cos_a - raw_y * sin_a
        rot_y = raw_x * sin_a + raw_y * cos_a

        # 角度计算：基础角度 + 旋转角度，并归一化到 0-360 范围
        # 注意：用户定义的 -90 会在这里自动处理 (例如 -90 % 360 = 270)
        final_angle = (base_angle + angle_deg) % 360

        results.append((round(rot_x, 4), round(rot_y, 4), round(final_angle, 2)))

    # --- 坐标生成 (以中心 0,0 为基准) ---

    # 1. 左边 (Left Side)
    # 位置: x = -length/2
    # 设定朝向: 0度
    w_start = -(actual_spacing_w * (n_height - 1)) / 2
    l_start = -(actual_spacing_l * (n_width - 1)) / 2
    for j in range(n_height):
        curr_x = -length / 2
        curr_y = w_start + j * actual_spacing_w
        add_pad(curr_x, curr_y, 0)  # 用户指定: 左边为 0

    # 2. 上边 (Top Side)
    # 位置: y = width/2
    # 设定朝向: -90度
    for i in range(n_width):
        curr_x = l_start + i * actual_spacing_l
        curr_y = width / 2
        add_pad(curr_x, curr_y, -90)  # 用户指定: 上边为 -90

    # 3. 右边 (Right Side)
    # 位置: x = length/2
    # 设定朝向: 180度
    for j in range(n_height):
        curr_x = length / 2
        curr_y = w_start + (n_height - 1) * actual_spacing_w - j * actual_spacing_w
        add_pad(curr_x, curr_y, 180)  # 用户指定: 右边为 180

    # 4. 下边 (Bottom Side)
    # 位置: y = -width/2
    # 设定朝向: 90度
    for i in range(n_width):
        curr_x = l_start + (n_width - 1) * actual_spacing_l - i * actual_spacing_l
        curr_y = -width / 2
        add_pad(curr_x, curr_y, 90)  # 用户指定: 下边为 90
    return results


def insert_tees_with_pathfinder(design, bus_prefix, start_pin_dict, end_pin_dict, tee_data, jogs_start=None,
                                jogs_end=None):
    """
    在 Bus 上插入多个 CoupledLineTee，使用 RoutePathfinder 连接，并支持自定义引脚方向逻辑和 Jog 引导。

    参数:
        design: QDesign 对象
        bus_prefix: 组件命名前缀 (str)
        start_pin_dict: 总线起始引脚字典 {'component': name, 'pin': name}
        end_pin_dict: 总线结束引脚字典 {'component': name, 'pin': name}
        tee_data: 数据列表，格式 [(pos_x, pos_y, orientation, coupling_space, mirror), ...]
                  注意: pos_x/y 为数字(mm), orientation 为度数(int/float)
        jogs_start: 第一段线起始处的引导参数 (OrderedDict 或 dict), 传递给 RoutePathfinder 的 lead
        jogs_end: 最后一段线结束处的引导参数 (OrderedDict 或 dict), 传递给 RoutePathfinder 的 lead
    """

    tees = []

    # --- 1. 辅助函数：根据 Orientation 决定输入/输出引脚 ---
    def get_io_pins(orientation):
        """
        根据用户规则：
        - Orientation 0 (Tee往下): 左边是 prime_start (In), 右边是 prime_end (Out)
        - Orientation 180 (Tee往上): 左边是 prime_end (In), 右边是 prime_start (Out)
        假设总线流向是从左到右。
        """
        # 归一化角度处理 (防止输入 360, -180 等)
        norm_orient = float(orientation) % 360

        if norm_orient == 0:
            return 'prime_start', 'prime_end'
        elif norm_orient == 180:
            return 'prime_end', 'prime_start'
        else:
            # 如果有 90 或 270 的情况，默认回退到 0 的逻辑，或者在此扩展
            print(f"Warning: Orientation {orientation} not strictly 0 or 180, using default flow.")
            return 'prime_start', 'prime_end'

    # --- 2. 生成所有 Tee 组件 ---
    for i, data in enumerate(tee_data):
        # 解包数据
        pos_x, pos_y, orientation, coupling_space, over_length, mirror = data

        # 构建组件名称
        tee_name = f"{bus_prefix}{i}"

        # 构造 options 字典
        # 注意：mirror 参数在 CoupledLineTee 标准库中通常不作为直接参数，
        # 这里假设 mirror 控制 down_length 的方向或者你需要存入 options 供后续使用。
        # 如果是标准库，我们主要设置 pos, orientation, coupling_space
        options = Dict(
            pos_x=f"{pos_x}mm",
            pos_y=f"{pos_y}mm",
            orientation=str(orientation),
            coupling_length=f"{coupling_space}um",
            over_length=f"{over_length}um",
            mirror=mirror
        )

        # 实例化组件
        tee = MyCoupledLineTee(design, tee_name, options=options)
        tees.append(tee)

    # --- 3. 逐段连接 (RoutePathfinder) ---

    # --- 第一段：Start Pin -> Tee[0] Input ---
    first_tee = tees[0]
    first_tee_orient = tee_data[0][2]  # 获取第一个 tee 的 orientation

    # 动态获取第一个 Tee 的输入引脚
    t0_in_pin, _ = get_io_pins(first_tee_orient)

    RoutePathfinder(design, f"{bus_prefix}_seg_start", options=Dict(
        pin_inputs=Dict(
            start_pin=start_pin_dict,
            end_pin=Dict(component=first_tee.name, pin=t0_in_pin)
        ),
        # 应用第一段的 jog 引导
        lead=Dict(
            start_jogged_extension=jogs_start if jogs_start else {}
        )
    ))

    # --- 中间段：Tee[i] Output -> Tee[i+1] Input ---
    for i in range(len(tees) - 1):
        curr_tee = tees[i]
        next_tee = tees[i + 1]

        curr_orient = tee_data[i][2]
        next_orient = tee_data[i + 1][2]

        # 获取当前 Tee 的输出引脚 和 下一个 Tee 的输入引脚
        _, curr_out_pin = get_io_pins(curr_orient)
        next_in_pin, _ = get_io_pins(next_orient)

        RoutePathfinder(design, f"{bus_prefix}_seg_{i}", options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(component=curr_tee.name, pin=curr_out_pin),
                end_pin=Dict(component=next_tee.name, pin=next_in_pin)
            )
            # 中间段通常不需要特殊的 start/end jogs，除非有特殊需求
        ))

    # --- 最后一段：Tee[-1] Output -> End Pin ---
    last_tee = tees[-1]
    last_tee_orient = tee_data[-1][2]

    # 动态获取最后一个 Tee 的输出引脚
    _, last_out_pin = get_io_pins(last_tee_orient)

    RoutePathfinder(design, f"{bus_prefix}_seg_end", options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(component=last_tee.name, pin=last_out_pin),
            end_pin=end_pin_dict
        ),
        # 应用最后一段的 jog 引导
        lead=Dict(
            end_jogged_extension=jogs_end if jogs_end else {}
        )
    ))
    return tees
