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

from qiskit_metal import draw, Dict, designs, MetalGUI
from qiskit_metal.qlibrary.user_components.my_qcomponent import *
from qiskit_metal.qlibrary.user_components.airbridge import AirbridgeGenerator
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder
from qiskit_metal.qlibrary.user_components.stable_meander import StableRouteMeander
from qiskit_metal.qlibrary.user_components.chip_function import *
from collections import OrderedDict
from qiskit_metal.qlibrary.user_components.save_load import *
from qiskit_metal.qlibrary.user_components.reader import *
import re
import numpy as np


def resonator_layout(coupling_length_list=[200, 200, 200, 200, 200, 120, 120, 120, 120],
                     resonator_length_list=[4.3423, 4.2699, 4.1996, 4.0657, 4.1316, 4.1, 4.02, 3.94, 3.86]):
    design = designs.DesignPlanar()
    design.chips['main']['material'] = 'sapphire'
    design.chips.main.size['size_x'] = '10mm'
    design.chips.main.size['size_y'] = '10mm'
    design.chips['main']['size']['sample_holder_top'] = '500um'
    design.chips['main']['size']['sample_holder_bottom'] = '500um'
    design.chips['main']['size']['size_z'] = '-500um'
    design.variables.cpw_gap = '5um'
    gui = MetalGUI(design)

    design.delete_all_components()

    opt1 = Dict(pos_x='-3.88mm', pos_y=0, orientation='0', pad_width='245 um', pad_height='245 um', pad_gap='100 um',
                lead_length='176 um', )
    launch_zline1 = LaunchpadWirebond(design, 'launch_zline1', options=opt1)

    # opt2 = Dict(pos_x='3.88mm', pos_y=0, orientation='180', )
    opt2 = Dict(pos_x='3.88mm', pos_y=0, orientation='180', pad_width='245 um', pad_height='245 um', pad_gap='100 um',
                lead_length='176 um', )
    launch_zline2 = LaunchpadWirebond(design, 'launch_zline2', options=opt2)

    shift = 0.054
    rr_space1 = 0.317
    shift1 = 0.6
    ql_distance = 1.65
    qq_space = 1
    qpos_x = 0
    qpos_y = -1.65
    TQ_coupling_length = coupling_length_list

    TQ1 = CoupledLineTee(design,
                         'TQ1',
                         options=Dict(pos_x=shift, pos_y='0mm',
                                      orientation='0',
                                      coupling_length=str(TQ_coupling_length[0]) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ2 = CoupledLineTee(design,
                         'TQ2',
                         options=Dict(pos_x=-2 * qq_space + shift, pos_y='0mm',
                                      orientation='0',
                                      coupling_length=str(TQ_coupling_length[1]) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ3 = CoupledLineTee(design,
                         'TQ3',
                         options=Dict(pos_x=2 * qq_space + shift, pos_y='0mm',
                                      orientation='0',
                                      coupling_length=str(TQ_coupling_length[2]) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ4 = CoupledLineTee(design,
                         'TQ4',
                         options=Dict(pos_x=-qq_space - shift, pos_y='0mm',
                                      orientation='180',
                                      coupling_length=str(TQ_coupling_length[3]) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ5 = CoupledLineTee(design,
                         'TQ5',
                         options=Dict(pos_x=qq_space - shift, pos_y='0mm',
                                      orientation='180',
                                      coupling_length=str(TQ_coupling_length[4]) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    TQ6 = CoupledLineTee(design,
                         'TQ6',
                         options=Dict(pos_x=-2 * qq_space - shift1, pos_y='0mm',
                                      orientation='180',
                                      coupling_length=str(TQ_coupling_length[5]) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    TQ7 = CoupledLineTee(design,
                         'TQ7',
                         options=Dict(pos_x=-2 * qq_space - 2 * shift1, pos_y='0mm',
                                      orientation='180',
                                      coupling_length=str(TQ_coupling_length[6]) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    TQ8 = CoupledLineTee(design,
                         'TQ8',
                         options=Dict(pos_x=2 * qq_space + shift1, pos_y='0mm',
                                      orientation='180',
                                      coupling_length=str(TQ_coupling_length[7]) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    TQ9 = CoupledLineTee(design,
                         'TQ9',
                         options=Dict(pos_x=2 * qq_space + 2 * shift1, pos_y='0mm',
                                      orientation='180',
                                      coupling_length=str(TQ_coupling_length[8]) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    ops_oL = Dict(hfss_wire_bonds=False,
                  pin_inputs=Dict(start_pin=Dict(component='launch_zline1',
                                                 pin='tie'),
                                  end_pin=Dict(component='TQ7', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_openLeft = RouteStraight(design, 'cpw_openLeft', options=ops_oL)

    ops_1 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ7', pin='prime_start'),
                                 end_pin=Dict(component='TQ6', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_1 = RouteStraight(design, 'cpw_1', options=ops_1)

    ops_2 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ6', pin='prime_start'),
                                 end_pin=Dict(component='TQ2', pin='prime_start')), trace_width='10um', trace_gap='5um')
    cpw_2 = RouteStraight(design, 'cpw_2', options=ops_2)

    ops_3 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ2', pin='prime_end'),
                                 end_pin=Dict(component='TQ4', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_3 = RouteStraight(design, 'cpw_3', options=ops_3)

    ops_4 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ4', pin='prime_start'),
                                 end_pin=Dict(component='TQ1', pin='prime_start')), trace_width='10um', trace_gap='5um')
    cpw_4 = RouteStraight(design, 'cpw_4', options=ops_4)

    ops_5 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ1', pin='prime_end'),
                                 end_pin=Dict(component='TQ5', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_5 = RouteStraight(design, 'cpw_5', options=ops_5)

    ops_6 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ5', pin='prime_start'),
                                 end_pin=Dict(component='TQ3', pin='prime_start')), trace_width='10um', trace_gap='5um')
    cpw_6 = RouteStraight(design, 'cpw_6', options=ops_6)

    ops_7 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ3', pin='prime_end'),
                                 end_pin=Dict(component='TQ8', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_7 = RouteStraight(design, 'cpw_7', options=ops_7)

    ops_8 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ8', pin='prime_start'),
                                 end_pin=Dict(component='TQ9', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_8 = RouteStraight(design, 'cpw_8', options=ops_8)

    ops_oR = Dict(hfss_wire_bonds=False,
                  pin_inputs=Dict(start_pin=Dict(component='launch_zline2', pin='tie'),
                                  end_pin=Dict(component='TQ9', pin='prime_start')), trace_width='10um',
                  trace_gap='5um')
    cpw_openRight = RouteStraight(design, 'cpw_openRight', options=ops_oR)

    # draw spare resonator for Q factor test purpose
    # shift_r is the distance between x position of beginning vertical part of resonator and last vertical part of resonator
    # draw resonator
    jogsS = OrderedDict()
    jogsS[0] = ["R", '0um']

    spacing = 0.1
    ops = dict(fillet=spacing / 2 - 0.001)
    asymmetry = 0
    start_straight = 0.13
    TQ_y = 1.4

    shift_r = design.components['TQ1'].get_pin('second_end').middle[0]
    pos_start_x_TQ5 = design.components['TQ5'].get_pin('second_end').middle[0] + shift_r
    pos_start_y_TQ5 = TQ_y
    total_length = resonator_length_list

    for i in range(1, 10):
        if i not in [1, 2, 3]:
            OpenToGround(design, 'otg_TQ' + str(i) + '_start',
                         options=Dict(pos_x=design.components['TQ' + str(i)].get_pin('second_end').middle[0] + shift_r,
                                      pos_y=TQ_y, width='10um', gap='5um', orientation='90', ))
            options = Dict(total_length=str(total_length[i - 1]),
                           hfss_wire_bonds=False,
                           pin_inputs=Dict(end_pin=Dict(component='TQ' + str(i),
                                                        pin='second_end'),
                                           start_pin=Dict(component='otg_TQ' + str(i) + '_start', pin='open')),
                           lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                           meander=Dict(spacing=spacing, asymmetry=asymmetry),
                           **ops)
            RouteMeander(design, 'meander' + str(i), options=options)
        else:
            OpenToGround(design, 'otg_TQ' + str(i) + '_start',
                         options=Dict(pos_x=design.components['TQ' + str(i)].get_pin('second_end').middle[0] - shift_r,
                                      pos_y=-TQ_y, width='10um', gap='5um', orientation='-90', ))
            options = Dict(total_length=str(total_length[i - 1]),
                           hfss_wire_bonds=False,
                           pin_inputs=Dict(end_pin=Dict(component='TQ' + str(i),
                                                        pin='second_end'),
                                           start_pin=Dict(component='otg_TQ' + str(i) + '_start', pin='open')),
                           lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                           meander=Dict(spacing=spacing, asymmetry=asymmetry),
                           **ops)
            RouteMeander(design, 'meander' + str(i), options=options)

    gui.rebuild()
    gui.autoscale()
    return design, gui


def update_derived_variables_v1(design):
    """
    更新 resonator_layout_v1 中的派生变量。
    当修改基础变量（如 chip_size, cut_size, pad_width 等）后，
    调用此函数重新计算派生变量，然后再调用 gui.rebuild()。
    
    使用示例:
        design.variables.chip_size = '8mm'
        design.variables.pad_width = '0.3mm'
        update_derived_variables_v1(design)
        gui.rebuild()
        gui.autoscale()
    """
    # 解析基础变量
    chip_size_val = design.parse_value('chip_size')
    cut_size_val = design.parse_value('cut_size')
    pad_width_val = design.parse_value('pad_width')
    taper_height_val = design.parse_value('taper_height')
    pad_gap_val = design.parse_value('pad_gap')
    resonator_num = int(design.parse_value('resonator_num'))
    meander_spacing_val = design.parse_value('meander_spacing')
    TQ_y_val = design.parse_value('TQ_y')
    
    # 重新计算派生变量
    res = pad_width_val + taper_height_val + pad_gap_val
    pos_x = (chip_size_val - cut_size_val - res * 2) / 2
    rr_space = 2 * (pos_x - 0.535) / (resonator_num - 1) if resonator_num > 1 else 0
    
    # 更新派生变量到 design.variables
    design.variables.launchpad_pos_x = f'{pos_x}mm'
    design.variables.neg_launchpad_pos_x = f'{-pos_x}mm'
    design.variables.rr_space = f'{rr_space}mm'
    design.variables.meander_fillet = f'{meander_spacing_val / 2 - 0.001}mm'
    design.variables.version_pos_x = f'{0.95 * pos_x}mm'
    design.variables.version_pos_y = f'{-0.9 * pos_x}mm'
    
    # 更新 Tee 位置变量
    for i in range(resonator_num):
        tee_pos_x = (-(resonator_num - 1) / 2 + i) * rr_space
        design.variables[f'tee_pos_x_{i}'] = f'{tee_pos_x}mm'
        design.variables[f'tee_pos_y_{i}'] = '0mm'
        
        # 获取该 Tee 的 coupling_length (需要从组件中获取或存储)
        coupling_len_var = f'coupling_length_{i}'
        if coupling_len_var in design.variables:
            coupling_len = design.parse_value(coupling_len_var) * 1000  # mm to um
        else:
            coupling_len = 200  # 默认值 um
        shift_r = coupling_len / 2000  # um to mm
        
        # 根据方向计算 OpenToGround 位置
        orientation = 0 if i % 2 == 0 else 180
        if orientation == 180:
            otg_pos_x = tee_pos_x + shift_r
            otg_pos_y = TQ_y_val
        else:
            otg_pos_x = tee_pos_x - shift_r
            otg_pos_y = -TQ_y_val
        
        design.variables[f'otg_pos_x_{i}'] = f'{otg_pos_x}mm'
        design.variables[f'otg_pos_y_{i}'] = f'{otg_pos_y}mm'
    
    return pos_x, rr_space


def resonator_layout_v1(coupling_length_list, resonator_length_list, resonator_num=5, chip_size=6, version='1.0'):
    """
    谐振腔版图函数，所有组件位置参数使用 design.variables 变量引用，支持 rebuild 后更新。
    
    参数:
        coupling_length_list: 耦合长度列表 (um)
        resonator_length_list: 谐振腔长度列表 (mm)
        resonator_num: 谐振腔数量，默认为5
        chip_size: 芯片尺寸 (mm)，默认为6
        version: 版本号字符串，默认为 '1.0'
    
    返回:
        design, gui, update_func: 设计对象、GUI对象和更新派生变量的函数
        
    使用示例:
        design, gui, update_func = resonator_layout_v1(...)
        
        # 修改变量后更新
        design.variables.chip_size = '8mm'
        design.variables.pad_width = '0.3mm'
        update_func(design)  # 重新计算派生变量
        gui.rebuild()
        gui.autoscale()
    """
    # ===== 1. 初始化设计 =====
    design = designs.DesignPlanar()
    design.chips['main']['material'] = 'sapphire'
    design.chips.main.size['size_x'] = f'{chip_size}mm'
    design.chips.main.size['size_y'] = f'{chip_size}mm'
    design.chips['main']['size']['sample_holder_top'] = '500um'
    design.chips['main']['size']['sample_holder_bottom'] = '500um'
    design.chips['main']['size']['size_z'] = '-500um'
    gui = MetalGUI(design)
    design.delete_all_components()

    # ===== 2. 将设计参数存入 design.variables =====
    # 芯片基本参数
    design.variables.chip_size = f'{chip_size}mm'
    design.variables.cut_size = '0.5mm'
    design.variables.resonator_num = str(resonator_num)
    
    # Launchpad 参数
    design.variables.pad_width = '0.245mm'
    design.variables.pad_height = '0.245mm'
    design.variables.pad_gap = '0.1mm'
    design.variables.lead_length = '0.176mm'
    design.variables.taper_height = '0.122mm'
    
    # CPW 参数
    design.variables.cpw_width = '10um'
    design.variables.cpw_gap = '5um'
    design.variables.coupling_space = '3um'
    design.variables.over_length = '100um'
    
    # 谐振腔参数
    design.variables.meander_spacing = '0.1mm'
    design.variables.meander_asymmetry = '0mm'
    design.variables.start_straight = '0.13mm'
    design.variables.TQ_y = '1.4mm'
    
    # 存储每个谐振腔的耦合长度和总长度变量
    for i in range(resonator_num):
        design.variables[f'coupling_length_{i}'] = f'{coupling_length_list[i]}um'
        design.variables[f'resonator_length_{i}'] = f'{resonator_length_list[i]}mm'
    
    # ===== 3. 计算并更新派生变量 =====
    pos_x, rr_space = update_derived_variables_v1(design)
    
    # ===== 4. 创建 Launchpad =====
    launch_pad_name = 'launch_zline'
    
    # 创建左侧 Launchpad - 使用字符串变量名引用
    opt1 = Dict(
        pos_x='neg_launchpad_pos_x', 
        pos_y='0mm', 
        orientation='0', 
        pad_width='pad_width',
        pad_height='pad_height', 
        pad_gap='pad_gap',
        taper_height='taper_height', 
        lead_length='lead_length'
    )
    LaunchpadWirebond(design, f'{launch_pad_name}1', options=opt1)

    # 创建右侧 Launchpad
    opt2 = Dict(
        pos_x='launchpad_pos_x', 
        pos_y='0mm', 
        orientation='180', 
        pad_width='pad_width',
        pad_height='pad_height', 
        pad_gap='pad_gap',
        taper_height='taper_height', 
        lead_length='lead_length'
    )
    LaunchpadWirebond(design, f'{launch_pad_name}2', options=opt2)

    # ===== 5. 添加版本号组件 =====
    if version != '0.00':
        digits = [int(char) for char in version if char.isdigit()]
        number = digits[0]
        decimal1 = digits[1]
        decimal2 = digits[2] if len(digits) > 2 else 0
        options = {
            'orientation': '0',
            'number': number,
            'decimal1': decimal1,
            'decimal2': decimal2,
            'width': '20um',
            'height': '100um',
            'pos_x': 'version_pos_x',
            'pos_y': 'version_pos_y',
            'spacing': '30um',
        }
        NumberComponent(design, name='number1', options=options)

    # ===== 6. 直接创建 Tee 组件（使用变量引用） =====
    tee_name = 'TQ'
    tees = []
    
    def get_io_pins(orientation):
        """根据 orientation 获取输入/输出引脚"""
        norm_orient = float(orientation) % 360
        if norm_orient == 0:
            return 'prime_start', 'prime_end'
        elif norm_orient == 180:
            return 'prime_end', 'prime_start'
        else:
            return 'prime_start', 'prime_end'
    
    for i in range(resonator_num):
        orientation = 0 if i % 2 == 0 else 180
        # 使用变量引用创建 Tee
        tee_options = Dict(
            pos_x=f'tee_pos_x_{i}',  # 变量引用
            pos_y=f'tee_pos_y_{i}',  # 变量引用
            orientation=str(orientation),
            coupling_length=f'coupling_length_{i}',  # 变量引用
            coupling_space='coupling_space',  # 变量引用
            prime_width='cpw_width',  # 变量引用
            prime_gap='cpw_gap',  # 变量引用
            second_width='cpw_width',  # 变量引用
            second_gap='cpw_gap',  # 变量引用
            over_length='over_length',  # 变量引用
            open_termination=False,
            mirror=False
        )
        tee = MyCoupledLineTee(design, f'{tee_name}{i}', options=tee_options)
        tees.append(tee)
    
    # ===== 7. 使用 RoutePathfinder 连接 Tee =====
    # 第一段：Launchpad1 -> Tee0
    first_orient = 0  # 第一个 Tee 方向
    t0_in_pin, _ = get_io_pins(first_orient)
    RoutePathfinder(design, f'{tee_name}_seg_start', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(component=f'{launch_pad_name}1', pin='tie'),
            end_pin=Dict(component=f'{tee_name}0', pin=t0_in_pin)
        )
    ))
    
    # 中间段：Tee[i] -> Tee[i+1]
    for i in range(resonator_num - 1):
        curr_orient = 0 if i % 2 == 0 else 180
        next_orient = 0 if (i + 1) % 2 == 0 else 180
        _, curr_out_pin = get_io_pins(curr_orient)
        next_in_pin, _ = get_io_pins(next_orient)
        RoutePathfinder(design, f'{tee_name}_seg_{i}', options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(component=f'{tee_name}{i}', pin=curr_out_pin),
                end_pin=Dict(component=f'{tee_name}{i + 1}', pin=next_in_pin)
            )
        ))
    
    # 最后一段：Tee[-1] -> Launchpad2
    last_orient = 0 if (resonator_num - 1) % 2 == 0 else 180
    _, last_out_pin = get_io_pins(last_orient)
    RoutePathfinder(design, f'{tee_name}_seg_end', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(component=f'{tee_name}{resonator_num - 1}', pin=last_out_pin),
            end_pin=Dict(component=f'{launch_pad_name}2', pin='tie')
        )
    ))

    # ===== 8. 绘制谐振腔 (OpenToGround + RouteMeander) =====
    jogsS = OrderedDict()
    jogsS[0] = ["R", '0um']
    open_to_ground_name = 'otg_TQ'

    for i in range(resonator_num):
        orientation = 0 if i % 2 == 0 else 180
        otg_orient = '90' if orientation == 180 else '-90'
        
        # 使用变量引用创建 OpenToGround
        OpenToGround(design, f'{open_to_ground_name}{i}',
                     options=Dict(
                         pos_x=f'otg_pos_x_{i}',  # 变量引用
                         pos_y=f'otg_pos_y_{i}',  # 变量引用
                         width='cpw_width',  # 变量引用
                         gap='cpw_gap',  # 变量引用
                         orientation=otg_orient
                     ))
        
        # RouteMeander 使用变量引用
        meander_options = Dict(
            total_length=f'resonator_length_{i}',  # 变量引用
            hfss_wire_bonds=False,
            pin_inputs=Dict(
                end_pin=Dict(component=f'{tee_name}{i}', pin='second_end'),
                start_pin=Dict(component=f'{open_to_ground_name}{i}', pin='open')
            ),
            lead=Dict(start_straight='start_straight', start_jogged_extension=jogsS),
            meander=Dict(spacing='meander_spacing', asymmetry='meander_asymmetry'),
            fillet='meander_fillet'
        )
        RouteMeander(design, f'meander{i}', options=meander_options)

    gui.rebuild()
    gui.autoscale()
    return design, gui, update_derived_variables_v1


def small_single_qubit_layout(parameter_file_path=None,jj_dict=None, version='1.00'):
    """"
    含有5个比特和9个谐振腔的单比特版图，其中4个谐振腔为测试用途
    Default Options:
        * jj_dict: {'Q1':'FakeJunction_01','Q2':'FakeJunction_01'}- 每个比特的约瑟夫森结组成的字典
    """
    if jj_dict is None:
        jj_dict = {'Q1': 'FakeJunction_01', 'Q2': 'FakeJunction_02', 'Q3': 'FakeJunction_03', 'Q4': 'FakeJunction_04',
                   'Q5': 'FakeJunction_05', }
    design = designs.DesignPlanar()
    design.chips['main']['material'] = 'sapphire'
    design.chips.main.size['size_x'] = '6mm'
    design.chips.main.size['size_y'] = '6mm'
    design.chips['main']['size']['sample_holder_top'] = '500um'
    design.chips['main']['size']['sample_holder_bottom'] = '500um'
    design.chips['main']['size']['size_z'] = '-500um'
    design.variables.cpw_gap = '5um'
    gui = MetalGUI(design)

    chip_size = 6
    cut_size = 0.5
    pad_width = 0.245
    pad_height = 0.245
    pad_gap = 0.1
    lead_length = 0.176
    taper_height = 0.122
    res = pad_width + taper_height + pad_gap
    pos_x = (chip_size - cut_size - res * 2) / 2
    launch_pad_name = 'launch_zline'
    digits = [int(char) for char in version if char.isdigit()]
    number = digits[0]
    decimal1 = digits[1]
    decimal2 = digits[2]
    opt1 = Dict(pos_x=str(-pos_x) + 'mm', pos_y=0, orientation='0', pad_width=str(pad_width) + 'mm',
                pad_height=str(pad_height) + 'mm', pad_gap=str(pad_gap) + 'mm',
                taper_height=str(taper_height) + 'mm', lead_length=str(lead_length) + 'mm', )
    LaunchpadWirebond(design, launch_pad_name + str(1), options=opt1)

    opt2 = Dict(pos_x=str(pos_x) + 'mm', pos_y=0, orientation='180', pad_width=str(pad_width) + 'mm',
                pad_height=str(pad_height) + 'mm', pad_gap=str(pad_gap) + 'mm',
                taper_height=str(taper_height) + 'mm', lead_length=str(lead_length) + 'mm', )
    LaunchpadWirebond(design, launch_pad_name + str(2), options=opt2)

    if version != '0.00':
        options = {
            'number': number,
            'decimal1': decimal1,
            'decimal2': decimal2,
            'width': '20um',  # 笔画宽度
            'height': '100um',  # 数字高度
            'pos_x': str(0.95*pos_x)+'mm',
            'pos_y': str(-1.19*pos_x)+'mm',
            'spacing': '30um',
        }
        NumberComponent(design, name='number1', options=options)

    # draw transmon qubit
    ql_distance = 1.65
    qq_space = 0.60
    qpos_x = 0
    qpos_y = -1.65
    transmon_options = dict(
        pos_x=f'{qpos_x}mm',
        pos_y=f'{qpos_y}mm',
        orientation='0',
        pad_gap='80um',
        inductor_width='20um',
        pad_width='530um',
        pad_height='150um',
        pad_fillet='8um',
        pocket_width='800um',
        pocket_height='600um',
        pocket_fillet='100um',
        coupled_pad_height='50um',
        coupled_pad_width='20um',
        coupled_pad_gap='80um',
        connection_pads=dict(
            readout=dict(
                pad_gap='30um',
                pad_width='20um',
                pad_height='25um',
                pad_cpw_shift='0um',
                pad_cpw_extent='25um',
                cpw_width='10um',
                cpw_gap='5um',
                cpw_extend='20um',
                pocket_extent='5um',
                pocket_rise='0um',
                loc_W=0, loc_H=1),
        ),
        gds_cell_name=jj_dict['Q1'], )

    transmon = TransmonPocketRoundTeeth(design, 'Q1', options=transmon_options)

    design.copy_qcomponent(transmon, 'Q2', Dict(pos_x=-2 * qq_space, pos_y=-ql_distance))
    design.copy_qcomponent(transmon, 'Q3', Dict(pos_x=2 * qq_space, pos_y=-ql_distance))
    design.copy_qcomponent(transmon, 'Q4', Dict(pos_x=-qq_space, pos_y=ql_distance))
    design.copy_qcomponent(transmon, 'Q5', Dict(pos_x=qq_space, pos_y=ql_distance))
    design.components['Q4'].options.orientation = '180'
    design.components['Q5'].options.orientation = '180'
    design.components['Q2'].options.gds_cell_name = jj_dict['Q2']
    design.components['Q3'].options.gds_cell_name = jj_dict['Q3']
    design.components['Q4'].options.gds_cell_name = jj_dict['Q4']
    design.components['Q5'].options.gds_cell_name = jj_dict['Q5']

    # draw read line and coupledLineTee
    shift = -0.1
    rr_space1 = 0.317
    shift1 = 0.35
    # rr_space2 = 0.574

    TQ1 = CoupledLineTee(design,
                         'TQ1',
                         options=Dict(pos_x=shift, pos_y='0mm',
                                      orientation='0',
                                      coupling_length='200um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ2 = CoupledLineTee(design,
                         'TQ2',
                         options=Dict(pos_x=-2 * qq_space + shift, pos_y='0mm',
                                      orientation='0',
                                      coupling_length='200um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ3 = CoupledLineTee(design,
                         'TQ3',
                         options=Dict(pos_x=2 * qq_space + shift, pos_y='0mm',
                                      orientation='0',
                                      coupling_length='200um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ4 = CoupledLineTee(design,
                         'TQ4',
                         options=Dict(pos_x=-qq_space - shift, pos_y='0mm',
                                      orientation='180',
                                      coupling_length='200um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ5 = CoupledLineTee(design,
                         'TQ5',
                         options=Dict(pos_x=qq_space - shift, pos_y='0mm',
                                      orientation='180',
                                      coupling_length='200um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ6 = CoupledLineTee(design,
                         'TQ6',
                         options=Dict(pos_x=2 * qq_space + shift + shift1, pos_y='0mm',
                                      orientation='180',
                                      coupling_length='40um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ7 = CoupledLineTee(design,
                         'TQ7',
                         options=Dict(pos_x= -2 * qq_space + shift - shift1, pos_y='0mm',
                                      orientation='180',
                                      coupling_length='40um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    ops_oL = Dict(hfss_wire_bonds=False,
                  pin_inputs=Dict(start_pin=Dict(component='launch_zline1',
                                                 pin='tie'),
                                  end_pin=Dict(component='TQ7', pin='prime_end')), trace_width='10um',
                  trace_gap='5um')
    cpw_openLeft = RouteStraight(design, 'cpw_openLeft', options=ops_oL)

    ops_1 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ7', pin='prime_start'),
                                 end_pin=Dict(component='TQ2', pin='prime_start')), trace_width='10um', trace_gap='5um')
    cpw_1 = RouteStraight(design, 'cpw_1', options=ops_1)

    ops_3 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ2', pin='prime_end'),
                                 end_pin=Dict(component='TQ4', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_3 = RouteStraight(design, 'cpw_3', options=ops_3)

    ops_4 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ4', pin='prime_start'),
                                 end_pin=Dict(component='TQ1', pin='prime_start')), trace_width='10um', trace_gap='5um')
    cpw_4 = RouteStraight(design, 'cpw_4', options=ops_4)

    ops_5 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ1', pin='prime_end'),
                                 end_pin=Dict(component='TQ5', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_5 = RouteStraight(design, 'cpw_5', options=ops_5)

    ops_6 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ5', pin='prime_start'),
                                 end_pin=Dict(component='TQ3', pin='prime_start')), trace_width='10um', trace_gap='5um')
    cpw_6 = RouteStraight(design, 'cpw_6', options=ops_6)

    ops_2 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ3', pin='prime_end'),
                                 end_pin=Dict(component='TQ6', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_2 = RouteStraight(design, 'cpw_2', options=ops_2)

    ops_oR = Dict(hfss_wire_bonds=False,
                  pin_inputs=Dict(end_pin=Dict(component='launch_zline2', pin='tie'),
                                  start_pin=Dict(component='TQ6', pin='prime_start')), trace_width='10um',
                  trace_gap='5um')
    cpw_openRight = RouteStraight(design, 'cpw_openRight', options=ops_oR)

    # draw resonator
    jogsS = OrderedDict()
    jogsS[0] = ["R", '0um']

    spacing = 0.1
    ops = dict(fillet=spacing / 2 - 0.001)
    # asymmetry = 0
    start_straight = 0.13
    open_to_ground_name = 'otg_TQ'
    TQ_y = 1.18

    options1 = Dict(total_length='4.3423mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ1',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q1', pin='readout')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing),
                    **ops)
    StableRouteMeander(design, 'meanderQ1', options=options1)

    options2 = Dict(total_length='4.2699mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ2',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q2', pin='readout')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing),
                    **ops)
    StableRouteMeander(design, 'meanderQ2', options=options2)

    options3 = Dict(total_length='4.1996mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ3',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q3', pin='readout')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing),
                    **ops)
    StableRouteMeander(design, 'meanderQ3', options=options3)

    options4 = Dict(total_length='4.0657mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ4',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q4', pin='readout')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing),
                    **ops)
    StableRouteMeander(design, 'meanderQ4', options=options4)

    options5 = Dict(total_length='4.1316mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ5',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q5', pin='readout')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing),
                    **ops)
    StableRouteMeander(design, 'meanderQ5', options=options5)

    OpenToGround(design, open_to_ground_name + str(1),
                 options=Dict(
                     pos_x=design.components['TQ' + str(6)].get_pin('second_end').middle[0],
                     pos_y=TQ_y, width='10um', gap='5um', orientation='90', ))

    options6 = Dict(total_length='4.218mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ6',
                                                 pin='second_end'),
                                    start_pin=Dict(component=open_to_ground_name + str(1), pin='open')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing),
                    **ops)
    StableRouteMeander(design, 'meanderQ6', options=options6)

    OpenToGround(design, open_to_ground_name + str(2),
                 options=Dict(
                     pos_x=design.components['TQ' + str(7)].get_pin('second_end').middle[0],
                     pos_y=TQ_y, width='10um', gap='5um', orientation='90', ))

    options7 = Dict(total_length='4.468mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ7',
                                                 pin='second_end'),
                                    start_pin=Dict(component=open_to_ground_name + str(2), pin='open')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, ),
                    **ops)
    StableRouteMeander(design, 'meanderQ7', options=options7)

    if parameter_file_path is not None:
        parameter_import(design, convert_keys_to_int(load_json(parameter_file_path)))
    gui.rebuild()
    gui.autoscale()
    return design, gui


def single_qubit_layout(jj_dict: dict):
    """"
    含有5个比特和9个谐振腔的单比特版图，其中4个谐振腔为测试用途
    Default Options:
        * jj_dict: {'Q1':'FakeJunction_01','Q2':'FakeJunction_01'}- 每个比特的约瑟夫森结组成的字典
    """
    design = designs.DesignPlanar()
    design.chips['main']['material'] = 'sapphire'
    design.chips.main.size['size_x'] = '10mm'
    design.chips.main.size['size_y'] = '10mm'
    design.chips['main']['size']['sample_holder_top'] = '500um'
    design.chips['main']['size']['sample_holder_bottom'] = '500um'
    design.chips['main']['size']['size_z'] = '-500um'
    design.variables.cpw_gap = '5um'
    gui = MetalGUI(design)
    # opt1 = Dict(pos_x='-3.88mm', pos_y=0, orientation='0', )
    opt1 = Dict(pos_x='-3.88mm', pos_y=0, orientation='0', pad_width='245 um', pad_height='245 um', pad_gap='100 um',
                lead_length='176 um', )
    launch_zline1 = LaunchpadWirebond(design, 'launch_zline1', options=opt1)

    # opt2 = Dict(pos_x='3.88mm', pos_y=0, orientation='180', )
    opt2 = Dict(pos_x='3.88mm', pos_y=0, orientation='180', pad_width='245 um', pad_height='245 um', pad_gap='100 um',
                lead_length='176 um', )
    launch_zline2 = LaunchpadWirebond(design, 'launch_zline2', options=opt2)

    # draw transmon qubit
    ql_distance = 1.65
    qq_space = 1
    qpos_x = 0
    qpos_y = -1.65
    transmon_options = dict(
        pos_x=qpos_x,
        pos_y=qpos_y,
        orientation='0',
        pad_gap='40um',
        inductor_width='20um',
        pad_width='815um',
        pad_height='150um',
        pad_fillet='8um',
        pocket_width='1025um',
        pocket_height='900um',
        pocket_fillet='100um',
        coupled_pad_height='100um',
        coupled_pad_width='16.3um',
        coupled_pad_gap='20um',
        connection_pads=dict(
            readout=dict(
                pad_gap='10um',
                pad_width='16.7um',
                pad_height='170um',
                pad_cpw_shift='0um',
                pad_cpw_extent='25um',
                cpw_width='10um',
                cpw_gap='5um',
                cpw_extend='20um',
                pocket_extent='5um',
                pocket_rise='0um',
                loc_W=0, loc_H=1),
        ),
        gds_cell_name=jj_dict['Q1'], )

    transmon = TransmonPocketRoundTeeth(design, 'Q1', options=transmon_options)

    design.copy_qcomponent(transmon, 'Q2', Dict(pos_x=-2 * qq_space, pos_y=-ql_distance))
    design.copy_qcomponent(transmon, 'Q3', Dict(pos_x=2 * qq_space, pos_y=-ql_distance))
    design.copy_qcomponent(transmon, 'Q4', Dict(pos_x=-qq_space, pos_y=ql_distance))
    design.copy_qcomponent(transmon, 'Q5', Dict(pos_x=qq_space, pos_y=ql_distance))
    design.components['Q4'].options.orientation = '180'
    design.components['Q5'].options.orientation = '180'

    design.copy_qcomponent(transmon, 'Q6', Dict(pos_x=-3 * qq_space, pos_y=-2 * ql_distance))
    design.copy_qcomponent(transmon, 'Q7', Dict(pos_x=3 * qq_space, pos_y=-2 * ql_distance))
    design.copy_qcomponent(transmon, 'Q8', Dict(pos_x=qq_space, pos_y=-2 * ql_distance))
    design.copy_qcomponent(transmon, 'Q9', Dict(pos_x=-qq_space, pos_y=-2 * ql_distance))

    design.components['Q2'].options.gds_cell_name = jj_dict['Q2']
    design.components['Q3'].options.gds_cell_name = jj_dict['Q3']
    design.components['Q4'].options.gds_cell_name = jj_dict['Q4']
    design.components['Q5'].options.gds_cell_name = jj_dict['Q5']
    design.components['Q6'].options.gds_cell_name = jj_dict['Q6']
    design.components['Q7'].options.gds_cell_name = jj_dict['Q7']
    design.components['Q8'].options.gds_cell_name = jj_dict['Q8']
    design.components['Q9'].options.gds_cell_name = jj_dict['Q9']

    # design.components['Q5'].options.gds_cell_name = 'FakeJunction_03_r'
    # design.components['Q6'].options.gds_cell_name = 'FakeJunction_01'
    # design.components['Q7'].options.gds_cell_name = 'FakeJunction_02'
    # design.components['Q8'].options.gds_cell_name = 'FakeJunction_05'
    # design.components['Q9'].options.gds_cell_name = 'my_other_junction'
    # if same_freq is True:
    #     design.components['Q2'].options.gds_cell_name = 'FakeJunction_04'
    #     design.components['Q4'].options.gds_cell_name = 'FakeJunction_04_r'

    gui.rebuild()

    # draw read line and coupledLineTee
    shift = 0.054
    rr_space1 = 0.317
    shift1 = 0.6
    # rr_space2 = 0.574

    TQ1 = CoupledLineTee(design,
                         'TQ1',
                         options=Dict(pos_x=shift, pos_y='0mm',
                                      orientation='0',
                                      coupling_length='200um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ2 = CoupledLineTee(design,
                         'TQ2',
                         options=Dict(pos_x=-2 * qq_space + shift, pos_y='0mm',
                                      orientation='0',
                                      coupling_length='200um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ3 = CoupledLineTee(design,
                         'TQ3',
                         options=Dict(pos_x=2 * qq_space + shift, pos_y='0mm',
                                      orientation='0',
                                      coupling_length='200um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ4 = CoupledLineTee(design,
                         'TQ4',
                         options=Dict(pos_x=-qq_space - shift, pos_y='0mm',
                                      orientation='180',
                                      coupling_length='200um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ5 = CoupledLineTee(design,
                         'TQ5',
                         options=Dict(pos_x=qq_space - shift, pos_y='0mm',
                                      orientation='180',
                                      coupling_length='200um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    TQ6 = CoupledLineTee(design,
                         'TQ6',
                         options=Dict(pos_x=-2 * qq_space - shift1, pos_y='0mm',
                                      orientation='180',
                                      coupling_length='120um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    TQ7 = CoupledLineTee(design,
                         'TQ7',
                         options=Dict(pos_x=-2 * qq_space - 2 * shift1, pos_y='0mm',
                                      orientation='180',
                                      coupling_length='120um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    TQ8 = CoupledLineTee(design,
                         'TQ8',
                         options=Dict(pos_x=2 * qq_space + shift1, pos_y='0mm',
                                      orientation='180',
                                      coupling_length='120um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    TQ9 = CoupledLineTee(design,
                         'TQ9',
                         options=Dict(pos_x=2 * qq_space + 2 * shift1, pos_y='0mm',
                                      orientation='180',
                                      coupling_length='120um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    ops_oL = Dict(hfss_wire_bonds=False,
                  pin_inputs=Dict(start_pin=Dict(component='launch_zline1',
                                                 pin='tie'),
                                  end_pin=Dict(component='TQ7', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_openLeft = RouteStraight(design, 'cpw_openLeft', options=ops_oL)

    ops_1 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ7', pin='prime_start'),
                                 end_pin=Dict(component='TQ6', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_1 = RouteStraight(design, 'cpw_1', options=ops_1)

    ops_2 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ6', pin='prime_start'),
                                 end_pin=Dict(component='TQ2', pin='prime_start')), trace_width='10um', trace_gap='5um')
    cpw_2 = RouteStraight(design, 'cpw_2', options=ops_2)

    ops_3 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ2', pin='prime_end'),
                                 end_pin=Dict(component='TQ4', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_3 = RouteStraight(design, 'cpw_3', options=ops_3)

    ops_4 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ4', pin='prime_start'),
                                 end_pin=Dict(component='TQ1', pin='prime_start')), trace_width='10um', trace_gap='5um')
    cpw_4 = RouteStraight(design, 'cpw_4', options=ops_4)

    ops_5 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ1', pin='prime_end'),
                                 end_pin=Dict(component='TQ5', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_5 = RouteStraight(design, 'cpw_5', options=ops_5)

    ops_6 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ5', pin='prime_start'),
                                 end_pin=Dict(component='TQ3', pin='prime_start')), trace_width='10um', trace_gap='5um')
    cpw_6 = RouteStraight(design, 'cpw_6', options=ops_6)

    ops_7 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ3', pin='prime_end'),
                                 end_pin=Dict(component='TQ8', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_7 = RouteStraight(design, 'cpw_7', options=ops_7)

    ops_8 = Dict(hfss_wire_bonds=False,
                 pin_inputs=Dict(start_pin=Dict(component='TQ8', pin='prime_start'),
                                 end_pin=Dict(component='TQ9', pin='prime_end')), trace_width='10um', trace_gap='5um')
    cpw_8 = RouteStraight(design, 'cpw_8', options=ops_8)

    ops_oR = Dict(hfss_wire_bonds=False,
                  pin_inputs=Dict(start_pin=Dict(component='launch_zline2', pin='tie'),
                                  end_pin=Dict(component='TQ9', pin='prime_start')), trace_width='10um',
                  trace_gap='5um')
    cpw_openRight = RouteStraight(design, 'cpw_openRight', options=ops_oR)

    # draw resonator
    jogsS = OrderedDict()
    jogsS[0] = ["R", '0um']

    spacing = 0.1
    ops = dict(fillet=spacing / 2 - 0.001)
    asymmetry = 0
    start_straight = 0.13

    options1 = Dict(total_length='4.3423mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ1',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q1', pin='readout')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meanderQ1 = RouteMeander(design, 'meanderQ1', options=options1)

    options2 = Dict(total_length='4.2699mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ2',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q2', pin='readout')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meanderQ2 = RouteMeander(design, 'meanderQ2', options=options2)

    options3 = Dict(total_length='4.1996mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ3',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q3', pin='readout')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meanderQ3 = RouteMeander(design, 'meanderQ3', options=options3)

    options4 = Dict(total_length='4.0657mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ4',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q4', pin='readout')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meanderQ4 = RouteMeander(design, 'meanderQ4', options=options4)

    options5 = Dict(total_length='4.1316mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ5',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q5', pin='readout')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meanderQ5 = RouteMeander(design, 'meanderQ5', options=options5)

    # draw spare resonator for Q factor test purpose
    # shift_r is the distance between x position of beginning vertical part of resonator and last vertical part of resonator
    shift_r = design.components['TQ1'].get_pin('second_end').middle[0] - design.components['Q1'].parse_options().pos_x
    pos_start_x_TQ6 = design.components['TQ6'].get_pin('second_end').middle[0] + shift_r
    pos_start_y_TQ6 = design.components['Q5'].get_pin('readout').middle[1]
    # short pin for test resonator
    otg_TQ6_start = OpenToGround(design, 'otg_TQ6_start',
                                 options=Dict(pos_x=pos_start_x_TQ6, pos_y=pos_start_y_TQ6, width='10um', gap='5um',
                                              orientation='90', ))
    options6 = Dict(total_length='4.1mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ6',
                                                 pin='second_end'),
                                    start_pin=Dict(component='otg_TQ6_start', pin='open')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meanderQ6 = RouteMeander(design, 'meanderQ6', options=options6)

    pos_start_x_TQ7 = design.components['TQ7'].get_pin('second_end').middle[0] + shift_r
    pos_start_y_TQ7 = design.components['Q5'].get_pin('readout').middle[1]
    otg_TQ7_start = OpenToGround(design, 'otg_TQ7_start',
                                 options=Dict(pos_x=pos_start_x_TQ7, pos_y=pos_start_y_TQ7, width='10um', gap='5um',
                                              orientation='90', ))
    options7 = Dict(total_length='4.02mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ7',
                                                 pin='second_end'),
                                    start_pin=Dict(component='otg_TQ7_start', pin='open')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meanderQ7 = RouteMeander(design, 'meanderQ7', options=options7)

    pos_start_x_TQ8 = design.components['TQ8'].get_pin('second_end').middle[0] + shift_r
    pos_start_y_TQ8 = design.components['Q5'].get_pin('readout').middle[1]
    otg_TQ8_start = OpenToGround(design, 'otg_TQ8_start',
                                 options=Dict(pos_x=pos_start_x_TQ8, pos_y=pos_start_y_TQ8, width='10um', gap='5um',
                                              orientation='90', ))
    options8 = Dict(total_length='3.94mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ8',
                                                 pin='second_end'),
                                    start_pin=Dict(component='otg_TQ8_start', pin='open')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meanderQ8 = RouteMeander(design, 'meanderQ8', options=options8)

    pos_start_x_TQ9 = design.components['TQ9'].get_pin('second_end').middle[0] + shift_r
    pos_start_y_TQ9 = design.components['Q5'].get_pin('readout').middle[1]
    otg_TQ9_start = OpenToGround(design, 'otg_TQ9_start',
                                 options=Dict(pos_x=pos_start_x_TQ9, pos_y=pos_start_y_TQ9, width='10um', gap='5um',
                                              orientation='90', ))
    options9 = Dict(total_length='3.86mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ9',
                                                 pin='second_end'),
                                    start_pin=Dict(component='otg_TQ9_start', pin='open')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meanderQ9 = RouteMeander(design, 'meanderQ9', options=options9)
    gui.rebuild()
    return design, gui


def large_single_qubit_layout(jj_dict=None, parameter_file_path=None, airbridge=False, version='1.00'):
    # define chip parameter
    design = designs.DesignPlanar()
    design.chips.main.size['size_x'] = '12.5mm'
    design.chips.main.size['size_y'] = '12.5mm'
    design.variables.cpw_gap = '5um'
    gui = MetalGUI(design)
    design.overwrite_enabled = True

    # 引脚pad绘制
    chip_size = 12.5
    cut_length = 0.3
    cut_spacing = 0.3
    launchpad_num_each_side = 12
    launchpad_spacing = 0.76
    launchpad_width = 250
    launchpad_height = launchpad_width
    launchpad_gap = 100
    launchpad_taper = 122
    layout_length = layout_width = (chip_size - cut_length - 2 * cut_spacing
                                    - 2 * (launchpad_width + launchpad_taper + launchpad_gap) * 1e-3)

    launchpad_data = get_launchpad_data(n_width=launchpad_num_each_side, n_height=launchpad_num_each_side,
                                        spacing=launchpad_spacing, length=layout_length, width=layout_width,
                                        angle_deg=0)
    for i in range(len(launchpad_data)):
        opt = Dict(pos_x=f'{launchpad_data[i][0]} mm', pos_y=f'{launchpad_data[i][1]} mm',
                   orientation=f'{launchpad_data[i][2]}',
                   pad_width=f'{launchpad_width} um', pad_height=f'{launchpad_height} um',
                   pad_gap=f'{launchpad_gap} um', taper_height=f'{launchpad_taper} um',
                   lead_length='67 um', chip='main', trace_width='10 um', trace_gap='5 um')
        LaunchpadWirebond(design, f'launch_line{i}', options=opt)

    # Tee绘制
    start_pin_dict1 = {'component': 'launch_line9', 'pin': 'tie'}
    end_pin_dict1 = {'component': 'launch_line26', 'pin': 'tie'}
    pos_y1 = design.components['launch_line9'].parse_options().pos_y
    qq_space = 1.2
    tee_data = [(-3.7 * qq_space, pos_y1, 180, 40,100,False), (-2.7 * qq_space, pos_y1, 180, 40, 100,False),
                (-2 * qq_space, pos_y1, 0, 224, 100,False), (-qq_space, pos_y1, 180, 224,100, False),
                (0, pos_y1, 0, 224,100, False),
                (qq_space, pos_y1, 180, 224,100, False), (2 * qq_space, pos_y1, 0, 224, 100,False),
                (2.7 * qq_space, pos_y1, 180, 40, 100,True), (3.7 * qq_space, pos_y1, 180, 40, 100,True)]
    insert_tees_with_pathfinder(design, 'TQ', start_pin_dict=start_pin_dict1, end_pin_dict=end_pin_dict1,
                                tee_data=tee_data)

    start_pin_dict2 = {'component': 'launch_line2', 'pin': 'tie'}
    end_pin_dict2 = {'component': 'launch_line33', 'pin': 'tie'}
    pos_y2 = design.components['launch_line2'].parse_options().pos_y
    tee_data = [(-3.7 * qq_space, pos_y2, 180, 40, 100,False), (-2.7 * qq_space, pos_y2, 180, 40, 100,False),
                (-2 * qq_space, pos_y2, 0, 224, 300,False), (-qq_space, pos_y2, 180, 224, 100,False),
                (0, pos_y2, 0, 224, 100,False),
                (qq_space, pos_y2, 180, 224,100, False), (2 * qq_space, pos_y2, 0, 224, 100,False),
                (2.7 * qq_space, pos_y2, 180, 40, 100,True), (3.7 * qq_space, pos_y2, 180, 40, 100,True)]
    insert_tees_with_pathfinder(design, 'TQ_prime', start_pin_dict=start_pin_dict2, end_pin_dict=end_pin_dict2,
                                tee_data=tee_data)

    # 比特绘制
    ql_distance = 1.18
    transmon_options = Dict(
        pos_x=f'{-2 * qq_space}mm',
        pos_y=f'{pos_y1 - ql_distance}mm',
        orientation='0',
        pad_gap='80um',
        inductor_width='20um',
        pad_width='530um',
        pad_height='150um',
        pad_fillet='8um',
        pocket_width='800um',
        pocket_height='600um',
        pocket_fillet='100um',
        coupled_pad_height='50um',
        coupled_pad_width='20um',
        coupled_pad_gap='42um',
        connection_pads=dict(
            readout=dict(
                pad_gap='30um',
                pad_width='22um',
                pad_height='40um',
                pad_cpw_shift='0um',
                pad_cpw_extent='25um',
                cpw_width='10um',
                cpw_gap='5um',
                cpw_extend='20um',
                pocket_extent='5um',
                pocket_rise='0um',
                loc_W=0, loc_H=1),
        ))
    transmon = TransmonPocketRoundTeeth(design, 'Q1', options=transmon_options)
    design.copy_qcomponent(transmon, 'Q2', Dict(pos_x=f'{-qq_space}mm', pos_y=f'{pos_y1 + ql_distance}mm'))
    design.copy_qcomponent(transmon, 'Q3', Dict(pos_x=f'{0}mm', pos_y=f'{pos_y1 - ql_distance}mm'))
    design.copy_qcomponent(transmon, 'Q4', Dict(pos_x=f'{qq_space}mm', pos_y=f'{pos_y1 + ql_distance}mm'))
    design.copy_qcomponent(transmon, 'Q5', Dict(pos_x=f'{2 * qq_space}mm', pos_y=f'{pos_y1 - ql_distance}mm'))
    transmon_options = Dict(
        pos_x=f'{-2 * qq_space}mm',
        pos_y=f'{pos_y2 - ql_distance}mm',
        orientation='0',
        pad_gap='80um',
        inductor_width='20um',
        pad_width='530um',
        pad_height='150um',
        pad_fillet='8um',
        pocket_width='800um',
        pocket_height='600um',
        pocket_fillet='100um',
        coupled_pad_height='60um',
        coupled_pad_width='20um',
        coupled_pad_gap='45um',
        connection_pads=dict(
            readout=dict(
                pad_gap='15um',
                pad_width='22um',
                pad_height='82um',
                pad_cpw_shift='0um',
                pad_cpw_extent='25um',
                cpw_width='10um',
                cpw_gap='5um',
                cpw_extend='20um',
                pocket_extent='5um',
                pocket_rise='0um',
                loc_W=0, loc_H=1),
        ))
    transmon = TransmonPocketRoundTeeth(design, 'Q6', options=transmon_options)
    # design.copy_qcomponent(transmon, 'Q6', Dict(pos_x=f'{-2 * qq_space}mm', pos_y=f'{pos_y2 - ql_distance}mm'))
    design.copy_qcomponent(transmon, 'Q7', Dict(pos_x=f'{-qq_space}mm', pos_y=f'{pos_y2 + ql_distance}mm'))
    design.copy_qcomponent(transmon, 'Q8', Dict(pos_x=f'{0}mm', pos_y=f'{pos_y2 - ql_distance}mm'))
    design.copy_qcomponent(transmon, 'Q9', Dict(pos_x=f'{qq_space}mm', pos_y=f'{pos_y2 + ql_distance}mm'))
    design.copy_qcomponent(transmon, 'Q10', Dict(pos_x=f'{2 * qq_space}mm', pos_y=f'{pos_y2 - ql_distance}mm'))
    design.components['Q2'].options.orientation = '180'
    design.components['Q4'].options.orientation = '180'
    design.components['Q7'].options.orientation = '180'
    design.components['Q9'].options.orientation = '180'

    # 谐振腔绘制
    spacing = 0.1
    ops = dict(fillet=spacing / 2 - 0.001)
    TQ_list = ['TQ2', 'TQ3', 'TQ4', 'TQ5', 'TQ6', 'TQ_prime2', 'TQ_prime3', 'TQ_prime4', 'TQ_prime5', 'TQ_prime6']
    Q_meander_length = [4.444, 4.40765, 4.37157, 4.3358, 4.300, 4.444, 4.40765, 4.37157, 4.3358, 4.300]
    for i, TQ in enumerate(TQ_list):
        options = Dict(total_length=f'{Q_meander_length[i]}mm',
                       hfss_wire_bonds=False,
                       pin_inputs=Dict(end_pin=Dict(component=TQ,
                                                    pin='second_end'),
                                       start_pin=Dict(component=f'Q{i + 1}', pin='readout')),
                       lead=Dict(start_straight='100um'),
                       meander=Dict(spacing=spacing),
                       **ops)
        StableRouteMeander(design, f'meanderQ{i+1}', options=options)

    TR_list = ['TQ0', 'TQ1', 'TQ7', 'TQ8', 'TQ_prime0', 'TQ_prime1', 'TQ_prime7', 'TQ_prime8']
    R_meander_length = [4.45134004, 4.2591667, 4.19900125, 4.140782, 4.084509, 4.444, 4.0301822, 3.97780156, 3.9273671]
    for i, TR in enumerate(TR_list):
        if i < 4:
            OpenToGround(design, f'Otg{i}',
                         options=Dict(
                             pos_x=design.components[TR].parse_options().pos_x,
                             pos_y=design.components['launch_line9'].parse_options().pos_y + 1, width='10um', gap='5um',
                             orientation='90', ))
        else:
            OpenToGround(design, f'Otg{i}',
                         options=Dict(
                             pos_x=design.components[TR].parse_options().pos_x,
                             pos_y=design.components['launch_line2'].parse_options().pos_y + 1, width='10um', gap='5um',
                             orientation='90', ))
        options = Dict(total_length=f'{R_meander_length[i]}mm',
                       hfss_wire_bonds=False,
                       pin_inputs=Dict(end_pin=Dict(component=TR,
                                                    pin='second_end'),
                                       start_pin=Dict(component=f'Otg{i}', pin='open')),
                       lead=Dict(start_straight='100um'),
                       meander=Dict(spacing=spacing),
                       **ops)
        StableRouteMeander(design, f'meanderR{i+1}', options=options)
    if parameter_file_path is not None:
        parameter_import(design, convert_keys_to_int(load_json(parameter_file_path)))

    if jj_dict is not None:
        for i in range(1,11):
            design.components[f'Q{i}'].options.gds_cell_name = jj_dict[f'Q{i}']
    gui.rebuild()
    gui.autoscale()
    return design, gui


def small_two_qubit_layout(jj_dict=None, parameter_file_path=None, airbridge=False, version='1.00'):
    """"
    含有一个可调耦合器双比特固定频率版图，可调耦合器均带有谐振腔
    Default Options:
        * jj_dict: {'Q1':'FakeJunction_01','Q2':'FakeJunction_01'}- 每个比特的约瑟夫森结组成的字典
    """
    if jj_dict is None:
        jj_dict = {'xmon_round1': 'FakeJunction_01', 'xmon_round2': 'FakeJunction_02',
                   'tunable_coupler1': 'FakeJunction_03'}
    design = designs.DesignPlanar()
    design.chips.main.size['size_x'] = '6mm'
    design.chips.main.size['size_y'] = '6mm'
    design.variables.cpw_gap = '5 um'
    design.chips['main']['material'] = 'sapphire'
    design.chips['main']['size']['sample_holder_top'] = '500um'
    design.chips['main']['size']['sample_holder_bottom'] = '500um'
    design.chips['main']['size']['size_z'] = '-500um'
    gui = MetalGUI(design)

    design.delete_all_components()
    chip_size = 6
    cut_size = 0.
    pad_width = 0.245
    pad_height = 0.245
    pad_gap = 0.1
    lead_length = 0.176
    taper_height = 0.122
    res = pad_width + taper_height + pad_gap
    pos_x = (chip_size - cut_size - res * 2) / 2
    pos_y = 0.49
    launch_pad_name = 'launchpad'
    digits = [int(char) for char in version if char.isdigit()]
    number = digits[0]
    decimal1 = digits[1]
    decimal2 = digits[2]

    # --------------------------------------绘制电极板----------------------------------------------------
    opt1 = Dict(pos_x=str(-pos_x * 2 / 3) + 'mm', pos_y=str(pos_x) + 'mm', orientation='-90',
                pad_width=str(pad_width) + 'mm',
                pad_height=str(pad_height) + 'mm', pad_gap=str(pad_gap) + 'mm',
                taper_height=str(taper_height) + 'mm', lead_length=str(lead_length) + 'mm', )
    LaunchpadWirebond(design, launch_pad_name + str(1), options=opt1)

    opt2 = Dict(pos_x=str(0) + 'mm', pos_y=str(pos_x) + 'mm', orientation='-90', pad_width=str(pad_width) + 'mm',
                pad_height=str(pad_height) + 'mm', pad_gap=str(pad_gap) + 'mm',
                taper_height=str(taper_height) + 'mm', lead_length=str(lead_length) + 'mm', )
    LaunchpadWirebond(design, launch_pad_name + str(2), options=opt2)

    opt3 = Dict(pos_x=str(pos_x * 2 / 3) + 'mm', pos_y=str(pos_x) + 'mm', orientation='-90',
                pad_width=str(pad_width) + 'mm',
                pad_height=str(pad_height) + 'mm', pad_gap=str(pad_gap) + 'mm',
                taper_height=str(taper_height) + 'mm', lead_length=str(lead_length) + 'mm', )
    LaunchpadWirebond(design, launch_pad_name + str(3), options=opt3)

    opt4 = Dict(pos_x=str(-pos_x) + 'mm', pos_y=str(pos_y) + 'mm', orientation='0', pad_width=str(pad_width) + 'mm',
                pad_height=str(pad_height) + 'mm', pad_gap=str(pad_gap) + 'mm',
                taper_height=str(taper_height) + 'mm', lead_length=str(lead_length) + 'mm', )
    LaunchpadWirebond(design, launch_pad_name + str(4), options=opt4)

    opt5 = Dict(pos_x=str(pos_x) + 'mm', pos_y=str(pos_y) + 'mm', orientation='180', pad_width=str(pad_width) + 'mm',
                pad_height=str(pad_height) + 'mm', pad_gap=str(pad_gap) + 'mm',
                taper_height=str(taper_height) + 'mm', lead_length=str(lead_length) + 'mm', )
    LaunchpadWirebond(design, launch_pad_name + str(5), options=opt5)

    if version != '0.00':
        options = {
            'number': number,
            'decimal1': decimal1,
            'decimal2': decimal2,
            'width': '20um',  # 笔画宽度
            'height': '100um',  # 数字高度
            'pos_x': str(0.95*pos_x)+'mm',
            'pos_y': str(-1.19*pos_x)+'mm',
            'spacing': '30um',
        }
        NumberComponent(design, name='number1', options=options)

    global_pos_y = 0
    cross_width = 16
    cross_gap = 16
    space = 400
    x_gap = 5
    y_gap = 5
    xmon_round1 = TransmonCrossRound_v1(design, 'xmon_round1',
                                        options=Dict(pos_x=str(-space / 2) + 'um', pos_y=str(global_pos_y) + 'um',
                                                     radius='1 um', cross_width=str(cross_width) + 'um',
                                                     cross_gap=str(cross_gap) + 'um',
                                                     rect_width=str(cross_width) + 'um', rect_height='0um',
                                                     connection_pads=dict(
                                                         bus_02=dict(claw_length='120um', ground_spacing='3um',
                                                                     claw_width='10um', claw_gap='5um',coupling_gap='5um',
                                                                     connector_location='-90'),
                                                         bus_01=dict(connector_location='90', connector_type='1',
                                                                     ground_spacing='4um', claw_width='4um',
                                                                     coupling_gap='2um')
                                                     )))
    xmon_round2 = TransmonCrossRound_v1(design, 'xmon_round2',
                                        options=Dict(pos_x=str(space / 2) + 'um', pos_y=str(global_pos_y) + 'um',
                                                     radius='1 um', cross_width=str(cross_width) + 'um',
                                                     cross_gap=str(cross_gap) + 'um',
                                                     rect_width=str(cross_width) + 'um', rect_height='0um',
                                                     connection_pads=dict(
                                                         bus_02=dict(claw_length='61um', ground_spacing='3um',
                                                                     claw_width='10um', claw_gap='5um',
                                                                     connector_location='180'),
                                                         bus_01=dict(connector_location='90', connector_type='1',
                                                                     ground_spacing='4um', claw_width='4um',
                                                                     coupling_gap='2um')
                                                     )))
    rc_gap = 3
    cq_gap = 2
    l_gap = 16
    cp_gap = 5
    l_width = 9
    a_height = 30
    t_l_ratio = 7
    c_width = space - 2 * (cross_gap + cq_gap + l_gap) - cross_width
    pos_y = -(cross_width / 2 + cross_gap + cq_gap + l_gap + l_width / 2)
    cp_arm_width = 2 * ((c_width - l_width) / 5 - l_width / 2 - l_gap - rc_gap - cp_gap)
    cp_arm_length = a_height - l_width / 2 + rc_gap - rc_gap

    options = Dict(pos_x='0um',
                   pos_y=str(pos_y + global_pos_y) + 'um',
                   orientation='180',
                   c_width=str(c_width) + 'um',
                   l_width=str(l_width) + 'um',
                   l_gap=str(l_gap) + 'um',
                   a_height=str(a_height) + 'um',
                   cp_height='15um',
                   cp_arm_length=str(cp_arm_length) + 'um',
                   cp_arm_width='5um',
                   cp_gap=str(cp_gap) + 'um',
                   cp_gspace='3um',
                   fl_width='4um',
                   fl_gap='2um',
                   fl_length='10um',
                   fl_ground='3um',
                   jj_pad_width='8um',
                   jj_pad_height='6um',
                   jj_etch_length='4um',
                   jj_etch_pad1_width='2um',
                   jj_etch_pad2_width='5um',
                   jj_sub_rect_width='100um',
                   jj_sub_rect_height='100um',
                   t_l_ratio=str(t_l_ratio))
    tunable_coupler = MyTunableCoupler03(design, 'tunable_coupler1', options=options)

    design.components['xmon_round1'].options.gds_cell_name = jj_dict['xmon_round1']
    design.components['xmon_round2'].options.gds_cell_name = jj_dict['xmon_round2']
    design.components['tunable_coupler1'].options.gds_cell_name = jj_dict['tunable_coupler1']

    # -------------------------------------绘制谐振腔中读取线耦合部分------------------------------------------
    TQ_pos_x = chip_size / 4
    TQ_pos_y = (global_pos_y - 140) * 1e-3
    coupling_length_qubit = 280
    down_length_qubit = 100
    coupling_length_coupler = 280
    down_length_coupler = 600

    TQ1 = CoupledLineTee(design,
                         'TQ1',
                         options=Dict(pos_x=str(-TQ_pos_x) + 'mm', pos_y=str(TQ_pos_y) + 'mm',
                                      orientation='90',
                                      coupling_length=str(coupling_length_qubit) + 'um',
                                      down_length=str(down_length_qubit) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))
    TQ2 = CoupledLineTee(design,
                         'TQ2',
                         options=Dict(pos_x=str(TQ_pos_x) + 'mm', pos_y=str(TQ_pos_y) + 'mm',
                                      orientation='-90',
                                      coupling_length=str(coupling_length_qubit) + 'um',
                                      down_length=str(down_length_qubit) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=True))
    TQ3 = CoupledLineTee(design,
                         'TQ3',
                         options=Dict(pos_x=str(0) + 'mm', pos_y=str(-chip_size / 4) + 'mm',
                                      orientation='180',
                                      coupling_length=str(coupling_length_coupler) + 'um',
                                      down_length=str(down_length_coupler) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    # # -------------------------------------------------------绘制谐振腔----------------------------------------------
    whole_length1 = 4.378768750777398 + 1.18
    whole_length2 = 4.378768750777398 + 1.18
    whole_length3 = 4.18
    whole_length4 = 4.378768750777398 + 1.18
    whole_length5 = 4.378768750777398 + 1.18
    whole_length6 = 4.18
    total_length1 = whole_length1 - (coupling_length_qubit + down_length_qubit) * 1e-3
    total_length2 = whole_length2 - (coupling_length_qubit + down_length_qubit) * 1e-3
    total_length3 = whole_length3 - (coupling_length_coupler + down_length_coupler) * 1e-3
    total_length4 = whole_length4 - (coupling_length_qubit + down_length_qubit) * 1e-3
    total_length5 = whole_length5 - (coupling_length_qubit + down_length_qubit) * 1e-3
    total_length6 = whole_length6 - (coupling_length_coupler + down_length_coupler) * 1e-3
    jogsS = OrderedDict()
    jogsS[0] = ["R", '0um']
    spacing = 0.1
    ops = dict(fillet=spacing / 2 - 0.001)
    asymmetry = 0
    start_straight = 0.13
    options1 = Dict(total_length=str(total_length1) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ1',
                                                 pin='second_end'),
                                    start_pin=Dict(component='xmon_round1', pin='bus_02')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander1 = RouteMeander(design, 'meander1', options=options1)

    jogsS = OrderedDict()
    jogsS[0] = ["L", '0um']
    options2 = Dict(total_length=str(total_length2) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ2',
                                                 pin='second_end'),
                                    start_pin=Dict(component='xmon_round2', pin='bus_02')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander2 = RouteMeander(design, 'meander2', options=options2)

    jogsS = OrderedDict()
    jogsS[0] = ["L", '0um']
    options3 = Dict(total_length=str(total_length3) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ3',
                                                 pin='second_end'),
                                    start_pin=Dict(component='tunable_coupler1', pin='Control')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander3 = RouteMeander(design, 'meander3', options=options3)
    #
    # # -----------------------------------------------绘制读取线---------------------------------------------------------
    fillet = 100
    pin_opt1 = Dict(pin_inputs=Dict(start_pin=Dict(component='launchpad4', pin='tie'),
                                    end_pin=Dict(component='TQ1', pin='prime_end'), ), lead=Dict(start_straight=0.01,
                                                                                                 end_straight=0.1, ),
                    fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout1_part1', options=pin_opt1)

    pin_opt2 = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ1', pin='prime_start'),
                                    end_pin=Dict(component='TQ3', pin='prime_end'), ), lead=Dict(start_straight=0.01,
                                                                                                 end_straight=0.1, ),
                    fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout1_part2', options=pin_opt2)

    pin_opt3 = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ3', pin='prime_start'),
                                    end_pin=Dict(component='TQ2', pin='prime_end'), ), lead=Dict(start_straight=0.01,
                                                                                                 end_straight=0.1, ),
                    fillet=str(fillet) + 'um', )
    RoutePathfinder(design, 'readout1_part3', options=pin_opt3)

    pin_opt4 = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ2', pin='prime_start'),
                                    end_pin=Dict(component='launchpad5', pin='tie'), ), lead=Dict(start_straight=0.01,
                                                                                                  end_straight=0.1, ),
                    fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout1_part4', options=pin_opt4)
    # --------------------------------------------------------绘制控制线---------------------------------------------------
    gap = 2
    xy_gap = 4
    reference_point_x1 = design.components['xmon_round1'].parse_options().pos_x
    reference_point_y1 = design.components['xmon_round1'].parse_options().pos_y + design.components[
        'xmon_round1'].parse_options().cross_length1 \
                         + design.components['xmon_round1'].parse_options().cross_gap + gap * 1e-3 + xy_gap * 1e-3

    reference_point_x2 = design.components['xmon_round2'].parse_options().pos_x
    reference_point_y2 = design.components['xmon_round2'].parse_options().pos_y + design.components[
        'xmon_round2'].parse_options().cross_length1 \
                         + design.components['xmon_round2'].parse_options().cross_gap + gap * 1e-3 + xy_gap * 1e-3

    connector_x1 = reference_point_x1 - 0.2
    connector_y1 = reference_point_y1 + 0.35
    connector1 = MyConnector(design, 'connector1',
                             options=Dict(pos_x=connector_x1, pos_y=connector_y1, width='4um', gap=str(gap) + 'um',
                                          width0='10um', gap0='5um', length='10um', orientation='-90'))
    connector_x2 = reference_point_x2 + 0.2
    connector_y2 = reference_point_y2 + 0.35
    connector2 = MyConnector(design, 'connector2',
                             options=Dict(pos_x=connector_x2, pos_y=connector_y2, width='4um', gap=str(gap) + 'um',
                                          width0='10um', gap0='5um', length='10um', orientation='-90'))
    connector_x3 = 0
    connector_y3 = connector_y2
    connector3 = MyConnector(design, 'connector3',
                             options=Dict(pos_x=connector_x3, pos_y=connector_y3, width='4um', gap=str(gap) + 'um',
                                          width0='10um', gap0='5um', length='10um', orientation='-90'))

    #
    opt1 = Dict(pin_inputs=Dict(start_pin=Dict(component='xmon_round1', pin='bus_01'),
                                end_pin=Dict(component='connector1', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
                                                                                                  end_straight=0.1),
                fillet=str(fillet) + 'um', trace_width='4um', trace_gap='2um')
    RoutePathfinder(design, 'xy1_part1', options=opt1)
    opt1 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector1', pin='c_pin_l'),
                                end_pin=Dict(component='launchpad1', pin='tie'), ), lead=Dict(start_straight=0.150,
                                                                                              end_straight=0.1),
                fillet=str(fillet) + 'um', trace_width='10um', trace_gap='5um')
    RoutePathfinder(design, 'xy1_part2', options=opt1)
    opt2 = Dict(pin_inputs=Dict(start_pin=Dict(component='xmon_round2', pin='bus_01'),
                                end_pin=Dict(component='connector2', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
                                                                                                  end_straight=0.1),
                fillet=str(fillet) + 'um', trace_width='4um', trace_gap='2um')
    RoutePathfinder(design, 'xy2_part1', options=opt2)
    opt2 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector2', pin='c_pin_l'),
                                end_pin=Dict(component='launchpad3', pin='tie'), ), lead=Dict(start_straight=0.150,
                                                                                              end_straight=0.1),
                fillet=str(fillet) + 'um', trace_width='10um', trace_gap='5um')
    RoutePathfinder(design, 'xy2_part2', options=opt2)
    opt3 = Dict(pin_inputs=Dict(start_pin=Dict(component='tunable_coupler1', pin='Flux'),
                                end_pin=Dict(component='connector3', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
                                                                                                  end_straight=0.1),
                fillet=str(fillet) + 'um', trace_width='4um', trace_gap='2um')
    RoutePathfinder(design, 'z1_part1', options=opt3)
    opt3 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector3', pin='c_pin_l'),
                                end_pin=Dict(component='launchpad2', pin='tie'), ), lead=Dict(start_straight=0.150,
                                                                                              end_straight=0.1),
                fillet=str(fillet) + 'um', trace_width='10um', trace_gap='5um')
    RoutePathfinder(design, 'z1_part2', options=opt3)
    if parameter_file_path is not None:
        parameter_import(design, convert_keys_to_int(load_json(parameter_file_path)))
        gui.rebuild()
        gui.autoscale()
    else:
        gui.rebuild()
        gui.autoscale()
    if airbridge is True:
        list0 = []
        list1 = []
        list2 = []
        for i in range(1, 4):
            list0.append(design.components['meander' + str(i)])
        for i in range(1, 5):
            list1.append(design.components['readout1_part' + str(i)])
        for i in range(1, 3):
            list2.append(design.components['xy' + str(i) + '_part2'])
        list2.append(design.components['z1_part2'])
        parameter_dict = Dict(pad_width='22 um', etch_residue='-2 um',
                              bridge_length='50um', pad_layer=3, etch_layer=4)
        build_airbridge(design, gui, list_meander=list0, list_controlLine=list2 + list1, parameter_dict=parameter_dict)
        # gui.rebuild()
    # gui.autoscale()
    return design, gui


# def two_qubit_layout(jj_dict=None):
#     """"
#     含有两个可调耦合器双比特固定频率版图，其中一个含有控制线，一个没有控制线。两个可调耦合器均带有谐振腔
#     Default Options:
#         * jj_dict: {'Q1':'FakeJunction_01','Q2':'FakeJunction_01'}- 每个比特的约瑟夫森结组成的字典
#     """
#     if jj_dict is None:
#         jj_dict = {'xmon_round1': 'FakeJunction_01', 'xmon_round2': 'FakeJunction_02', 'xmon_round3': 'FakeJunction_03', 'xmon_round4': 'FakeJunction_04',
#                    'tunable_coupler1': 'FakeJunction_05', 'tunable_coupler2': 'FakeJunction_06'}
#     design = designs.DesignPlanar()
#     design.chips.main.size['size_x'] = '10mm'
#     design.chips.main.size['size_y'] = '10mm'
#     design.variables.cpw_gap = '5 um'
#     design.chips['main']['material'] = 'sapphire'
#     design.chips['main']['size']['sample_holder_top'] = '500um'
#     design.chips['main']['size']['sample_holder_bottom'] = '500um'
#     design.chips['main']['size']['size_z'] = '-500um'
#     gui = MetalGUI(design)
#
#     global_pos_y = 2000
#     cross_width = 16
#     cross_gap = 16
#     space = 400
#     x_gap = 5
#     y_gap = 5
#     xmon_round1 = TransmonCrossRound_v1(design, 'xmon_round1',
#                                         options=Dict(pos_x=str(-space / 2) + 'um', pos_y=str(global_pos_y) + 'um',
#                                                      radius='1 um', cross_width=str(cross_width) + 'um',
#                                                      cross_gap=str(cross_gap) + 'um',
#                                                      rect_width=str(cross_width) + 'um', rect_height='0um',
#                                                      connection_pads=dict(
#                                                          bus_02=dict(claw_length='61um', ground_spacing='3um',
#                                                                      claw_width='10um', claw_gap='5um',
#                                                                      connector_location='-90'),
#                                                      )))
#     xmon_round2 = TransmonCrossRound_v1(design, 'xmon_round2',
#                                         options=Dict(pos_x=str(space / 2) + 'um', pos_y=str(global_pos_y) + 'um',
#                                                      radius='1 um', cross_width=str(cross_width) + 'um',
#                                                      cross_gap=str(cross_gap) + 'um',
#                                                      rect_width=str(cross_width) + 'um', rect_height='0um',
#                                                      connection_pads=dict(
#                                                          bus_02=dict(claw_length='61um', ground_spacing='3um',
#                                                                      claw_width='10um', claw_gap='5um',
#                                                                      connector_location='180'),
#                                                      )))
#     rc_gap = 3
#     cq_gap = 2
#     l_gap = 16
#     cp_gap = 5
#     l_width = 9
#     a_height = 30
#     t_l_ratio = 7
#     c_width = space - 2 * (cross_gap + cq_gap + l_gap) - cross_width
#     pos_y = -(cross_width / 2 + cross_gap + cq_gap + l_gap + l_width / 2)
#     cp_arm_width = 2 * ((c_width - l_width) / 5 - l_width / 2 - l_gap - rc_gap - cp_gap)
#     cp_arm_length = a_height - l_width / 2 + rc_gap - rc_gap
#
#     options = Dict(pos_x='0um',
#                    pos_y=str(pos_y + global_pos_y) + 'um',
#                    orientation='180',
#                    c_width=str(c_width) + 'um',
#                    l_width=str(l_width) + 'um',
#                    l_gap=str(l_gap) + 'um',
#                    a_height=str(a_height) + 'um',
#                    cp_height='15um',
#                    cp_arm_length=str(cp_arm_length) + 'um',
#                    cp_arm_width='5um',
#                    cp_gap=str(cp_gap) + 'um',
#                    cp_gspace='3um',
#                    fl_width='4um',
#                    fl_gap='2um',
#                    fl_length='10um',
#                    fl_ground='3um',
#                    jj_pad_width='8um',
#                    jj_pad_height='6um',
#                    jj_etch_length='4um',
#                    jj_etch_pad1_width='2um',
#                    jj_etch_pad2_width='5um',
#                    jj_sub_rect_width='100um',
#                    jj_sub_rect_height='100um',
#                    t_l_ratio=str(t_l_ratio))
#     tunable_coupler = MyTunableCoupler03(design, 'tunable_coupler1', options=options)
#     design.copy_qcomponent(xmon_round1, 'xmon_round3', Dict(pos_y=str(-global_pos_y) + 'um'))
#     design.copy_qcomponent(xmon_round2, 'xmon_round4', Dict(pos_y=str(-global_pos_y) + 'um'))
#     design.copy_qcomponent(tunable_coupler, 'tunable_coupler2', Dict(pos_y=str(-pos_y - global_pos_y) + 'um'))
#     design.components['xmon_round3'].options.orientation = '180'
#     design.components['xmon_round3'].options.connection_pads['bus_02']['connector_location'] = '180'
#     design.components['xmon_round4'].options.orientation = '180'
#     design.components['xmon_round4'].options.connection_pads['bus_02']['connector_location'] = '0'
#     design.components['tunable_coupler2'].options.orientation = '0'
#
#     design.components['xmon_round1'].options.gds_cell_name = jj_dict['xmon_round1']
#     design.components['xmon_round2'].options.gds_cell_name = jj_dict['xmon_round2']
#     design.components['xmon_round3'].options.gds_cell_name = jj_dict['xmon_round3']
#     design.components['xmon_round4'].options.gds_cell_name = jj_dict['xmon_round4']
#     design.components['tunable_coupler1'].options.gds_cell_name = jj_dict['tunable_coupler1']
#     design.components['tunable_coupler2'].options.gds_cell_name = jj_dict['tunable_coupler2']
#     gui.rebuild()
#
#     # --------------------------------------绘制电极板----------------------------------------------------
#     opt1 = Dict(pos_x='-2.5mm', pos_y='3.88mm', pad_width='250 um',
#                 pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='-90', )
#     launchpad1 = LaunchpadWirebond(design, 'launchpad1', options=opt1)
#
#     opt2 = Dict(pos_x='-0.79mm', pos_y='3.88mm', pad_width='250 um',
#                 pad_height='250 um', lead_length='50 um', pad_gap='100 um', orientation='-90', )
#     launchpad2 = LaunchpadWirebond(design, 'launchpad2', options=opt2)
#
#     opt3 = Dict(pos_x='1.06mm', pos_y='3.88mm', pad_width='250 um',
#                 pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='-90', )
#     launchpad3 = LaunchpadWirebond(design, 'launchpad3', options=opt3)
#
#     opt4 = Dict(pos_x='2.7mm', pos_y='3.88mm', pad_width='250 um',
#                 pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='-90', )
#     launchpad4 = LaunchpadWirebond(design, 'launchpad4', options=opt4)
#
#     opt5 = Dict(pos_x='3.88mm', pos_y='2.49mm', pad_width='250 um',
#                 pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='180', )
#     launchpad5 = LaunchpadWirebond(design, 'launchpad5', options=opt5)
#
#     opt6 = Dict(pos_x='3.88mm', pos_y='0.83mm', pad_width='250 um',
#                 pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='180', )
#     launchpad6 = LaunchpadWirebond(design, 'launchpad6', options=opt6)
#
#     opt7 = Dict(pos_x='3.88mm', pos_y='-0.83mm', pad_width='250 um',
#                 pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='180', )
#     launchpad7 = LaunchpadWirebond(design, 'launchpad7', options=opt7)
#
#     opt8 = Dict(pos_x='3.88mm', pos_y='-2.5mm', pad_width='250 um',
#                 pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='180', )
#     launchpad8 = LaunchpadWirebond(design, 'launchpad8', options=opt8)
#
#     design.copy_multiple_qcomponents([launchpad1, launchpad2, launchpad3, launchpad4],
#                                      ['launchpad12', 'launchpad11', 'launchpad10', 'launchpad9'],
#                                      [Dict(pos_y='-3.88mm', orientation='90'), Dict(pos_y='-3.88mm', orientation='90'),
#                                       Dict(pos_y='-3.88mm', orientation='90'), Dict(pos_y='-3.88mm', orientation='90')])
#     design.copy_multiple_qcomponents([launchpad5, launchpad6, launchpad7, launchpad8],
#                                      ['launchpad16', 'launchpad15', 'launchpad14', 'launchpad13'],
#                                      [Dict(pos_x='-3.88mm', orientation='0'), Dict(pos_x='-3.88mm', orientation='0'),
#                                       Dict(pos_x='-3.88mm', orientation='0'), Dict(pos_x='-3.88mm', orientation='0')])
#     #
#     # opt9 = Dict(pos_x='-1mm', pos_y=str(-3.88) + 'mm', pad_width='245 um',
#     #             pad_height='245 um', lead_length='176 um', pad_gap='100 um', orientation='90', )
#     # launchpad9 = LaunchpadWirebond(design, 'launchpad9', options=opt9)
#     #
#     # opt10 = Dict(pos_x='1mm', pos_y=str(-3.88) + 'mm', pad_width='245 um',
#     #              pad_height='245 um', lead_length='176 um', pad_gap='100 um', orientation='90', )
#     # launchpad10 = LaunchpadWirebond(design, 'launchpad10', options=opt10)
#     #
#     # opt11 = Dict(pos_x='3mm', pos_y=str(-3.88) + 'mm', pad_width='245 um',
#     #              pad_height='245 um', lead_length='176 um', pad_gap='100 um', orientation='90', )
#     # launchpad11 = LaunchpadWirebond(design, 'launchpad11', options=opt11)
#     # -------------------------------------绘制谐振腔中读取线耦合部分------------------------------------------
#     TQ_pos_x = 2.4
#     TQ_pos_y = global_pos_y * 1e-3
#     coupling_length_qubit = 280
#     down_length_qubit = 900
#     coupling_length_coupler = 280
#     down_length_coupler = 600
#
#     TQ1 = CoupledLineTee(design,
#                          'TQ1',
#                          options=Dict(pos_x=str(-TQ_pos_x) + 'mm', pos_y=str(TQ_pos_y) + 'mm',
#                                       orientation='90',
#                                       coupling_length=str(coupling_length_qubit) + 'um',
#                                       down_length=str(down_length_qubit) + 'um',
#                                       coupling_space='3um',
#                                       prime_width='10um',
#                                       prime_gap='5um',
#                                       second_width='10um',
#                                       second_gap='5um',
#                                       open_termination=False,
#                                       mirror=False))
#     TQ2 = CoupledLineTee(design,
#                          'TQ2',
#                          options=Dict(pos_x=str(TQ_pos_x) + 'mm', pos_y=str(TQ_pos_y) + 'mm',
#                                       orientation='-90',
#                                       coupling_length=str(coupling_length_qubit) + 'um',
#                                       down_length=str(down_length_qubit) + 'um',
#                                       coupling_space='3um',
#                                       prime_width='10um',
#                                       prime_gap='5um',
#                                       second_width='10um',
#                                       second_gap='5um',
#                                       open_termination=False,
#                                       mirror=True))
#     TQ3 = CoupledLineTee(design,
#                          'TQ3',
#                          options=Dict(pos_x=str(0) + 'mm', pos_y=str(0.25) + 'mm',
#                                       orientation='180',
#                                       coupling_length=str(coupling_length_coupler) + 'um',
#                                       down_length=str(down_length_coupler) + 'um',
#                                       coupling_space='3um',
#                                       prime_width='10um',
#                                       prime_gap='5um',
#                                       second_width='10um',
#                                       second_gap='5um',
#                                       open_termination=False,
#                                       mirror=False))
#
#     TQ4 = CoupledLineTee(design,
#                          'TQ4',
#                          options=Dict(pos_x=str(-TQ_pos_x) + 'mm', pos_y=str(-TQ_pos_y) + 'mm',
#                                       orientation='90',
#                                       coupling_length=str(coupling_length_qubit) + 'um',
#                                       down_length=str(down_length_qubit) + 'um',
#                                       coupling_space='3um',
#                                       prime_width='10um',
#                                       prime_gap='5um',
#                                       second_width='10um',
#                                       second_gap='5um',
#                                       open_termination=False,
#                                       mirror=False))
#
#     TQ5 = CoupledLineTee(design,
#                          'TQ5',
#                          options=Dict(pos_x=str(TQ_pos_x) + 'mm', pos_y=str(-TQ_pos_y) + 'mm',
#                                       orientation='-90',
#                                       coupling_length=str(coupling_length_qubit) + 'um',
#                                       down_length=str(down_length_qubit) + 'um',
#                                       coupling_space='3um',
#                                       prime_width='10um',
#                                       prime_gap='5um',
#                                       second_width='10um',
#                                       second_gap='5um',
#                                       open_termination=False,
#                                       mirror=True))
#
#     TQ6 = CoupledLineTee(design,
#                          'TQ6',
#                          options=Dict(pos_x=str(0) + 'mm', pos_y=str(-0.25) + 'mm',
#                                       orientation='0',
#                                       coupling_length=str(coupling_length_coupler) + 'um',
#                                       down_length=str(down_length_coupler) + 'um',
#                                       coupling_space='3um',
#                                       prime_width='10um',
#                                       prime_gap='5um',
#                                       second_width='10um',
#                                       second_gap='5um',
#                                       open_termination=False,
#                                       mirror=True))
#
#     # -------------------------------------------------------绘制谐振腔----------------------------------------------
#     whole_length1 = 4.378768750777398 + 1.18
#     whole_length2 = 4.378768750777398 + 1.18
#     whole_length3 = 4.18
#     whole_length4 = 4.378768750777398 + 1.18
#     whole_length5 = 4.378768750777398 + 1.18
#     whole_length6 = 4.18
#     total_length1 = whole_length1 - (coupling_length_qubit + down_length_qubit) * 1e-3
#     total_length2 = whole_length2 - (coupling_length_qubit + down_length_qubit) * 1e-3
#     total_length3 = whole_length3 - (coupling_length_coupler + down_length_coupler) * 1e-3
#     total_length4 = whole_length4 - (coupling_length_qubit + down_length_qubit) * 1e-3
#     total_length5 = whole_length5 - (coupling_length_qubit + down_length_qubit) * 1e-3
#     total_length6 = whole_length6 - (coupling_length_coupler + down_length_coupler) * 1e-3
#     jogsS = OrderedDict()
#     jogsS[0] = ["R", '0um']
#     spacing = 0.1
#     ops = dict(fillet=spacing / 2 - 0.001)
#     asymmetry = 0
#     start_straight = 0.13
#     # total_length = total_length[1]
#     options1 = Dict(total_length=str(total_length1) + 'mm',
#                     hfss_wire_bonds=False,
#                     pin_inputs=Dict(end_pin=Dict(component='TQ1',
#                                                  pin='second_end'),
#                                     start_pin=Dict(component='xmon_round1', pin='bus_02')),
#                     lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
#                     meander=Dict(spacing=spacing, asymmetry=asymmetry),
#                     **ops)
#     meander1 = RouteMeander(design, 'meander1', options=options1)
#
#     jogsS = OrderedDict()
#     jogsS[0] = ["L", '0um']
#     options2 = Dict(total_length=str(total_length2) + 'mm',
#                     hfss_wire_bonds=False,
#                     pin_inputs=Dict(end_pin=Dict(component='TQ2',
#                                                  pin='second_end'),
#                                     start_pin=Dict(component='xmon_round2', pin='bus_02')),
#                     lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
#                     meander=Dict(spacing=spacing, asymmetry=asymmetry),
#                     **ops)
#     meander2 = RouteMeander(design, 'meander2', options=options2)
#
#     jogsS = OrderedDict()
#     jogsS[0] = ["L", '0um']
#     options3 = Dict(total_length=str(total_length3) + 'mm',
#                     hfss_wire_bonds=False,
#                     pin_inputs=Dict(end_pin=Dict(component='TQ3',
#                                                  pin='second_end'),
#                                     start_pin=Dict(component='tunable_coupler1', pin='Control')),
#                     lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
#                     meander=Dict(spacing=spacing, asymmetry=asymmetry),
#                     **ops)
#     meander3 = RouteMeander(design, 'meander3', options=options3)
#
#     jogsS = OrderedDict()
#     jogsS[0] = ["R", '0um']
#     options4 = Dict(total_length=str(total_length4) + 'mm',
#                     hfss_wire_bonds=False,
#                     pin_inputs=Dict(end_pin=Dict(component='TQ4',
#                                                  pin='second_end'),
#                                     start_pin=Dict(component='xmon_round3', pin='bus_02')),
#                     lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
#                     meander=Dict(spacing=spacing, asymmetry=asymmetry),
#                     **ops)
#     meander4 = RouteMeander(design, 'meander4', options=options4)
#
#     jogsS = OrderedDict()
#     jogsS[0] = ["L", '0um']
#     options5 = Dict(total_length=str(total_length5) + 'mm',
#                     hfss_wire_bonds=False,
#                     pin_inputs=Dict(end_pin=Dict(component='TQ5',
#                                                  pin='second_end'),
#                                     start_pin=Dict(component='xmon_round4', pin='bus_02')),
#                     lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
#                     meander=Dict(spacing=spacing, asymmetry=asymmetry),
#                     **ops)
#     meander5 = RouteMeander(design, 'meander5', options=options5)
#
#     jogsS = OrderedDict()
#     jogsS[0] = ["R", '0um']
#     options6 = Dict(total_length=str(total_length6) + 'mm',
#                     hfss_wire_bonds=False,
#                     pin_inputs=Dict(end_pin=Dict(component='TQ6',
#                                                  pin='second_end'),
#                                     start_pin=Dict(component='tunable_coupler2', pin='Control')),
#                     lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
#                     meander=Dict(spacing=spacing, asymmetry=asymmetry),
#                     **ops)
#     meander6 = RouteMeander(design, 'meander6', options=options6)
#
#     # -----------------------------------------------绘制读取线---------------------------------------------------------
#     fillet = 100
#     pin_opt1 = Dict(pin_inputs=Dict(start_pin=Dict(component='launchpad16', pin='tie'),
#                                     end_pin=Dict(component='TQ1', pin='prime_end'), ), lead=Dict(start_straight=0.01,
#                                                                                                  end_straight=0.1, ),
#                     fillet=str(fillet)+'um')
#     RoutePathfinder(design, 'readout1_part1', options=pin_opt1)
#
#     pin_opt2 = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ1', pin='prime_start'),
#                                     end_pin=Dict(component='TQ3', pin='prime_end'), ), lead=Dict(start_straight=0.01,
#                                                                                                  end_straight=0.1, ),
#                     fillet=str(fillet)+'um')
#     RoutePathfinder(design, 'readout1_part2', options=pin_opt2)
#
#     pin_opt3 = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ3', pin='prime_start'),
#                                     end_pin=Dict(component='TQ2', pin='prime_end'), ), lead=Dict(start_straight=0.01,
#                                                                                                  end_straight=0.1, ),
#                     fillet=str(fillet)+'um', )
#     RoutePathfinder(design, 'readout1_part3', options=pin_opt3)
#
#     pin_opt4 = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ2', pin='prime_start'),
#                                     end_pin=Dict(component='launchpad5', pin='tie'), ), lead=Dict(start_straight=0.01,
#                                                                                                   end_straight=0.1, ),
#                     fillet=str(fillet)+'um')
#     RoutePathfinder(design, 'readout1_part4', options=pin_opt4)
#
#     pin_opt5 = Dict(pin_inputs=Dict(start_pin=Dict(component='launchpad13', pin='tie'),
#                                     end_pin=Dict(component='TQ4', pin='prime_start'), ), lead=Dict(start_straight=0.01,
#                                                                                                    end_straight=0.1, ),
#                     fillet=str(fillet)+'um')
#     RoutePathfinder(design, 'readout2_part1', options=pin_opt5)
#
#     pin_opt6 = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ4', pin='prime_end'),
#                                     end_pin=Dict(component='TQ6', pin='prime_start'), ), lead=Dict(start_straight=0.01,
#                                                                                                    end_straight=0.1, ),
#                     fillet=str(fillet)+'um')
#     RoutePathfinder(design, 'readout2_part2', options=pin_opt6)
#
#     pin_opt7 = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ6', pin='prime_end'),
#                                     end_pin=Dict(component='TQ5', pin='prime_start'), ), lead=Dict(start_straight=0.01,
#                                                                                                    end_straight=0.1, ),
#                     fillet=str(fillet)+'um')
#     RoutePathfinder(design, 'readout2_part3', options=pin_opt7)
#
#     pin_opt8 = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ5', pin='prime_end'),
#                                     end_pin=Dict(component='launchpad8', pin='tie'), ), lead=Dict(start_straight=0.01,
#                                                                                                   end_straight=0.1, ),
#                     fillet=str(fillet)+'um')
#     RoutePathfinder(design, 'readout2_part4', options=pin_opt8)
#
#     # --------------------------------------------------------绘制控制线---------------------------------------------------
#     gap = 2
#     xy_gap = 4
#     reference_point_x1 = design.components['xmon_round1'].parse_options().pos_x
#     reference_point_y1 = design.components['xmon_round1'].parse_options().pos_y + design.components[
#         'xmon_round1'].parse_options().cross_length1 \
#                          + design.components['xmon_round1'].parse_options().cross_gap + gap * 1e-3 + xy_gap * 1e-3
#     otg1 = OpenToGround(design, 'open_xmon1_xyline',
#                         options=Dict(pos_x=reference_point_x1, pos_y=reference_point_y1, width='4um',
#                                      gap=str(gap) + 'um', termination_gap=str(gap) + 'um', orientation='-90'))
#
#     reference_point_x2 = design.components['xmon_round2'].parse_options().pos_x
#     reference_point_y2 = design.components['xmon_round2'].parse_options().pos_y + design.components[
#         'xmon_round2'].parse_options().cross_length1 \
#                          + design.components['xmon_round2'].parse_options().cross_gap + gap * 1e-3 + xy_gap * 1e-3
#     otg2 = OpenToGround(design, 'open_xmon2_xyline',
#                         options=Dict(pos_x=reference_point_x2, pos_y=reference_point_y2, width='4um',
#                                      gap=str(gap) + 'um', termination_gap=str(gap) + 'um', orientation='-90'))
#     reference_point_x3 = design.components['xmon_round3'].parse_options().pos_x \
#                          - design.components['xmon_round3'].parse_options().cross_width / 2 \
#                          - design.components['xmon_round3'].parse_options().cross_gap - (xy_gap + 2) * 1e-3
#     reference_point_y3 = design.components['xmon_round3'].parse_options().pos_y - design.components[
#         'xmon_round3'].parse_options().cross_length1
#     # - design.components['xmon_round3'].parse_options().cross_gap - gap * 1e-3 - xy_gap * 1e-3
#     otg3 = OpenToGround(design, 'open_xmon3_xyline',
#                         options=Dict(pos_x=reference_point_x3, pos_y=reference_point_y3, width='4um',
#                                      gap=str(gap) + 'um', termination_gap=str(gap) + 'um', orientation='0'))
#
#     reference_point_x4 = design.components['xmon_round4'].parse_options().pos_x \
#                          + design.components['xmon_round4'].parse_options().cross_width / 2 \
#                          + design.components['xmon_round3'].parse_options().cross_gap + (xy_gap + 2) * 1e-3
#     reference_point_y4 = design.components['xmon_round4'].parse_options().pos_y - design.components[
#         'xmon_round2'].parse_options().cross_length1
#     # - design.components['xmon_round2'].parse_options().cross_gap - gap * 1e-3 - xy_gap * 1e-3
#     otg4 = OpenToGround(design, 'open_xmon4_xyline',
#                         options=Dict(pos_x=reference_point_x4, pos_y=reference_point_y4, width='4um',
#                                      gap=str(gap) + 'um', termination_gap=str(gap) + 'um', orientation='180'))
#     reference_point_x5 = design.components['tunable_coupler2'].parse_options().pos_x - design.components[
#         'tunable_coupler2'].parse_options().l_width / 2 \
#                          - design.components['tunable_coupler2'].parse_options().l_gap - (xy_gap + 2) * 1e-3
#     reference_point_y5 = design.components['tunable_coupler2'].parse_options().pos_y - design.components[
#         'tunable_coupler2'].parse_options().l_width / 2 \
#                          - design.components['tunable_coupler2'].parse_options().t_l_ratio * design.components[
#                              'tunable_coupler2'].parse_options().a_height
#     otg5 = OpenToGround(design, 'open_coupler2_xyline',
#                         options=Dict(pos_x=reference_point_x5, pos_y=reference_point_y5, width='4um',
#                                      gap=str(gap) + 'um', termination_gap=str(gap) + 'um', orientation='0'))
#
#     connector_x1 = reference_point_x1 - 0.2
#     connector_y1 = reference_point_y1 + 0.35
#     connector1 = MyConnector(design, 'connector1',
#                              options=Dict(pos_x=connector_x1, pos_y=connector_y1, width='4um', gap=str(gap) + 'um',
#                                           width0='10um', gap0='5um', length='10um', orientation='-90'))
#     connector_x2 = reference_point_x2 + 0.2
#     connector_y2 = reference_point_y2 + 0.35
#     connector2 = MyConnector(design, 'connector2',
#                              options=Dict(pos_x=connector_x2, pos_y=connector_y2, width='4um', gap=str(gap) + 'um',
#                                           width0='10um', gap0='5um', length='10um', orientation='-90'))
#     connector_x3 = 0
#     connector_y3 = connector_y2
#     connector3 = MyConnector(design, 'connector3',
#                              options=Dict(pos_x=connector_x3, pos_y=connector_y3, width='4um', gap=str(gap) + 'um',
#                                           width0='10um', gap0='5um', length='10um', orientation='-90'))
#     connector_x4 = reference_point_x3 - 0.2
#     connector_y4 = reference_point_y3 - 0.35
#     connector4 = MyConnector(design, 'connector4',
#                              options=Dict(pos_x=connector_x4, pos_y=connector_y4, width='4um', gap=str(gap) + 'um',
#                                           width0='10um', gap0='5um', length='10um', orientation='90'))
#     connector_x5 = reference_point_x4 + 0.2
#     connector_y5 = reference_point_y4 - 0.35
#     connector5 = MyConnector(design, 'connector5',
#                              options=Dict(pos_x=connector_x5, pos_y=connector_y5, width='4um', gap=str(gap) + 'um',
#                                           width0='10um', gap0='5um', length='10um', orientation='90'))
#     connector_x6 = 0
#     connector_y6 = connector_y5
#     connector6 = MyConnector(design, 'connector6',
#                              options=Dict(pos_x=connector_x6, pos_y=connector_y6, width='4um', gap=str(gap) + 'um',
#                                           width0='10um', gap0='5um', length='10um', orientation='90'))
#     connector_x7 = connector_x6 - 0.20
#     connector_y7 = connector_y6
#     connector7 = MyConnector(design, 'connector7',
#                              options=Dict(pos_x=connector_x7, pos_y=connector_y7, width='4um', gap=str(gap) + 'um',
#                                           width0='10um', gap0='5um', length='10um', orientation='90'))
#     # connector7 = OpenToGround(design, 'connector7',options=Dict(pos_x=connector_x7, pos_y=connector_y7,width='4um',
#     #                                                             gap=str(gap)+'um',termination_gap=str(gap)+'um', orientation='-90'))
#
#     opt1 = Dict(pin_inputs=Dict(start_pin=Dict(component='open_xmon1_xyline', pin='open'),
#                                 end_pin=Dict(component='connector1', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
#                                                                                                   end_straight=0.1),
#                 fillet=str(fillet)+'um', trace_width='4um', trace_gap='2um')
#     RoutePathfinder(design, 'xy1_part1', options=opt1)
#     opt1 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector1', pin='c_pin_l'),
#                                 end_pin=Dict(component='launchpad1', pin='tie'), ), lead=Dict(start_straight=0.150,
#                                                                                               end_straight=0.1),
#                 fillet=str(fillet)+'um', trace_width='10um', trace_gap='5um')
#     RoutePathfinder(design, 'xy1_part2', options=opt1)
#     opt2 = Dict(pin_inputs=Dict(start_pin=Dict(component='open_xmon2_xyline', pin='open'),
#                                 end_pin=Dict(component='connector2', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
#                                                                                                   end_straight=0.1),
#                 fillet=str(fillet)+'um', trace_width='4um', trace_gap='2um')
#     RoutePathfinder(design, 'xy2_part1', options=opt2)
#     opt2 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector2', pin='c_pin_l'),
#                                 end_pin=Dict(component='launchpad4', pin='tie'), ), lead=Dict(start_straight=0.150,
#                                                                                               end_straight=0.1),
#                 fillet=str(fillet)+'um', trace_width='10um', trace_gap='5um')
#     RoutePathfinder(design, 'xy2_part2', options=opt2)
#     opt3 = Dict(pin_inputs=Dict(start_pin=Dict(component='tunable_coupler1', pin='Flux'),
#                                 end_pin=Dict(component='connector3', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
#                                                                                                   end_straight=0.1),
#                 fillet=str(fillet)+'um', trace_width='4um', trace_gap='2um')
#     RoutePathfinder(design, 'z1_part1', options=opt3)
#     opt3 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector3', pin='c_pin_l'),
#                                 end_pin=Dict(component='launchpad3', pin='tie'), ), lead=Dict(start_straight=0.150,
#                                                                                               end_straight=0.1),
#                 fillet=str(fillet)+'um', trace_width='10um', trace_gap='5um')
#     RoutePathfinder(design, 'z1_part2', options=opt3)
#
#     opt5 = Dict(pin_inputs=Dict(start_pin=Dict(component='open_xmon4_xyline', pin='open'),
#                                 end_pin=Dict(component='connector5', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
#                                                                                                   end_straight=0.1),
#                 advanced=Dict(avoid_collision=False), fillet=str(fillet)+'um', trace_width='4um', trace_gap='2um')
#     RoutePathfinder(design, 'xy4_part1', options=opt5)
#     opt5 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector5', pin='c_pin_l'),
#                                 end_pin=Dict(component='launchpad9', pin='tie'), ), lead=Dict(start_straight=0.150,
#                                                                                               end_straight=0.4),
#                 fillet=str(fillet)+'um', trace_width='10um', trace_gap='5um')
#     RoutePathfinder(design, 'xy4_part2', options=opt5)
#     opt6 = Dict(pin_inputs=Dict(start_pin=Dict(component='tunable_coupler2', pin='Flux'),
#                                 end_pin=Dict(component='connector6', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
#                                                                                                   end_straight=0.1),
#                 fillet=str(fillet)+'um', trace_width='4um', trace_gap='2um')
#     RoutePathfinder(design, 'z2_part1', options=opt6)
#     opt6 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector6', pin='c_pin_l'),
#                                 end_pin=Dict(component='launchpad10', pin='tie'), ), lead=Dict(start_straight=0.150,
#                                                                                                end_straight=0.1),
#                 fillet=str(fillet)+'um', trace_width='10um', trace_gap='5um')
#     RoutePathfinder(design, 'z2_part2', options=opt6)
#
#     anchors = OrderedDict()
#     midpoint_x = connector_x6 - 0.12
#     midpoint_y = connector_y6 + 0.14
#     anchors[0] = np.array([midpoint_x, midpoint_y])
#     opt7 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector7', pin='c_pin_r'),
#                                 end_pin=Dict(component='open_coupler2_xyline', pin='open'), ),
#                 lead=Dict(start_straight=0.05,
#                           end_straight=0.05), advanced=Dict(avoid_collision=False), anchors=anchors, fillet=str(40)+'um',
#                 trace_width='4um', trace_gap='2um')
#     RoutePathfinder(design, 'xy5_part1', options=opt7)
#     opt7 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector7', pin='c_pin_l'),
#                                 end_pin=Dict(component='launchpad11', pin='tie'), ), lead=Dict(start_straight=0.150,
#                                                                                                end_straight=0.1),
#                 fillet=str(fillet)+'um', trace_width='10um', trace_gap='5um')
#     RoutePathfinder(design, 'xy5_part2', options=opt7)
#     # jogsS = OrderedDict()
#     # jogsS[0] = ["R", '0um']
#     # anchors = OrderedDict()
#     # midpoint_x = connector_x6 - 0.12
#     # midpoint_y = connector_y6 + 0.14
#     # anchors[0] = np.array([midpoint_x, midpoint_y])
#     opt4 = Dict(pin_inputs=Dict(start_pin=Dict(component='open_xmon3_xyline', pin='open'),
#                                 end_pin=Dict(component='connector4', pin='c_pin_r'), ), lead=Dict(start_straight=0.100,
#                                                                                                   end_straight=0.1,
#                                                                                                   ),
#                 advanced=Dict(avoid_collision=False), fillet=str(fillet)+'um', trace_width='4um', trace_gap='2um')
#     RoutePathfinder(design, 'xy3_part1', options=opt4)
#     opt4 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector4', pin='c_pin_l'),
#                                 end_pin=Dict(component='launchpad12', pin='tie'), ), lead=Dict(start_straight=0.150,
#                                                                                                end_straight=0.4),
#                 fillet=str(fillet)+'um', trace_width='10um', trace_gap='5um')
#     RoutePathfinder(design, 'xy3_part2', options=opt4)
#
#     gui.rebuild()
#     return design, gui


def two_qubit_layout(jj_dict=None, parameter_file_path=None, airbridge=False, version='1.00'):
    design = designs.DesignPlanar()
    design.chips.main.size['size_x'] = '10mm'
    design.chips.main.size['size_y'] = '10mm'
    design.variables.cpw_gap = '5 um'
    design.chips['main']['material'] = 'sapphire'
    design.chips['main']['size']['sample_holder_top'] = '500um'
    design.chips['main']['size']['sample_holder_bottom'] = '500um'
    design.chips['main']['size']['size_z'] = '-500um'
    gui = MetalGUI(design)

    design.delete_all_components()
    global_pos_y = 2000
    cross_width = 16
    cross_gap = 16
    space = 400
    x_gap = 5
    y_gap = 5
    digits = [int(char) for char in version if char.isdigit()]
    number = digits[0]
    decimal1 = digits[1]
    decimal2 = digits[2]

    if version != '0.00':
        options = {
            'number': number,
            'decimal1': decimal1,
            'decimal2': decimal2,
            'width': '20um',  # 笔画宽度
            'height': '100um',  # 数字高度
            'pos_x': str(3.67)+'mm',
            'pos_y': str(-3.80)+'mm',
            'spacing': '30um',
        }
        NumberComponent(design, name='number1', options=options)
    TransmonCrossRound_v1(design, 'Q1',
                               options=Dict(pos_x=str(-space / 2) + 'um', pos_y=str(global_pos_y) + 'um',
                                            radius='1 um', cross_width=str(cross_width) + 'um',
                                            cross_gap=str(cross_gap) + 'um',
                                            rect_width=str(cross_width) + 'um', rect_height='0um',
                                            connection_pads=dict(
                                                bus_02=dict(claw_length='61um', ground_spacing='3um',
                                                            claw_width='10um', claw_gap='5um',
                                                            connector_location='-90'),
                                                bus_01=dict(connector_location='90', connector_type='1',
                                                            ground_spacing='4um', claw_width='4um', coupling_gap='2um')
                                            )))
    TransmonCrossRound_v1(design, 'Q2',
                               options=Dict(pos_x=str(space / 2) + 'um', pos_y=str(global_pos_y) + 'um',
                                            radius='1 um', cross_width=str(cross_width) + 'um',
                                            cross_gap=str(cross_gap) + 'um',
                                            rect_width=str(cross_width) + 'um', rect_height='0um',
                                            connection_pads=dict(
                                                bus_02=dict(claw_length='61um', ground_spacing='3um',
                                                            claw_width='10um', claw_gap='5um',
                                                            connector_location='180'),
                                                bus_01=dict(connector_location='90', connector_type='1',
                                                            ground_spacing='4um', claw_width='4um', coupling_gap='2um')
                                            )))
    TransmonCrossRound_v1(design, 'Q3',
                               options=Dict(pos_x=str(-space / 2) + 'um', pos_y=str(-global_pos_y) + 'um',
                                            orientation='180',
                                            radius='1 um', cross_width=str(cross_width) + 'um',
                                            cross_gap=str(cross_gap) + 'um',
                                            rect_width=str(cross_width) + 'um', rect_height='0um',
                                            connection_pads=dict(
                                                bus_02=dict(claw_length='61um', ground_spacing='3um',
                                                            claw_width='10um', claw_gap='5um',
                                                            connector_location='180'),
                                                bus_01=dict(connector_type='2', xyline_location='1',
                                                            ground_spacing='4um', claw_width='4um', coupling_gap='2um')
                                            )))
    TransmonCrossRound_v1(design, 'Q4',
                               options=Dict(pos_x=str(space / 2) + 'um', pos_y=str(-global_pos_y) + 'um',
                                            orientation='180',
                                            radius='1 um', cross_width=str(cross_width) + 'um',
                                            cross_gap=str(cross_gap) + 'um',
                                            rect_width=str(cross_width) + 'um', rect_height='0um',
                                            connection_pads=dict(
                                                bus_02=dict(claw_length='61um', ground_spacing='3um',
                                                            claw_width='10um', claw_gap='5um',
                                                            connector_location='0'),
                                                bus_01=dict(connector_type='2', xyline_location='0',
                                                            ground_spacing='4um', claw_width='4um', coupling_gap='2um')
                                            )))

    rc_gap = 3
    cq_gap = 2
    l_gap = 16
    cp_gap = 5
    l_width = 9
    a_height = 30
    t_l_ratio = 7
    c_width = space - 2 * (cross_gap + cq_gap + l_gap) - cross_width
    pos_y = -(cross_width / 2 + cross_gap + cq_gap + l_gap + l_width / 2)
    cp_arm_width = 2 * ((c_width - l_width) / 5 - l_width / 2 - l_gap - rc_gap - cp_gap)
    cp_arm_length = a_height - l_width / 2 + rc_gap - rc_gap

    options = Dict(pos_x='0um',
                   pos_y=str(pos_y + global_pos_y) + 'um',
                   orientation='180',
                   c_width=str(c_width) + 'um',
                   l_width=str(l_width) + 'um',
                   l_gap=str(l_gap) + 'um',
                   a_height=str(a_height) + 'um',
                   cp_height='15um',
                   cp_arm_length=str(cp_arm_length) + 'um',
                   cp_arm_width='5um',
                   cp_gap=str(cp_gap) + 'um',
                   cp_gspace='3um',
                   fl_width='4um',
                   fl_gap='2um',
                   fl_length='10um',
                   fl_ground='3um',
                   jj_pad_width='8um',
                   jj_pad_height='6um',
                   jj_etch_length='4um',
                   jj_etch_pad1_width='2um',
                   jj_etch_pad2_width='5um',
                   jj_sub_rect_width='100um',
                   jj_sub_rect_height='100um',
                   t_l_ratio=str(t_l_ratio))
    tunable_coupler = MyTunableCoupler03(design, 'tunable_coupler1', options=options)
    # design.copy_qcomponent(xmon_round1, 'Q3', Dict(pos_y=str(-global_pos_y) + 'um'))
    # design.copy_qcomponent(xmon_round2, 'Q4', Dict(pos_y=str(-global_pos_y) + 'um'))
    design.copy_qcomponent(tunable_coupler, 'tunable_coupler2', Dict(pos_y=str(-pos_y - global_pos_y) + 'um'))
    # design.components['Q3'].options.orientation = '180'
    # design.components['Q3'].options.connection_pads['bus_02']['connector_location'] = '180'
    # design.components['Q4'].options.orientation = '180'
    # design.components['Q4'].options.connection_pads['bus_02']['connector_location'] = '0'
    design.components['tunable_coupler2'].options.orientation = '0'
    #
    # design.components['xmon_round1'].options.gds_cell_name = jj_dict['xmon_round1']
    # design.components['xmon_round2'].options.gds_cell_name = jj_dict['xmon_round2']
    # design.components['xmon_round3'].options.gds_cell_name = jj_dict['xmon_round3']
    # design.components['xmon_round4'].options.gds_cell_name = jj_dict['xmon_round4']
    # design.components['tunable_coupler1'].options.gds_cell_name = jj_dict['tunable_coupler1']
    # design.components['tunable_coupler2'].options.gds_cell_name = jj_dict['tunable_coupler2']
    # gui.rebuild()

    # --------------------------------------绘制电极板----------------------------------------------------
    opt1 = Dict(pos_x='-2.5mm', pos_y='3.88mm', pad_width='250 um',
                pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='-90', )
    launchpad1 = LaunchpadWirebond(design, 'launchpad1', options=opt1)

    opt2 = Dict(pos_x='-0.79mm', pos_y='3.88mm', pad_width='250 um',
                pad_height='250 um', lead_length='50 um', pad_gap='100 um', orientation='-90', )
    launchpad2 = LaunchpadWirebond(design, 'launchpad2', options=opt2)

    opt3 = Dict(pos_x='1.06mm', pos_y='3.88mm', pad_width='250 um',
                pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='-90', )
    launchpad3 = LaunchpadWirebond(design, 'launchpad3', options=opt3)

    opt4 = Dict(pos_x='2.7mm', pos_y='3.88mm', pad_width='250 um',
                pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='-90', )
    launchpad4 = LaunchpadWirebond(design, 'launchpad4', options=opt4)

    opt5 = Dict(pos_x='3.88mm', pos_y='2.49mm', pad_width='250 um',
                pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='180', )
    launchpad5 = LaunchpadWirebond(design, 'launchpad5', options=opt5)

    opt6 = Dict(pos_x='3.88mm', pos_y='0.83mm', pad_width='250 um',
                pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='180', )
    launchpad6 = LaunchpadWirebond(design, 'launchpad6', options=opt6)

    opt7 = Dict(pos_x='3.88mm', pos_y='-0.83mm', pad_width='250 um',
                pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='180', )
    launchpad7 = LaunchpadWirebond(design, 'launchpad7', options=opt7)

    opt8 = Dict(pos_x='3.88mm', pos_y='-2.5mm', pad_width='250 um',
                pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='180', )
    launchpad8 = LaunchpadWirebond(design, 'launchpad8', options=opt8)

    design.copy_multiple_qcomponents([launchpad1, launchpad2, launchpad3, launchpad4],
                                     ['launchpad12', 'launchpad11', 'launchpad10', 'launchpad9'],
                                     [Dict(pos_y='-3.88mm', orientation='90'), Dict(pos_y='-3.88mm', orientation='90'),
                                      Dict(pos_y='-3.88mm', orientation='90'), Dict(pos_y='-3.88mm', orientation='90')])
    design.copy_multiple_qcomponents([launchpad5, launchpad6, launchpad7, launchpad8],
                                     ['launchpad16', 'launchpad15', 'launchpad14', 'launchpad13'],
                                     [Dict(pos_x='-3.88mm', orientation='0'), Dict(pos_x='-3.88mm', orientation='0'),
                                      Dict(pos_x='-3.88mm', orientation='0'), Dict(pos_x='-3.88mm', orientation='0')])
    #
    # opt9 = Dict(pos_x='-1mm', pos_y=str(-3.88) + 'mm', pad_width='245 um',
    #             pad_height='245 um', lead_length='176 um', pad_gap='100 um', orientation='90', )
    # launchpad9 = LaunchpadWirebond(design, 'launchpad9', options=opt9)
    #
    # opt10 = Dict(pos_x='1mm', pos_y=str(-3.88) + 'mm', pad_width='245 um',
    #              pad_height='245 um', lead_length='176 um', pad_gap='100 um', orientation='90', )
    # launchpad10 = LaunchpadWirebond(design, 'launchpad10', options=opt10)
    #
    # opt11 = Dict(pos_x='3mm', pos_y=str(-3.88) + 'mm', pad_width='245 um',
    #              pad_height='245 um', lead_length='176 um', pad_gap='100 um', orientation='90', )
    # launchpad11 = LaunchpadWirebond(design, 'launchpad11', options=opt11)
    # gui.rebuild()
    # gui.autoscale()
    # -------------------------------------绘制谐振腔中读取线耦合部分------------------------------------------
    TQ_pos_x = 2.4
    TQ_pos_y = global_pos_y * 1e-3
    coupling_length_qubit = 280
    down_length_qubit = 900
    coupling_length_coupler = 280
    down_length_coupler = 600
    readout_line_y = 0.3

    MyCoupledLineTee(design,
                           'TQ1',
                           options=Dict(pos_x=str(-TQ_pos_x) + 'mm', pos_y=str(TQ_pos_y) + 'mm',
                                        orientation='90',
                                        coupling_length=str(coupling_length_qubit) + 'um',
                                        down_length=str(down_length_qubit) + 'um',
                                        coupling_space='3um',
                                        prime_width='10um',
                                        prime_gap='5um',
                                        second_width='10um',
                                        second_gap='5um',
                                        open_termination=False,
                                        mirror=False))
    MyCoupledLineTee(design,
                           'TQ2',
                           options=Dict(pos_x=str(TQ_pos_x) + 'mm', pos_y=str(TQ_pos_y) + 'mm',
                                        orientation='-90',
                                        coupling_length=str(coupling_length_qubit) + 'um',
                                        down_length=str(down_length_qubit) + 'um',
                                        coupling_space='3um',
                                        prime_width='10um',
                                        prime_gap='5um',
                                        second_width='10um',
                                        second_gap='5um',
                                        open_termination=False,
                                        mirror=True))
    MyCoupledLineTee(design,
                           'TQ3',
                           options=Dict(pos_x=str(0) + 'mm', pos_y=str(readout_line_y) + 'mm',
                                        orientation='180',
                                        coupling_length=str(coupling_length_coupler) + 'um',
                                        down_length=str(down_length_coupler) + 'um',
                                        coupling_space='3um',
                                        prime_width='10um',
                                        prime_gap='5um',
                                        second_width='10um',
                                        second_gap='5um',
                                        open_termination=False,
                                        mirror=False))

    MyCoupledLineTee(design,
                           'TQ4',
                           options=Dict(pos_x=str(-TQ_pos_x) + 'mm', pos_y=str(-TQ_pos_y) + 'mm',
                                        orientation='90',
                                        coupling_length=str(coupling_length_qubit) + 'um',
                                        down_length=str(down_length_qubit) + 'um',
                                        coupling_space='3um',
                                        prime_width='10um',
                                        prime_gap='5um',
                                        second_width='10um',
                                        second_gap='5um',
                                        open_termination=False,
                                        mirror=False))

    MyCoupledLineTee(design,
                           'TQ5',
                           options=Dict(pos_x=str(TQ_pos_x) + 'mm', pos_y=str(-TQ_pos_y) + 'mm',
                                        orientation='-90',
                                        coupling_length=str(coupling_length_qubit) + 'um',
                                        down_length=str(down_length_qubit) + 'um',
                                        coupling_space='3um',
                                        prime_width='10um',
                                        prime_gap='5um',
                                        second_width='10um',
                                        second_gap='5um',
                                        open_termination=False,
                                        mirror=True))

    MyCoupledLineTee(design,
                           'TQ6',
                           options=Dict(pos_x=str(0) + 'mm', pos_y=str(-readout_line_y) + 'mm',
                                        orientation='0',
                                        coupling_length=str(coupling_length_coupler) + 'um',
                                        down_length=str(down_length_coupler) + 'um',
                                        coupling_space='3um',
                                        prime_width='10um',
                                        prime_gap='5um',
                                        second_width='10um',
                                        second_gap='5um',
                                        open_termination=False,
                                        mirror=True))

    MyCoupledLineTee(design,
                           'TQ7',
                           options=Dict(pos_x=str(-1.3) + 'mm', pos_y=str(readout_line_y) + 'mm',
                                        orientation='180',
                                        coupling_length=str(40) + 'um',
                                        down_length=str(100) + 'um',
                                        over_length=str(450) + 'um',
                                        coupling_space='3um',
                                        prime_width='10um',
                                        prime_gap='5um',
                                        second_width='10um',
                                        second_gap='5um',
                                        open_termination=False,
                                        mirror=False))

    MyCoupledLineTee(design,
                           'TQ8',
                           options=Dict(pos_x=str(1.3) + 'mm', pos_y=str(readout_line_y) + 'mm',
                                        orientation='180',
                                        coupling_length=str(100) + 'um',
                                        down_length=str(100) + 'um',
                                        over_length=str(450) + 'um',
                                        coupling_space='3um',
                                        prime_width='10um',
                                        prime_gap='5um',
                                        second_width='10um',
                                        second_gap='5um',
                                        open_termination=False,
                                        mirror=False))

    MyCoupledLineTee(design,
                           'TQ9',
                           options=Dict(pos_x=str(-1.3) + 'mm', pos_y=str(-readout_line_y) + 'mm',
                                        orientation='0',
                                        coupling_length=str(40) + 'um',
                                        down_length=str(100) + 'um',
                                        over_length=str(450) + 'um',
                                        coupling_space='3um',
                                        prime_width='10um',
                                        prime_gap='5um',
                                        second_width='10um',
                                        second_gap='5um',
                                        open_termination=False,
                                        mirror=True))

    MyCoupledLineTee(design,
                            'TQ10',
                            options=Dict(pos_x=str(1.3) + 'mm', pos_y=str(-readout_line_y) + 'mm',
                                         orientation='0',
                                         coupling_length=str(100) + 'um',
                                         down_length=str(100) + 'um',
                                         over_length=str(450) + 'um',
                                         coupling_space='3um',
                                         prime_width='10um',
                                         prime_gap='5um',
                                         second_width='10um',
                                         second_gap='5um',
                                         open_termination=False,
                                         mirror=True))
    # gui.rebuild()
    # gui.autoscale()

    # -------------------------------------------------------绘制谐振腔----------------------------------------------
    # whole_length1 = 4.378768750777398 + 1.18
    # whole_length2 = 4.378768750777398 + 1.18
    # whole_length3 = 4.18
    # whole_length4 = 4.378768750777398 + 1.18
    # whole_length5 = 4.378768750777398 + 1.18
    # whole_length6 = 4.18
    # total_length1 = whole_length1 - (coupling_length_qubit + down_length_qubit) * 1e-3
    # total_length2 = whole_length2 - (coupling_length_qubit + down_length_qubit) * 1e-3
    # total_length3 = whole_length3 - (coupling_length_coupler + down_length_coupler) * 1e-3
    # total_length4 = whole_length4 - (coupling_length_qubit + down_length_qubit) * 1e-3
    # total_length5 = whole_length5 - (coupling_length_qubit + down_length_qubit) * 1e-3
    # total_length6 = whole_length6 - (coupling_length_coupler + down_length_coupler) * 1e-3
    whole_length = np.array(
        [3.96564, 3.85023, 3.967587, 4.35408, 4.21541, 4.13567, 4.46816792, 4.27801111, 4.27516252, 4.15380048])
    res_length = np.array(
        [(coupling_length_qubit + down_length_qubit) * 1e-3, (coupling_length_qubit + down_length_qubit) * 1e-3,
         (coupling_length_coupler + down_length_coupler) * 1e-3, (coupling_length_qubit + down_length_qubit) * 1e-3,
         (coupling_length_qubit + down_length_qubit) * 1e-3, (coupling_length_coupler + down_length_coupler) * 1e-3,
         0.14, 0.2, 0.14, 0.2])
    total_length = whole_length - res_length

    jogsS = OrderedDict()
    jogsS[0] = ["R", '0um']
    spacing = 0.1
    ops = dict(fillet=spacing / 2 - 0.001)
    asymmetry = 0
    start_straight = 0.13
    # total_length = total_length[1]
    options1 = Dict(total_length=str(total_length[0]) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ1',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q1', pin='bus_02')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander1 = RouteMeander(design, 'R1', options=options1)

    jogsS = OrderedDict()
    jogsS[0] = ["L", '0um']
    options2 = Dict(total_length=str(total_length[1]) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ2',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q2', pin='bus_02')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander2 = RouteMeander(design, 'R2', options=options2)

    jogsS = OrderedDict()
    jogsS[0] = ["L", '0um']
    options3 = Dict(total_length=str(total_length[2]) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ3',
                                                 pin='second_end'),
                                    start_pin=Dict(component='tunable_coupler1', pin='Control')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander3 = RouteMeander(design, 'R3', options=options3)

    jogsS = OrderedDict()
    jogsS[0] = ["R", '0um']
    options4 = Dict(total_length=str(total_length[3]) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ4',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q3', pin='bus_02')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander4 = RouteMeander(design, 'R4', options=options4)

    jogsS = OrderedDict()
    jogsS[0] = ["L", '0um']
    options5 = Dict(total_length=str(total_length[4]) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ5',
                                                 pin='second_end'),
                                    start_pin=Dict(component='Q4', pin='bus_02')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander5 = RouteMeander(design, 'R5', options=options5)

    jogsS = OrderedDict()
    jogsS[0] = ["R", '0um']
    options6 = Dict(total_length=str(total_length[5]) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='TQ6',
                                                 pin='second_end'),
                                    start_pin=Dict(component='tunable_coupler2', pin='Control')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander6 = RouteMeander(design, 'R6', options=options6)

    # draw bare resonator
    total_length = total_length[6:10]
    open_to_ground_name = 'otg_TQ'
    resonator_num = 4
    tee_name = 'TQ'
    TQ_y = 1.2

    for i in range(1, resonator_num + 1):
        shift_r = design.components[tee_name + str(i + 6)].parse_options().coupling_length / 2
        if design.components[tee_name + str(i + 6)].parse_options().orientation == 180:
            OpenToGround(design, open_to_ground_name + str(i),
                         options=Dict(
                             pos_x=design.components[tee_name + str(i + 6)].get_pin('second_end').middle[0] + shift_r,
                             pos_y=TQ_y, width='10um', gap='5um', orientation='90', ))
            options = Dict(total_length=str(total_length[i - 1]),
                           hfss_wire_bonds=False,
                           pin_inputs=Dict(end_pin=Dict(component=tee_name + str(i + 6),
                                                        pin='second_end'),
                                           start_pin=Dict(component=open_to_ground_name + str(i), pin='open')),
                           lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                           meander=Dict(spacing=spacing, asymmetry=asymmetry),
                           **ops)
            RouteMeander(design, 'R' + str(i + 6), options=options)
        else:
            OpenToGround(design, open_to_ground_name + str(i),
                         options=Dict(
                             pos_x=design.components[tee_name + str(i + 6)].get_pin('second_end').middle[0] - shift_r,
                             pos_y=-TQ_y, width='10um', gap='5um', orientation='-90', ))
            options = Dict(total_length=str(total_length[i - 1]),
                           hfss_wire_bonds=False,
                           pin_inputs=Dict(end_pin=Dict(component=tee_name + str(i + 6),
                                                        pin='second_end'),
                                           start_pin=Dict(component=open_to_ground_name + str(i), pin='open')),
                           lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                           meander=Dict(spacing=spacing, asymmetry=asymmetry),
                           **ops)
            RouteMeander(design, 'R' + str(i + 6), options=options)
    #
    # shift_r = design.components[tee_name + str(i)].parse_options().coupling_length / 2
    #
    # jogsS = OrderedDict()
    # jogsS[0] = ["R", '0um']
    # options7 = Dict(total_length=str(total_length[6]) + 'mm',
    #             hfss_wire_bonds=False,
    #             pin_inputs=Dict(end_pin=Dict(component='TQ7',
    #                                          pin='second_end'),
    #                             start_pin=Dict(component='tunable_coupler2', pin='Control')),
    #             lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
    #             meander=Dict(spacing=spacing, asymmetry=asymmetry),
    #             **ops)
    # meander7 = RouteMeander(design, 'R7', options=options7)
    #
    # jogsS = OrderedDict()
    # jogsS[0] = ["R", '0um']
    # options8 = Dict(total_length=str(total_length[7]) + 'mm',
    #             hfss_wire_bonds=False,
    #             pin_inputs=Dict(end_pin=Dict(component='TQ6',
    #                                          pin='second_end'),
    #                             start_pin=Dict(component='tunable_coupler2', pin='Control')),
    #             lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
    #             meander=Dict(spacing=spacing, asymmetry=asymmetry),
    #             **ops)
    # meander8 = RouteMeander(design, 'R8', options=options8)
    #
    # jogsS = OrderedDict()
    # jogsS[0] = ["R", '0um']
    # options9 = Dict(total_length=str(total_length[8]) + 'mm',
    #             hfss_wire_bonds=False,
    #             pin_inputs=Dict(end_pin=Dict(component='TQ6',
    #                                          pin='second_end'),
    #                             start_pin=Dict(component='tunable_coupler2', pin='Control')),
    #             lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
    #             meander=Dict(spacing=spacing, asymmetry=asymmetry),
    #             **ops)
    # meander9 = RouteMeander(design, 'R9', options=options9)
    #
    # jogsS = OrderedDict()
    # jogsS[0] = ["R", '0um']
    # options10 = Dict(total_length=str(total_length[9]) + 'mm',
    #             hfss_wire_bonds=False,
    #             pin_inputs=Dict(end_pin=Dict(component='TQ6',
    #                                          pin='second_end'),
    #                             start_pin=Dict(component='tunable_coupler2', pin='Control')),
    #             lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
    #             meander=Dict(spacing=spacing, asymmetry=asymmetry),
    #             **ops)
    # meander10 = RouteMeander(design, 'R10', options=options10)
    # gui.rebuild()
    # gui.autoscale()

    # -----------------------------------------------绘制读取线---------------------------------------------------------
    fillet = 100
    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='launchpad16', pin='tie'),
                                   end_pin=Dict(component='TQ1', pin='prime_end'), ), lead=Dict(start_straight=0.01,
                                                                                                end_straight=0.1, ),
                   fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout1_part1', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ1', pin='prime_start'),
                                   end_pin=Dict(component='TQ7', pin='prime_end'), ), lead=Dict(start_straight=0.01,
                                                                                                end_straight=0.1, ),
                   fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout1_part2', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ7', pin='prime_start'),
                                   end_pin=Dict(component='TQ3', pin='prime_end'), ), lead=Dict(start_straight=0.01,
                                                                                                end_straight=0.1, ),
                   fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout1_part3', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ3', pin='prime_start'),
                                   end_pin=Dict(component='TQ8', pin='prime_end'), ), lead=Dict(start_straight=0.01,
                                                                                                end_straight=0.1, ),
                   fillet=str(fillet) + 'um', )
    RoutePathfinder(design, 'readout1_part4', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ8', pin='prime_start'),
                                   end_pin=Dict(component='TQ2', pin='prime_end'), ), lead=Dict(start_straight=0.01,
                                                                                                end_straight=0.1, ),
                   fillet=str(fillet) + 'um', )
    RoutePathfinder(design, 'readout1_part5', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ2', pin='prime_start'),
                                   end_pin=Dict(component='launchpad5', pin='tie'), ), lead=Dict(start_straight=0.01,
                                                                                                 end_straight=0.1, ),
                   fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout1_part6', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='launchpad13', pin='tie'),
                                   end_pin=Dict(component='TQ4', pin='prime_start'), ), lead=Dict(start_straight=0.01,
                                                                                                  end_straight=0.1, ),
                   fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout2_part1', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ4', pin='prime_end'),
                                   end_pin=Dict(component='TQ9', pin='prime_start'), ), lead=Dict(start_straight=0.01,
                                                                                                  end_straight=0.1, ),
                   fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout2_part2', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ9', pin='prime_end'),
                                   end_pin=Dict(component='TQ6', pin='prime_start'), ), lead=Dict(start_straight=0.01,
                                                                                                  end_straight=0.1, ),
                   fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout2_part3', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ6', pin='prime_end'),
                                   end_pin=Dict(component='TQ10', pin='prime_start'), ), lead=Dict(start_straight=0.01,
                                                                                                   end_straight=0.1, ),
                   fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout2_part4', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ10', pin='prime_end'),
                                   end_pin=Dict(component='TQ5', pin='prime_start'), ), lead=Dict(start_straight=0.01,
                                                                                                  end_straight=0.1, ),
                   fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout2_part5', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='TQ5', pin='prime_end'),
                                   end_pin=Dict(component='launchpad8', pin='tie'), ), lead=Dict(start_straight=0.01,
                                                                                                 end_straight=0.1, ),
                   fillet=str(fillet) + 'um')
    RoutePathfinder(design, 'readout2_part6', options=pin_opt)
    # gui.rebuild()
    # gui.autoscale()

    # --------------------------------------------------------绘制控制线---------------------------------------------------
    connector_fillet = 50
    gap = 2
    # xy_gap = 4
    reference_point_x1 = design.components['Q1'].pins.bus_01.middle[0]
    reference_point_y1 = design.components['Q1'].pins.bus_01.middle[1]

    reference_point_x2 = design.components['Q2'].pins.bus_01.middle[0]
    reference_point_y2 = design.components['Q2'].pins.bus_01.middle[1]

    reference_point_x3 = design.components['Q3'].pins.bus_01.middle[0]
    reference_point_y3 = design.components['Q3'].pins.bus_01.middle[1]

    reference_point_x4 = design.components['Q4'].pins.bus_01.middle[0]
    reference_point_y4 = design.components['Q4'].pins.bus_01.middle[1]

    reference_point_x5 = design.components['tunable_coupler2'].pins.Flux.middle[0]
    reference_point_y5 = design.components['tunable_coupler2'].pins.Flux.middle[1]

    connector_shift_x = 0.5
    connector_shift_y = 0.35

    connector_x1 = reference_point_x1 - connector_shift_x
    connector_y1 = reference_point_y1 + connector_shift_y
    connector1 = MyConnector(design, 'connector1',
                             options=Dict(pos_x=connector_x1, pos_y=connector_y1, width='4um', gap=str(gap) + 'um',
                                          width0='10um', gap0='5um', length='10um', orientation='-90'))
    connector_x2 = reference_point_x2 + connector_shift_x
    connector_y2 = reference_point_y2 + connector_shift_y
    connector2 = MyConnector(design, 'connector2',
                             options=Dict(pos_x=connector_x2, pos_y=connector_y2, width='4um', gap=str(gap) + 'um',
                                          width0='10um', gap0='5um', length='10um', orientation='-90'))
    connector_x3 = 0
    connector_y3 = connector_y2
    connector3 = MyConnector(design, 'connector3',
                             options=Dict(pos_x=connector_x3, pos_y=connector_y3, width='4um', gap=str(gap) + 'um',
                                          width0='10um', gap0='5um', length='10um', orientation='-90'))
    connector_x4 = reference_point_x3 - connector_shift_x
    connector_y4 = reference_point_y3 - connector_shift_y
    connector4 = MyConnector(design, 'connector4',
                             options=Dict(pos_x=connector_x4, pos_y=connector_y4, width='4um', gap=str(gap) + 'um',
                                          width0='10um', gap0='5um', length='10um', orientation='90'))
    connector_x5 = reference_point_x4 + connector_shift_x
    connector_y5 = reference_point_y4 - connector_shift_y
    connector5 = MyConnector(design, 'connector5',
                             options=Dict(pos_x=connector_x5, pos_y=connector_y5, width='4um', gap=str(gap) + 'um',
                                          width0='10um', gap0='5um', length='10um', orientation='90'))
    connector_x6 = 0
    connector_y6 = connector_y5
    connector6 = MyConnector(design, 'connector6',
                             options=Dict(pos_x=connector_x6, pos_y=connector_y6, width='4um', gap=str(gap) + 'um',
                                          width0='10um', gap0='5um', length='10um', orientation='90'))
    # connector_x7 = connector_x6 - 0.20
    # connector_y7 = connector_y6
    # connector7 = MyConnector(design, 'connector7',
    #                      options=Dict(pos_x=connector_x7, pos_y=connector_y7, width='4um', gap=str(gap) + 'um',
    #                                   width0='10um', gap0='5um', length='10um', orientation='90'))
    # connector7 = OpenToGround(design, 'connector7',options=Dict(pos_x=connector_x7, pos_y=connector_y7,width='4um',
    #                                                             gap=str(gap)+'um',termination_gap=str(gap)+'um', orientation='-90'))
    gui.rebuild()

    opt1 = Dict(pin_inputs=Dict(start_pin=Dict(component='Q1', pin='bus_01'),
                                end_pin=Dict(component='connector1', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
                                                                                                  end_straight=0.1),
                fillet=str(connector_fillet) + 'um', trace_width='4um', trace_gap='2um')
    RoutePathfinder(design, 'xy1_part1', options=opt1)
    opt1 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector1', pin='c_pin_l'),
                                end_pin=Dict(component='launchpad1', pin='tie'), ), lead=Dict(start_straight=0.150,
                                                                                              end_straight=0.1),
                fillet=str(fillet) + 'um', trace_width='10um', trace_gap='5um')
    RoutePathfinder(design, 'xy1_part2', options=opt1)
    opt2 = Dict(pin_inputs=Dict(start_pin=Dict(component='Q2', pin='bus_01'),
                                end_pin=Dict(component='connector2', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
                                                                                                  end_straight=0.1),
                fillet=str(connector_fillet) + 'um', trace_width='4um', trace_gap='2um')
    RoutePathfinder(design, 'xy2_part1', options=opt2)
    opt2 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector2', pin='c_pin_l'),
                                end_pin=Dict(component='launchpad4', pin='tie'), ), lead=Dict(start_straight=0.350,
                                                                                              end_straight=0.6),
                fillet=str(fillet) + 'um', trace_width='10um', trace_gap='5um')
    RoutePathfinder(design, 'xy2_part2', options=opt2)
    opt3 = Dict(pin_inputs=Dict(start_pin=Dict(component='tunable_coupler1', pin='Flux'),
                                end_pin=Dict(component='connector3', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
                                                                                                  end_straight=0.1),
                fillet=str(connector_fillet) + 'um', trace_width='4um', trace_gap='2um')
    RoutePathfinder(design, 'z1_part1', options=opt3)
    opt3 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector3', pin='c_pin_l'),
                                end_pin=Dict(component='launchpad3', pin='tie'), ), lead=Dict(start_straight=0.150,
                                                                                              end_straight=0.1),
                fillet=str(fillet) + 'um', trace_width='10um', trace_gap='5um')
    RoutePathfinder(design, 'z1_part2', options=opt3)

    jogsS = OrderedDict()
    jogsS[0] = ["R", '0um']

    opt5 = Dict(pin_inputs=Dict(start_pin=Dict(component='Q4', pin='bus_01'),
                                end_pin=Dict(component='connector5', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
                                                                                                  end_straight=0.1,
                                                                                                  start_jogged_extension=jogsS),
                advanced=Dict(avoid_collision=False), fillet=str(connector_fillet) + 'um', trace_width='4um',
                trace_gap='2um')
    RoutePathfinder(design, 'xy4_part1', options=opt5)
    opt5 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector5', pin='c_pin_l'),
                                end_pin=Dict(component='launchpad9', pin='tie'), ), lead=Dict(start_straight=0.150,
                                                                                              end_straight=0.4),
                fillet=str(fillet) + 'um', trace_width='10um', trace_gap='5um')
    RoutePathfinder(design, 'xy4_part2', options=opt5)
    opt6 = Dict(pin_inputs=Dict(start_pin=Dict(component='tunable_coupler2', pin='Flux'),
                                end_pin=Dict(component='connector6', pin='c_pin_r'), ), lead=Dict(start_straight=0.150,
                                                                                                  end_straight=0.1),
                fillet=str(connector_fillet) + 'um', trace_width='4um', trace_gap='2um')
    RoutePathfinder(design, 'z2_part1', options=opt6)
    opt6 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector6', pin='c_pin_l'),
                                end_pin=Dict(component='launchpad10', pin='tie'), ), lead=Dict(start_straight=0.150,
                                                                                               end_straight=0.1),
                fillet=str(fillet) + 'um', trace_width='10um', trace_gap='5um')
    RoutePathfinder(design, 'z2_part2', options=opt6)

    # anchors = OrderedDict()
    # midpoint_x = connector_x6 - 0.12
    # midpoint_y = connector_y6 + 0.14
    # anchors[0] = np.array([midpoint_x, midpoint_y])
    # opt7 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector7', pin='c_pin_r'),
    #                         end_pin=Dict(component='open_coupler2_xyline', pin='open'), ),
    #         lead=Dict(start_straight=0.05,
    #                   end_straight=0.05), advanced=Dict(avoid_collision=False), anchors=anchors, fillet=str(40)+'um',
    #         trace_width='4um', trace_gap='2um')
    # RoutePathfinder(design, 'xy5_part1', options=opt7)
    # opt7 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector7', pin='c_pin_l'),
    #                         end_pin=Dict(component='launchpad11', pin='tie'), ), lead=Dict(start_straight=0.150,
    #                                                                                        end_straight=0.1),
    #         fillet=str(fillet)+'um', trace_width='10um', trace_gap='5um')
    # RoutePathfinder(design, 'xy5_part2', options=opt7)

    jogsS = OrderedDict()
    jogsS[0] = ["L", '0um']
    # anchors = OrderedDict()
    # midpoint_x = connector_x6 - 0.12
    # midpoint_y = connector_y6 + 0.14
    # anchors[0] = np.array([midpoint_x, midpoint_y])

    opt4 = Dict(pin_inputs=Dict(start_pin=Dict(component='Q3', pin='bus_01'),
                                end_pin=Dict(component='connector4', pin='c_pin_r'), ), lead=Dict(start_straight=0.100,
                                                                                                  end_straight=0.1,
                                                                                                  start_jogged_extension=jogsS
                                                                                                  ),
                advanced=Dict(avoid_collision=False), fillet=str(50) + 'um', trace_width='4um', trace_gap='2um')
    RoutePathfinder(design, 'xy3_part1', options=opt4)
    opt4 = Dict(pin_inputs=Dict(start_pin=Dict(component='connector4', pin='c_pin_l'),
                                end_pin=Dict(component='launchpad12', pin='tie'), ), lead=Dict(start_straight=0.150,
                                                                                               end_straight=0.4),
                fillet=str(fillet) + 'um', trace_width='10um', trace_gap='5um')
    RoutePathfinder(design, 'xy3_part2', options=opt4)
    if parameter_file_path is not None:
        parameter_import(design, convert_keys_to_int(load_json(parameter_file_path)))
    if jj_dict is not None:
        design.components['Q1'].options.gds_cell_name = jj_dict['Q1']
        design.components['Q2'].options.gds_cell_name = jj_dict['Q2']
        design.components['Q3'].options.gds_cell_name = jj_dict['Q3']
        design.components['Q4'].options.gds_cell_name = jj_dict['Q4']
        design.components['tunable_coupler1'].options.gds_cell_name = jj_dict['tunable_coupler1']
        design.components['tunable_coupler2'].options.gds_cell_name = jj_dict['tunable_coupler2']
    gui.rebuild()
    gui.autoscale()
    if airbridge is True:
        list0 = []
        list1 = []
        list2 = []
        for i in range(1, 4):
            list0.append(design.components['R' + str(i)])
        for i in range(1, 5):
            list1.append(design.components['readout1_part' + str(i)])
        for i in range(1, 3):
            list2.append(design.components['xy' + str(i) + '_part2'])
        list2.append(design.components['z1_part2'])
        parameter_dict = Dict(pad_width='22 um', etch_residue='-2 um',
                              bridge_length='50um', pad_layer=3, etch_layer=4)
        build_airbridge(design, gui, list_meander=list0, list_controlLine=list2 + list1, parameter_dict=parameter_dict)
    return design, gui



def twenty_qubits_tunable_coupler_layout(parameter_file_path=None, meander_length_list=None, jj_dict=None):
    """"
    含有20个可调耦合器双比特固定频率版图，线性排布
    Default Options:
        *parameter_file_path: 芯片参数文件，比特和耦合器名称分别为'xmon_round0','xmon_round1'和'tunable_coupler'
        * jj_dict: {'Q1':'FakeJunction_01','Q2':'FakeJunction_01'}- 每个比特的约瑟夫森结组成的字典
    """
    design = designs.DesignPlanar()
    # design.overwrite_enabled = True
    design.chips.main.size['size_x'] = '13mm'
    design.chips.main.size['size_y'] = '13mm'
    design.chips['main']['material'] = 'sapphire'
    design.variables.cpw_gap = '5 um'
    design.variables.cpw_width = '10 um'
    gui = MetalGUI(design)

    if parameter_file_path is not None:
        parameter_dict = convert_keys_to_int(load_json(parameter_file_path))

    # ----------------------------------------------------------------------------绘制发射台---------------------------------------------------------#
    points = []
    N = 12  # 网格中每条边上的焊盘数量
    size = 12.5 + 0.35  # 网格的总尺寸（单位：mm）
    pad_pad_space = 0.76  # 焊盘之间的间距（单位：mm）
    edge_gap = (size - (pad_pad_space * (N - 1))) / 2  # 边缘到第一个焊盘的距离

    # 生成网格中的焊盘位置
    for i in range(N):
        shape = draw.Point(-size / 2 + edge_gap + i * pad_pad_space, size / 2 - 0.885)  # 生成上边界焊盘位置
        points.append(shape)

    # 将网格旋转并复制到四个方向
    x = draw.shapely.geometrycollections(points)
    x0 = draw.rotate(x, 90, origin=(0, 0))
    x1 = draw.rotate(x0, 90, origin=(0, 0))
    x2 = draw.rotate(x1, 90, origin=(0, 0))
    square = draw.shapely.geometrycollections([x, x0, x1, x2])

    # 提取所有焊盘的坐标
    square_coords = []
    for i in range(4):
        for j in range(N):
            square_coords.append(square.geoms[i].geoms[j].coords[0])  # 包含四个方向的焊盘位置

    # 定义旋转函数（45度）
    def rotate_point(x, y, angle_degrees=45):
        angle_radians = np.deg2rad(angle_degrees)
        cos_theta = np.cos(angle_radians)
        sin_theta = np.sin(angle_radians)
        new_x = x * cos_theta - y * sin_theta
        new_y = x * sin_theta + y * cos_theta
        return round(new_x, 4), round(new_y, 4)

    # 对所有焊盘坐标进行45度旋转
    rotated_coords = []
    for coord in square_coords:
        rotated_x, rotated_y = rotate_point(coord[0], coord[1])
        rotated_coords.append((rotated_x, rotated_y))

    # 创建焊盘模板
    opt = Dict(pos_x=0, pos_y=0, orientation='-45', pad_width='250 um', pad_height='250 um', pad_gap='100 um',
               lead_length='67 um', chip='main', trace_width='10 um', trace_gap='5 um')
    opt_a = Dict(pos_x=0, pos_y=0, orientation='45', pad_width='250 um', pad_height='250 um', pad_gap='100 um',
                 lead_length='67 um', chip='main', trace_width='10 um', trace_gap='5 um')
    opt_b = Dict(pos_x=0, pos_y=0, orientation='135', pad_width='250 um', pad_height='250 um', pad_gap='100 um',
                 lead_length='67 um', chip='main', trace_width='10 um', trace_gap='5 um')
    opt_c = Dict(pos_x=0, pos_y=0, orientation='-135', pad_width='250 um', pad_height='250 um', pad_gap='100 um',
                 lead_length='67 um', chip='main', trace_width='10 um', trace_gap='5 um')

    launch_line = LaunchpadWirebond(design, 'launch_line', options=opt)
    launch_line_a = LaunchpadWirebond(design, 'launch_line_a', options=opt_a)
    launch_line_b = LaunchpadWirebond(design, 'launch_line_b', options=opt_b)
    launch_line_c = LaunchpadWirebond(design, 'launch_line_c', options=opt_c)

    design.delete_all_components()
    # 复制焊盘模板到指定位置
    launch_list = []
    for i in range(4):
        for j in range(N):
            if i == 0:
                launch_list.append(design.copy_qcomponent(launch_line, 'launch_line' + str(i) + str(j),
                                                          Dict(pos_x=rotated_coords[i * N + j][0],
                                                               pos_y=rotated_coords[i * N + j][1])))
            elif i == 1:
                launch_list.append(design.copy_qcomponent(launch_line_a, 'launch_line' + str(i) + str(j),
                                                          Dict(pos_x=rotated_coords[i * N + j][0],
                                                               pos_y=rotated_coords[i * N + j][1])))
            elif i == 2:
                launch_list.append(design.copy_qcomponent(launch_line_b, 'launch_line' + str(i) + str(j),
                                                          Dict(pos_x=rotated_coords[i * N + j][0],
                                                               pos_y=rotated_coords[i * N + j][1])))
            else:
                launch_list.append(design.copy_qcomponent(launch_line_c, 'launch_line' + str(i) + str(j),
                                                          Dict(pos_x=rotated_coords[i * N + j][0],
                                                               pos_y=rotated_coords[i * N + j][1])))

    # # 删除焊盘模板
    # components_to_delete = ['launch_line', 'launch_line_a', 'launch_line_b', 'launch_line_c']
    # for component_name in components_to_delete:
    #     design.delete_component(component_name)  # 删除组件
    # 定义量子比特的y坐标值（单位：微米）
    qubit_y = -200  # 所有量子比特的y坐标值

    # 生成比特的x位置
    num_qubits = 20
    space = 475  # 相邻比特中心之间的间距，单位：微米
    positions = [(-(num_qubits - 1) * space / 2 + i * space) * 1e-3 for i in range(int(num_qubits))]  # 原点(0,0)左侧10个位置
    cross_width = 24
    cross_gap = 24
    cross_length1 = 210
    cross_length2 = 220
    cross_length = 112

    # 创建20个量子比特
    if parameter_file_path is None:
        for i, pos_x in enumerate(positions):
            # 根据编号奇偶性选择参数
            if (i + 1) % 2 == 1:  # 奇数编号
                options = Dict(
                    pos_x=pos_x,
                    pos_y=f"{qubit_y}um",  # 使用定义的qubit_y
                    orientation="0.0",
                    chip="main",
                    layer="1",
                    connection_pads=dict(
                        bus_02=dict(
                            connector_type="0",
                            claw_length="60um",
                            ground_spacing="2um",
                            claw_width="10um",
                            claw_gap="5um",
                            coupling_width="20um",
                            coupling_gap="5um",
                            coupling_top_width="4um",
                            connector_location="90"
                        )
                    ),
                    cross_width="24um",
                    cross_length="110um",
                    cross_length1="210um",
                    cross_length2="220um",
                    cross_gap="24um",
                    cross_gap2="24um",
                    radius="1 um",
                    rect_width="24um",
                    rect_height="0um",
                    jj_pad_width="8um",
                    jj_pad_height="6um",
                    jj_etch_length="4um",
                    jj_etch_pad1_width="2um",
                    jj_etch_pad2_width="5um",
                    jj_pad2_height="8um",
                    hfss_inductance="10nH",
                    hfss_capacitance=0,
                    hfss_resistance=0,
                    hfss_mesh_kw_jj=7e-06,
                    q3d_inductance="10nH",
                    q3d_capacitance=0,
                    q3d_resistance=0,
                    q3d_mesh_kw_jj=7e-06,
                    gds_cell_name="my_other_junction"
                )
            else:  # 偶数编号
                options = Dict(
                    pos_x=pos_x,
                    pos_y=f"{qubit_y}um",  # 使用定义的qubit_y
                    orientation="0.0",
                    chip="main",
                    layer="1",
                    connection_pads=dict(
                        bus_02=dict(
                            connector_type="0",
                            claw_length="60um",
                            ground_spacing="2um",
                            claw_width="10um",
                            claw_gap="5um",
                            coupling_width="20um",
                            coupling_gap="5um",
                            coupling_top_width="4um",
                            connector_location="90"
                        )
                    ),
                    cross_width="24um",
                    cross_length="110um",
                    cross_length1="210um",
                    cross_length2="220um",
                    cross_gap="24um",
                    cross_gap2="24um",
                    radius="1 um",
                    rect_width="24um",
                    rect_height="0um",
                    jj_pad_width="8um",
                    jj_pad_height="6um",
                    jj_etch_length="4um",
                    jj_etch_pad1_width="2um",
                    jj_etch_pad2_width="5um",
                    jj_pad2_height="8um",
                    hfss_inductance="10nH",
                    hfss_capacitance=0,
                    hfss_resistance=0,
                    hfss_mesh_kw_jj=7e-06,
                    q3d_inductance="10nH",
                    q3d_capacitance=0,
                    q3d_resistance=0,
                    q3d_mesh_kw_jj=7e-06,
                    gds_cell_name="my_other_junction"
                )

            # 创建量子比特
            TransmonCrossRound_v1(design, 'xmon_round' + str(i), options=options)
    else:
        parameter_dict['xmon_round0']['pos_y'] = f"{qubit_y}um"
        parameter_dict['xmon_round1']['pos_y'] = f"{qubit_y}um"
        for i, pos_x in enumerate(positions):
            # 根据编号奇偶性选择参数
            if (i + 1) % 2 == 0:  # 耦数编号
                parameter_dict['xmon_round0']['pos_x'] = str(pos_x) + 'mm'
                options = parameter_dict['xmon_round0']

            else:  # 奇数编号
                parameter_dict['xmon_round1']['pos_x'] = pos_x
                options = parameter_dict['xmon_round1']
            # 创建量子比特
            TransmonCrossRound_v1(design, 'xmon_round' + str(i), options=options)

    for i in range(int(num_qubits)):
        if 5 <= i <= 9 or 15 <= i <= 19:
            design.components['xmon_round' + str(i)].options.orientation = '180'
        # else:
        #     offset_y=1621
        #     orientation=0

    # 生成19个耦合器
    # coupler_offset_y = parameter_dict['tunable_coupler0']['pos_y']
    # coupler_offset_y = float(re.findall(r'-?\d+\.?\d*', coupler_offset_y)[0]) * 1e3  # 提取所有匹配的数字部分
    coupler_offset_y = -116  # 耦合器相对于量子比特的y方向偏移量（单位：微米）
    coupler_y = qubit_y + coupler_offset_y  # 耦合器的y位置
    if parameter_file_path is None:
        for i in range(int(num_qubits - 1)):  # 从 -9 到 9，总共19个位置
            coupler_name = f"tunable_coupler{i}"  # 生成耦合器的名称
            pos_x = positions[i] + (positions[i + 1] - positions[i]) / 2  # 耦合器的x位置
            options1 = Dict(
                pos_x=str(pos_x) + 'mm',
                pos_y=str(coupler_y) + 'um',  # 使用计算后的耦合器y位置
                orientation="0.0",
                chip="main",
                layer="1",
                connection_pads={},
                c_width="326um",
                c_height="28um",
                c_gap="24um",
                m_width="15um",
                jj_pad_width="8um",
                jj_pad_height="6um",
                jj_etch_length="4um",
                jj_etch_pad1_width="2um",
                jj_etch_pad2_width="5um",
                jj_sub_rect_width="275um",
                jj_sub_rect_height="2um",
                fl_length="20um",
                fl_gap="2um",  # 连接Z线
                fl_ground="3um",
                fl_width="4um",  # 连接Z线
                fillet="1um",
                hfss_wire_bonds=False,
                q3d_wire_bonds=False,
                hfss_inductance="10nH",
                hfss_capacitance=0,
                hfss_resistance=0,
                hfss_mesh_kw_jj=7e-06,
                q3d_inductance="10nH",
                q3d_capacitance=0,
                q3d_resistance=0,
                q3d_mesh_kw_jj=7e-06,
                gds_cell_name="my_other_junction"
            )
            # 创建耦合器
            tunable_coupler = MyTunableCoupler02(design, coupler_name, options=options1)
    else:
        coupler_offset_y = parameter_dict['tunable_coupler0']['pos_y']
        coupler_offset_y = float(re.findall(r'-?\d+\.?\d*', coupler_offset_y)[0]) * 1e3  # 提取所有匹配的数字部分
        coupler_y = qubit_y + coupler_offset_y  # 耦合器的y位置
        parameter_dict['tunable_coupler0']['pos_y'] = str(coupler_y) + 'um'
        for i in range(int(num_qubits - 1)):
            coupler_name = f"tunable_coupler{i}"  # 生成耦合器的名称
            pos_x = positions[i] + (positions[i + 1] - positions[i]) / 2  # 耦合器的x位置
            parameter_dict['tunable_coupler0']['pos_x'] = str(pos_x) + 'mm'
            options1 = parameter_dict['tunable_coupler0']
            tunable_coupler = MyTunableCoupler02(design, coupler_name, options=options1)
    for i in range(int(num_qubits - 1)):
        if 5 <= i <= 9 or 15 <= i <= 19:
            design.components['tunable_coupler' + str(i)].options.pos_y = str(qubit_y - coupler_offset_y) + 'um'
            design.components['tunable_coupler' + str(i)].options.orientation = '180'
    if jj_dict is not None:
        for i in range(int(num_qubits)):
            design.components['xmon_round' + str(i)].options.gds_cell_name = jj_dict['xmon_round' + str(i)]
            if i != int(num_qubits - 1):
                design.components['tunable_coupler' + str(i)].options.gds_cell_name = jj_dict[
                    'tunable_coupler' + str(i)]

    # ------------------------------------------建立xy线和z线接口-------------------------------------------------------#
    gap = 2
    xy_gap = 4
    connector_path_length = 120 * 1e-3

    for i in range(20):
        if 5 <= i <= 9 or 15 <= i <= 19:
            reference_point_x = design.components['xmon_round' + str(i)].parse_options().pos_x

            reference_point_y = design.components['xmon_round' + str(i)].parse_options().pos_y + design.components[
                'xmon_round' + str(i)].parse_options().cross_length2 \
                                + design.components[
                                    'xmon_round' + str(i)].parse_options().cross_gap + gap * 1e-3 + xy_gap * 1e-3
            OpenToGround(design, 'open_xmon' + str(i) + '_xyline',
                         options=Dict(pos_x=reference_point_x, pos_y=reference_point_y, width='4um',
                                      gap=str(gap) + 'um', termination_gap=str(gap) + 'um', orientation='-90'))
            MyConnector(design, 'connector_xmon' + str(i),
                        options=Dict(pos_x=reference_point_x, pos_y=reference_point_y + connector_path_length,
                                     orientation='90', width='10um', gap='5um', width0='4um', gap0='2um',
                                     length='10um'))
            if i != 19:
                reference_point_x1 = design.components['tunable_coupler' + str(i)].parse_options().pos_x
                MyConnector(design, 'connector_tunable_coupler' + str(i),
                            options=Dict(pos_x=reference_point_x1, pos_y=reference_point_y + connector_path_length,
                                         orientation='90', width='10um', gap='5um', width0='4um', gap0='2um',
                                         length='10um'))
        else:
            reference_point_x = design.components['xmon_round' + str(i)].parse_options().pos_x
            reference_point_x1 = design.components['tunable_coupler' + str(i)].parse_options().pos_x
            reference_point_y = design.components['xmon_round' + str(i)].parse_options().pos_y - design.components[
                'xmon_round' + str(i)].parse_options().cross_length2 \
                                - design.components[
                                    'xmon_round' + str(i)].parse_options().cross_gap - gap * 1e-3 - xy_gap * 1e-3
            OpenToGround(design, 'open_xmon' + str(i) + '_xyline',
                         options=Dict(pos_x=reference_point_x, pos_y=reference_point_y, width='4um',
                                      gap=str(gap) + 'um', termination_gap=str(gap) + 'um', orientation='90'))
            MyConnector(design, 'connector_xmon' + str(i),
                        options=Dict(pos_x=reference_point_x, pos_y=reference_point_y - connector_path_length,
                                     orientation='-90', width='10um', gap='5um', width0='4um', gap0='2um',
                                     length='10um'))
            MyConnector(design, 'connector_tunable_coupler' + str(i),
                        options=Dict(pos_x=reference_point_x1, pos_y=reference_point_y - connector_path_length,
                                     orientation='-90', width='10um', gap='5um', width0='4um', gap0='2um',
                                     length='10um'))
        RouteStraight(design, 'xmon' + str(i) + '_xy_line_part1', options=Dict(pin_inputs=Dict(start_pin=Dict(  # 起始引脚定义
            component='open_xmon' + str(i) + '_xyline',
            pin='open'),
            end_pin=Dict(  # 结束引脚定义
                component='connector_xmon' + str(i),
                pin='c_pin_l')
        ),
            trace_width='4um',
            trace_gap='2um', ))
        if i != 19:
            RouteStraight(design, 'tunable_coupler' + str(i) + '_xy_line_part1',
                          options=Dict(pin_inputs=Dict(start_pin=Dict(  # 起始引脚定义
                              component='tunable_coupler' + str(i),
                              pin='Flux'),
                              end_pin=Dict(  # 结束引脚定义
                                  component='connector_tunable_coupler' + str(i),
                                  pin='c_pin_l')
                          ),
                              trace_width='4um',
                              trace_gap='2um', ))

    # ---------------------------------------------------------绘制最左边五个量子比特xmon_round6~10的谐振腔读取线耦合部分TQ6~TQ10--------------------------------------------#

    # 定义耦合器的偏移量
    offset_x = 30  # 偏移量的x分量（单位：um）（原-256um）
    coupling_length = 292
    coupling_space = 3
    over_length = (space - coupling_length) / 2

    # 创建TQ6到TQ10耦合器
    for i, pos_x in enumerate(positions):
        qubit_x_value = design.components['xmon_round' + str(i)].parse_options().pos_x * 1e3
        if 5 <= i <= 9:
            offset_y = -1950
            orientation = 180
            down_length = 400
        elif 15 <= i <= 19:
            offset_y = -1650
            orientation = 180
            down_length = 200
        else:
            offset_y = 1650
            orientation = 0
            down_length = 200

        # 计算耦合器的目标位置
        target_x = qubit_x_value + offset_x  # x坐标加上偏移量
        target_y = qubit_y + offset_y  # y坐标加上偏移量

        # 创建耦合器实例
        coupler_name = f"TQ{i}"
        MyCoupledLineTee(design, coupler_name, options=Dict(
            pos_x=str(target_x) + 'um',  # 耦合器的x坐标
            pos_y=str(target_y) + 'um',  # 耦合器的y坐标
            orientation=str(orientation),
            coupling_length=str(coupling_length) + 'um',  # 耦合区域的长度
            coupling_space=str(coupling_space) + 'um',  # 耦合区域的间距
            prime_width='10um',  # 主传输线的宽度
            prime_gap='5um',  # 主传输线的间隙
            second_width='10um',  # 次级传输线的宽度
            second_gap='5um',  # 次级传输线的间隙
            down_length=str(down_length) + 'um',  # 下拉长度（原200um）
            over_length=str(over_length) + 'um',
            fillet='34um',  # 圆角半径
            mirror=True,  # 是否镜像
            open_termination=False,  # 是否开放端
            hfss_wire_bonds=False  # 是否使用HFSS仿真
        ))
    gui.rebuild()

    # -------------------------------------------------绘制左边五个量子比特xmon_round1~5的谐振腔-------------------------------------------------#

    # 定义蛇形传输线的总长度列表（单位：毫米，取到小数点后四位）
    TQ_length_list = []
    for i in range(int(num_qubits)):
        TQ_length = design.components['TQ' + str(i)].parse_options().coupling_length + \
                    design.components['TQ' + str(i)].parse_options().down_length
        TQ_length_list.append(TQ_length)

    if meander_length_list is not None:
        try:
            assert len(meander_length_list) == len(TQ_length_list)
        except:
            raise Exception("The length of meander_length_list must be equal to the number of qubits")
        total_lengths = np.array(meander_length_list) - np.array(TQ_length_list)
    else:
        total_lengths = [3.3716, 3.5051, 3.4007, 3.5366, 3.4286, 3.5706, 3.4573, 3.6020, 3.4881, 3.6353, 3.4771,
                         3.3423, 3.2704, 3.1499, 3.2421, 3.1245, 3.2145, 3.0990, 3.1846, 3.0741]

    # 循环创建尾号为 1 到 5 的蛇形传输线
    for i in range(int(num_qubits)):
        # 定义蛇形传输线的参数模板
        options = Dict(
            total_length=str(total_lengths[i]) + "mm",  # 蛇形传输线的默认总长度
            hfss_wire_bonds=False,
            meander=Dict(
                spacing="69um",  # 蛇形传输线的间距
                # asymmetry="0um"  # 蛇形传输线的不对称性
            ),
            pin_inputs=Dict(end_pin=Dict(component='TQ' + str(i),
                                         pin='second_end'),
                            start_pin=Dict(component='xmon_round' + str(i), pin='bus_02')),
            lead=Dict(
                start_straight="0.2mm",  # 起始直线段的长度
                # start_jogged_extension=OrderedDict([(0, ["R", "0um"])]),  # 起始弯曲
                # end_straight="50um"  # 结束直线部分长度为 577 微米（left_offset_y-leftmost_offset_y）
            ),
            fillet="34um",  # 圆角半径
            snap=True,  # 是否对齐到网格
            prevent_short_edges=True  # 是否防止短边
        )
        # 创建蛇形传输线实例
        StableRouteMeander(design, 'meander' + str(i), options=options)
        print(f'meander{i} 建立')



    # -----------------------------------------------绘制读取线---------------------------------------------------------#

    # 创建 xmon_round0~4 量子比特的读取线

    readout_line_10 = RoutePathfinder(design, 'readout_line_10', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ0',
                pin='prime_start'),  # 起始引脚名称为 prime_start
            end_pin=Dict(  # 结束引脚定义
                component='launch_line03',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='20um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            # start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))
    jogs_start = OrderedDict()
    jogs_start[0] = ["L", '300um']
    jogs_start[1] = ["L", '550um']
    # jogs_start[2] = ["R", '990um']
    # jogs_start[3] = ["R", '650um']

    readout_line_11 = RoutePathfinder(design, 'readout_line_11', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ4',
                pin='prime_end'),  # 起始引脚名称为 prime_end
            end_pin=Dict(  # 结束引脚定义
                component='launch_line04',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '300um']
    jogs_start[1] = ["R", '900um']
    jogs_start[2] = ["L", '990um']
    # jogs_start[3] = ["R", '650um']

    readout_line_20 = RoutePathfinder(design, 'readout_line_20', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ10',
                pin='prime_start'),  # 起始引脚名称为 prime_end
            end_pin=Dict(  # 结束引脚定义
                component='launch_line33',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["L", '300um']
    jogs_start[1] = ["L", '900um']
    jogs_start[2] = ["R", '990um']
    # jogs_start[3] = ["R", '650um']

    readout_line_21 = RoutePathfinder(design, 'readout_line_21', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ14',
                pin='prime_end'),  # 起始引脚名称为 prime_end
            end_pin=Dict(  # 结束引脚定义
                component='launch_line34',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["L", '300um']
    jogs_start[1] = ["L", '900um']
    jogs_start[2] = ["R", '990um']
    # jogs_start[3] = ["R", '650um']

    readout_line_30 = RoutePathfinder(design, 'readout_line_30', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ5',
                pin='prime_end'),
            end_pin=Dict(  # 结束引脚定义
                component='launch_line14',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))
    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '300um']
    jogs_start[1] = ["R", '900um']
    jogs_start[2] = ["L", '990um']
    # jogs_start[3] = ["R", '650um']

    readout_line_31 = RoutePathfinder(design, 'readout_line_31', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ9',
                pin='prime_start'),
            end_pin=Dict(  # 结束引脚定义
                component='launch_line13',
                pin='tie')
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["L", '300um']
    jogs_start[1] = ["L", '550um']
    # jogs_start[3] = ["R", '650um']

    readout_line_40 = RoutePathfinder(design, 'readout_line_40', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ15',
                pin='prime_end'),
            end_pin=Dict(  # 结束引脚定义
                component='launch_line24',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))
    readout_line_41 = RoutePathfinder(design, 'readout_line_41', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='TQ19',
                pin='prime_start'),
            end_pin=Dict(
                component='launch_line23',
                pin='tie')
        ),
        lead=Dict(
            start_straight='110um',
            end_straight='100um',
            # start_jogged_extension=jogs_start
        ),
        fillet='100um',
        trace_width='10um',
        trace_gap='5um',

    ))
    # -------------------------------------------开始布线-------------------------------------------------------------------------
    # 最左边3根线
    line_space_y = 120
    initial_y = 100
    line_space_x = 150
    initial_x = 350
    for i in range(3):
        if i % 2 == 0:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'

        jogs_start = OrderedDict()
        jogs_start[0] = ["R", str(initial_x + i * (space / 2 + line_space_x)) + 'um']
        jogs_start[1] = ["R", '1000um']
        # jogs_start[3] = ["R", '650um']d
        RoutePathfinder(design, path_name + str(int(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(
                    component=name + str(int(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component='launch_line0' + str(2 - i),
                    pin='tie')
            ),
            lead=Dict(
                start_straight=str(initial_y + i * line_space_y) + 'um',
                end_straight='100um',
                start_jogged_extension=jogs_start
            ),
            fillet='80um',
            trace_width='10um',
            trace_gap='5um',

        ))

    # 左边第4根线
    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '800um']
    # jogs_start[1] = ["R", '1800um']
    # jogs_start[3] = ["R", '650um']
    RoutePathfinder(design, 'tunable_coupler' + str(1) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='connector_tunable_coupler' + str(1),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line111',
                pin='tie')
        ),
        lead=Dict(
            start_straight='460um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='80um',
        trace_width='10um',
        trace_gap='5um',
    ))

    # 第5根线，对齐接口和连接器的y值
    end_straight = 100
    y1 = design.components['launch_line110'].pins['tie']['middle'][1] * 1e3 + end_straight * math.cos(math.radians(45))
    y2 = design.components['connector_xmon2'].pins['c_pin_r']['middle'][1] * 1e3
    delta_y = abs(y1 - y2)

    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '800um']
    # jogs_start[1] = ["R", '1000um']
    # jogs_start[3] = ["R", '650um']d
    RoutePathfinder(design, 'xmon' + str(2) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_xmon' + str(2),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line110',
                pin='tie')
        ),
        lead=Dict(  # 定义引线部分
            start_straight=str(delta_y) + 'um',
            end_straight=str(end_straight) + 'um',
            start_jogged_extension=jogs_start
        ),
        fillet='80um',
        trace_width='10um',
        trace_gap='5um',
        # 设置传输线中的间隙
    ))
    # 第6-10根线
    for i in range(5, 10):
        if i % 2 == 0:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'

        jogs_start = OrderedDict()
        jogs_start[0] = ["R", '800um']
        # # jogs_start[1] = ["R", '1800um']
        # # jogs_start[3] = ["R", '650um']
        RoutePathfinder(design, path_name + str(int(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(  # 定义引脚输入
                start_pin=Dict(  # 起始引脚定义
                    component=name + str(int(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component='launch_line' + str(24 - i),
                    pin='tie')
            ),
            lead=Dict(  # 定义引线部分
                start_straight=str(delta_y + (i - 4) * line_space_y) + 'um',
                end_straight='100um',
                start_jogged_extension=jogs_start
            ),
            fillet='80um',
            trace_width='10um',
            trace_gap='5um',

        ))

    # 第11,12,13根线
    jogs_start = OrderedDict()
    jogs_start[0] = ["R45", '100um']
    jogs_start[1] = ["L45", '1000um']
    # jogs_start[3] = ["R", '650um']
    RoutePathfinder(design, 'xmon' + str(5) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_xmon' + str(5),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line05',
                pin='tie')
        ),
        lead=Dict(
            start_straight='1000um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='50um',
        trace_width='10um',
        trace_gap='5um',
        # 设置传输线中的间隙
    ))

    RoutePathfinder(design, 'tunable_coupler' + str(5) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_tunable_coupler' + str(5),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line06',
                pin='tie')
        ),
        lead=Dict(
            start_straight='1000um',
            end_straight='100um',
            # start_jogged_extension=jogs_start
        ),
        fillet='100um',
        trace_width='10um',
        trace_gap='5um',
    ))
    RoutePathfinder(design, 'xmon' + str(6) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='connector_xmon' + str(6),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line07',
                pin='tie')
        ),
        lead=Dict(
            start_straight='1000um',
            end_straight='100um',
            # start_jogged_extension=jogs_start
        ),
        fillet='100um',
        trace_width='10um',
        trace_gap='5um',
    ))

    # 14-20根线
    delta_y1 = 0
    delta_y2 = 350
    delta_x1 = 45
    delta_x2 = 30
    fillet = 100
    for i in range(7):
        skew_line_length = 400 - i * delta_x1
        if skew_line_length <= 2 * fillet:
            fillet = skew_line_length / 2 - 5
        if i % 2 == 1:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'
        if i < 3:
            launch_line_name = 'launch_line' + str(32 - i)
        else:
            launch_line_name = 'launch_line0' + str(14 - i)
        if i <= 4:
            jogs_start = OrderedDict()
            jogs_start[0] = ["L45", str(400 - i * delta_x1) + 'um']
            jogs_start[1] = ["R45", str(2000 + i * delta_y2) + 'um']
            jogs_start[2] = ["R", str(900 - delta_x2 * i) + 'um']
            jogs_start[3] = ["L", '100um']
        else:
            jogs_start = OrderedDict()
            jogs_start[0] = ["L45", str(400 - i * delta_x1) + 'um']
            jogs_start[1] = ["R45", str(2000) + 'um']
        RoutePathfinder(design, path_name + str(9 - int(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(  # 定义引脚输入
                start_pin=Dict(  # 起始引脚定义
                    component=name + str(9 - int(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component=launch_line_name,
                    pin='tie')
            ),
            lead=Dict(  # 定义引线部分
                start_straight=str(1100 - i * delta_y1) + 'um',
                end_straight='100um',
                start_jogged_extension=jogs_start
            ),
            fillet=str(fillet) + 'um',
            trace_width='10um',
            trace_gap='5um',

        ))

    # 第21,22,23根线
    jogs_start = OrderedDict()
    jogs_start[0] = ["L45", '100um']
    jogs_start[1] = ["R45", '1500um']
    jogs_start[2] = ["R", '800um']
    RoutePathfinder(design, 'xmon' + str(10) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_xmon' + str(10),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line12',
                pin='tie')
        ),
        lead=Dict(
            start_straight='1250um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='50um',
        trace_width='10um',
        trace_gap='5um',
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '800um']
    RoutePathfinder(design, 'tunable_coupler' + str(10) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_tunable_coupler' + str(10),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line11',
                pin='tie')
        ),
        lead=Dict(
            start_straight='3000um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='100um',
        trace_width='10um',
        trace_gap='5um',
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["R45", '100um']
    jogs_start[1] = ["L45", '1500um']
    # jogs_start[2] = ["R", '800um']
    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '800um']
    RoutePathfinder(design, 'xmon' + str(11) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='connector_xmon' + str(11),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line10',
                pin='tie')
        ),
        lead=Dict(
            start_straight='3200um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='100um',
        trace_width='10um',
        trace_gap='5um',
    ))

    # 24-30根线
    delta_y1 = 0
    delta_y2 = 350
    delta_x1 = 45
    delta_x2 = 30
    fillet = 80
    jog1 = 1000
    for i in range(7):
        skew_line_length = 400 - i * delta_x1
        if skew_line_length <= 2 * fillet:
            fillet = skew_line_length / 2 - 5
        if i % 2 == 1:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'

        if i == 6:
            jog1 = 2600
        launch_line_name = 'launch_line2' + str(5 + i)

        jogs_start = OrderedDict()
        jogs_start[0] = ["R45", str(450 - i * delta_x1) + 'um']
        jogs_start[1] = ["L45", str(jog1) + 'um']
        RoutePathfinder(design, path_name + str(14 - int(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(  # 定义引脚输入
                start_pin=Dict(  # 起始引脚定义
                    component=name + str(14 - int(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component=launch_line_name,
                    pin='tie')
            ),
            lead=Dict(
                start_straight=str(1100 - i * delta_y1) + 'um',
                end_straight='50um',
                start_jogged_extension=jogs_start
            ),
            fillet=str(fillet) + 'um',
            trace_width='10um',
            trace_gap='5um',
        ))

    # 第37,38,39（最右边）根线
    line_space_y = 120
    initial_y = 100
    line_space_x = 150
    initial_x = 350
    for i in range(3):
        if i % 2 == 0:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'

        jogs_start = OrderedDict()
        jogs_start[0] = ["R", str(initial_x + i * (space / 2 + line_space_x)) + 'um']
        jogs_start[1] = ["R", '500um']
        # jogs_start[3] = ["R", '650um']d
        RoutePathfinder(design, path_name + str(19 - math.ceil(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(
                    component=name + str(19 - math.ceil(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component='launch_line2' + str(2 - i),
                    pin='tie')
            ),
            lead=Dict(
                start_straight=str(initial_y + i * line_space_y) + 'um',
                end_straight='600um',
                start_jogged_extension=jogs_start
            ),
            fillet='50um',
            trace_width='10um',
            trace_gap='5um',
        ))

    # 32-36根线
    for i in range(5):
        if i % 2 == 1:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'

        RoutePathfinder(design, path_name + str(17 - int(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(
                    component=name + str(17 - int(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component='launch_line3' + str(11 - i),
                    pin='tie')
            ),
            lead=Dict(
                start_straight='100um',
                end_straight='100um',
                # start_jogged_extension=jogs_start
            ),
            fillet='80um',
            trace_width='10um',
            trace_gap='5um',
        ))

    # 第31根线
    jogs_start = OrderedDict()
    jogs_start[0] = ["R45", '120um']
    jogs_start[1] = ["L45", '200um']
    # jogs_start[2] = ["R", '800um']
    RoutePathfinder(design, 'xmon15_xy_line_part2', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='connector_xmon15',
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line36',
                pin='tie')
        ),
        lead=Dict(
            start_straight='960um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='60um',
        trace_width='10um',
        trace_gap='5um',
    ))
    if parameter_file_path is not None:
        for key in parameter_dict:
            if 'meander' in key:
                parameter_import(design, parameter_dict)
                break
    gui.rebuild()

    return design, gui


def twenty_qubits_tunable_coupler_layout_v1(parameter_file_path=None,jj_dict=None,airbridege=False,version='1.00'):
    design = designs.DesignPlanar()
    # design.overwrite_enabled = True
    design.chips.main.size['size_x'] = '13mm'
    design.chips.main.size['size_y'] = '13mm'
    design.chips['main']['material'] = 'sapphire'
    design.variables.cpw_gap = '5 um'
    design.variables.cpw_width = '10 um'
    gui = MetalGUI(design)

    # ----------------------------------------------------------------------------绘制发射台---------------------------------------------------------#
    points = []
    N = 12  # 网格中每条边上的焊盘数量
    size = 12.5 + 0.35 - (0.300*2-0.088*2)  # 网格的总尺寸（单位：mm）
    pad_pad_space = 0.76  # 焊盘之间的间距（单位：mm）
    edge_gap = (size - (pad_pad_space * (N - 1))) / 2  # 边缘到第一个焊盘的距离
    digits = [int(char) for char in version if char.isdigit()]
    number = digits[0]
    decimal1 = digits[1]
    decimal2 = digits[2]

    # 生成网格中的焊盘位置
    for i in range(N):
        shape = draw.Point(-size / 2 + edge_gap + i * pad_pad_space, size / 2 - 0.885)  # 生成上边界焊盘位置
        points.append(shape)

    # 将网格旋转并复制到四个方向
    x = draw.shapely.geometrycollections(points)
    x0 = draw.rotate(x, 90, origin=(0, 0))
    x1 = draw.rotate(x0, 90, origin=(0, 0))
    x2 = draw.rotate(x1, 90, origin=(0, 0))
    square = draw.shapely.geometrycollections([x, x0, x1, x2])

    # 提取所有焊盘的坐标
    square_coords = []
    for i in range(4):
        for j in range(N):
            square_coords.append(square.geoms[i].geoms[j].coords[0])  # 包含四个方向的焊盘位置

    # 定义旋转函数（45度）
    def rotate_point(x, y, angle_degrees=45):
        angle_radians = np.deg2rad(angle_degrees)
        cos_theta = np.cos(angle_radians)
        sin_theta = np.sin(angle_radians)
        new_x = x * cos_theta - y * sin_theta
        new_y = x * sin_theta + y * cos_theta
        return round(new_x, 4), round(new_y, 4)

    # 对所有焊盘坐标进行45度旋转
    rotated_coords = []
    for coord in square_coords:
        rotated_x, rotated_y = rotate_point(coord[0], coord[1])
        rotated_coords.append((rotated_x, rotated_y))

    # 创建焊盘模板
    opt = Dict(pos_x=0, pos_y=0, orientation='-45', pad_width='250 um', pad_height='250 um', pad_gap='100 um',
               lead_length='67 um', chip='main', trace_width='10 um', trace_gap='5 um')
    opt_a = Dict(pos_x=0, pos_y=0, orientation='45', pad_width='250 um', pad_height='250 um', pad_gap='100 um',
                 lead_length='67 um', chip='main', trace_width='10 um', trace_gap='5 um')
    opt_b = Dict(pos_x=0, pos_y=0, orientation='135', pad_width='250 um', pad_height='250 um', pad_gap='100 um',
                 lead_length='67 um', chip='main', trace_width='10 um', trace_gap='5 um')
    opt_c = Dict(pos_x=0, pos_y=0, orientation='-135', pad_width='250 um', pad_height='250 um', pad_gap='100 um',
                 lead_length='67 um', chip='main', trace_width='10 um', trace_gap='5 um')

    launch_line = LaunchpadWirebond(design, 'launch_line', options=opt)
    launch_line_a = LaunchpadWirebond(design, 'launch_line_a', options=opt_a)
    launch_line_b = LaunchpadWirebond(design, 'launch_line_b', options=opt_b)
    launch_line_c = LaunchpadWirebond(design, 'launch_line_c', options=opt_c)

    design.delete_all_components()
    # 复制焊盘模板到指定位置
    launch_list = []
    for i in range(4):
        for j in range(N):
            if i == 0:
                launch_list.append(design.copy_qcomponent(launch_line, 'launch_line' + str(i) + str(j),
                                                          Dict(pos_x=rotated_coords[i * N + j][0],
                                                               pos_y=rotated_coords[i * N + j][1])))
            elif i == 1:
                launch_list.append(design.copy_qcomponent(launch_line_a, 'launch_line' + str(i) + str(j),
                                                          Dict(pos_x=rotated_coords[i * N + j][0],
                                                               pos_y=rotated_coords[i * N + j][1])))
            elif i == 2:
                launch_list.append(design.copy_qcomponent(launch_line_b, 'launch_line' + str(i) + str(j),
                                                          Dict(pos_x=rotated_coords[i * N + j][0],
                                                               pos_y=rotated_coords[i * N + j][1])))
            else:
                launch_list.append(design.copy_qcomponent(launch_line_c, 'launch_line' + str(i) + str(j),
                                                          Dict(pos_x=rotated_coords[i * N + j][0],
                                                             pos_y=rotated_coords[i * N + j][1])))
    if version != '0.00':
        options = {
            'orientation': '-45',
            'number': number,
            'decimal1': decimal1,
            'decimal2': decimal2,
            'width': '15um',  # 笔画宽度
            'height': '50um',  # 数字高度
            'pos_x': str(0.35)+'mm',
            'pos_y': str(-7.3)+'mm',
            'spacing': '30um',
        }
        NumberComponent(design, name='number1', options=options)
    # 定义量子比特的y坐标值（单位：微米）
    qubit_y = -200  # 所有量子比特的y坐标值

    # 生成比特的x位置
    num_qubits = 20
    space = 475  # 相邻比特中心之间的间距，单位：微米
    positions = [(-(num_qubits - 1) * space / 2 + i * space) * 1e-3 for i in range(int(num_qubits))]  # 原点(0,0)左侧10个位置
    cross_width = 24
    cross_gap = 24
    cross_length1 = 210
    cross_length2 = 220
    cross_length = 112

    # 创建20个量子比特
    for i, pos_x in enumerate(positions):
        # 根据编号奇偶性选择参数
        if (i + 1) % 2 == 1:  # 奇数编号
            options = Dict(
                pos_x=pos_x,
                pos_y=f"{qubit_y}um",  # 使用定义的qubit_y
                orientation="0.0",
                chip="main",
                layer="1",
                connection_pads=dict(
                    bus_02=dict(
                        connector_type="0",
                        claw_length="60um",
                        ground_spacing="2um",
                        claw_width="10um",
                        claw_gap="5um",
                        coupling_width="20um",
                        coupling_gap="5um",
                        coupling_top_width="10um",
                        connector_location="90"
                    ),
                    bus_01=dict(connector_type='4',
                                connector_location='270',
                                zline_direction='1',
                                claw_width='4um',
                                coupling_gap='2um'
                                ),
                ),
                cross_width="24um",
                cross_length="110um",
                cross_length1="210um",
                cross_length2="220um",
                cross_gap="24um",
                cross_gap2="24um",
                radius="1 um",
                rect_width="24um",
                rect_height="0um",
                jj_pad_width="8um",
                jj_pad_height="6um",
                jj_etch_length="4um",
                jj_etch_pad1_width="2um",
                jj_etch_pad2_width="5um",
                jj_pad2_height="8um",
                hfss_inductance="10nH",
                hfss_capacitance=0,
                hfss_resistance=0,
                hfss_mesh_kw_jj=7e-06,
                q3d_inductance="10nH",
                q3d_capacitance=0,
                q3d_resistance=0,
                q3d_mesh_kw_jj=7e-06,
                gds_cell_name="my_other_junction"
            )
        else:  # 偶数编号
            options = Dict(
                pos_x=pos_x,
                pos_y=f"{qubit_y}um",  # 使用定义的qubit_y
                orientation="0.0",
                chip="main",
                layer="1",
                connection_pads=dict(
                    bus_02=dict(
                        connector_type="0",
                        claw_length="60um",
                        ground_spacing="2um",
                        claw_width="10um",
                        claw_gap="5um",
                        coupling_width="20um",
                        coupling_gap="5um",
                        coupling_top_width="10um",
                        connector_location="90"
                    ),
                    bus_01=dict(connector_type='4',
                                connector_location='270',
                                zline_direction='1',
                                claw_width='4um',
                                coupling_gap='2um'
                                ),
                ),
                cross_width="24um",
                cross_length="110um",
                cross_length1="210um",
                cross_length2="220um",
                cross_gap="24um",
                cross_gap2="24um",
                radius="1 um",
                rect_width="24um",
                rect_height="0um",
                jj_pad_width="8um",
                jj_pad_height="6um",
                jj_etch_length="4um",
                jj_etch_pad1_width="2um",
                jj_etch_pad2_width="5um",
                jj_pad2_height="8um",
                hfss_inductance="10nH",
                hfss_capacitance=0,
                hfss_resistance=0,
                hfss_mesh_kw_jj=7e-06,
                q3d_inductance="10nH",
                q3d_capacitance=0,
                q3d_resistance=0,
                q3d_mesh_kw_jj=7e-06,
                gds_cell_name="my_other_junction"
            )

        # 创建量子比特
        TransmonCrossRound_v1(design, 'xmon_round' + str(i), options=options)

    for i in range(int(num_qubits)):
        if 5 <= i <= 9 or 15 <= i <= 19:
            design.components['xmon_round' + str(i)].options.orientation = '180'

    # 生成19个耦合器
    qc_gap = 3
    c_gap = 17
    c_height = 36
    coupler_offset_y = -(cross_width/2 + cross_gap + qc_gap + c_gap + c_height/2)
    # coupler_offset_y = -116  # 耦合器相对于量子比特的y方向偏移量（单位：微米）
    coupler_y = qubit_y + coupler_offset_y  # 耦合器的y位置
    for i in range(int(num_qubits - 1)):  # 从 -9 到 9，总共19个位置
        coupler_name = f"tunable_coupler{i}"  # 生成耦合器的名称
        pos_x = positions[i] + (positions[i + 1] - positions[i]) / 2  # 耦合器的x位置
        options1 = Dict(
            pos_x=str(pos_x) + 'mm',
            pos_y=str(coupler_y) + 'um',  # 使用计算后的耦合器y位置
            orientation="0.0",
            chip="main",
            layer="1",
            connection_pads={},
            c_width="326um",
            c_height=f"{c_height}um",
            c_gap=f"{c_gap}um",
            m_width="15um",
            jj_pad_width="8um",
            jj_pad_height="6um",
            jj_etch_length="4um",
            jj_etch_pad1_width="2um",
            jj_etch_pad2_width="5um",
            jj_sub_rect_width="275um",
            jj_sub_rect_height="2um",
            fl_length="20um",
            fl_gap="2um",  # 连接Z线
            fl_ground="3um",
            fl_width="4um",  # 连接Z线
            fillet="1um",
            hfss_wire_bonds=False,
            q3d_wire_bonds=False,
            hfss_inductance="10nH",
            hfss_capacitance=0,
            hfss_resistance=0,
            hfss_mesh_kw_jj=7e-06,
            q3d_inductance="10nH",
            q3d_capacitance=0,
            q3d_resistance=0,
            q3d_mesh_kw_jj=7e-06,
            gds_cell_name="my_other_junction"
        )
        # 创建耦合器
        tunable_coupler = MyTunableCoupler02(design, coupler_name, options=options1)

    for i in range(int(num_qubits - 1)):
        if 5 <= i <= 9 or 15 <= i <= 19:
            design.components['tunable_coupler' + str(i)].options.pos_y = str(qubit_y - coupler_offset_y) + 'um'
            design.components['tunable_coupler' + str(i)].options.orientation = '180'


    # ------------------------------------------建立xy线和z线接口-------------------------------------------------------#
    gap = 2
    xy_gap = 4
    connector_path_length = 120 * 1e-3

    for i in range(20):
        if 5 <= i <= 9 or 15 <= i <= 19:
            reference_point_x = design.components['xmon_round' + str(i)].parse_options().pos_x

            reference_point_y = design.components['xmon_round' + str(i)].parse_options().pos_y + design.components[
                'xmon_round' + str(i)].parse_options().cross_length2 \
                                + design.components[
                                    'xmon_round' + str(i)].parse_options().cross_gap + gap * 1e-3 + xy_gap * 1e-3

            MyConnector(design, 'connector_xmon' + str(i),
                        options=Dict(pos_x=reference_point_x, pos_y=reference_point_y + connector_path_length,
                                     orientation='90', width='10um', gap='5um', width0='4um', gap0='2um',
                                     length='10um'))
            if i != 19:
                reference_point_x1 = design.components['tunable_coupler' + str(i)].parse_options().pos_x
                MyConnector(design, 'connector_tunable_coupler' + str(i),
                            options=Dict(pos_x=reference_point_x1, pos_y=reference_point_y + connector_path_length,
                                         orientation='90', width='10um', gap='5um', width0='4um', gap0='2um',
                                         length='10um'))
        else:
            reference_point_x = design.components['xmon_round' + str(i)].parse_options().pos_x
            reference_point_x1 = design.components['tunable_coupler' + str(i)].parse_options().pos_x
            reference_point_y = design.components['xmon_round' + str(i)].parse_options().pos_y - design.components[
                'xmon_round' + str(i)].parse_options().cross_length2 \
                                - design.components[
                                    'xmon_round' + str(i)].parse_options().cross_gap - gap * 1e-3 - xy_gap * 1e-3

            MyConnector(design, 'connector_xmon' + str(i),
                        options=Dict(pos_x=reference_point_x, pos_y=reference_point_y - connector_path_length,
                                     orientation='-90', width='10um', gap='5um', width0='4um', gap0='2um',
                                     length='10um'))
            MyConnector(design, 'connector_tunable_coupler' + str(i),
                        options=Dict(pos_x=reference_point_x1, pos_y=reference_point_y - connector_path_length,
                                     orientation='-90', width='10um', gap='5um', width0='4um', gap0='2um',
                                     length='10um'))
        RouteStraight(design, 'xmon' + str(i) + '_xy_line_part1' , options=Dict(pin_inputs=Dict(start_pin=Dict(  # 起始引脚定义
            component='xmon_round' + str(i),
            pin='bus_01'),
            end_pin=Dict(  # 结束引脚定义
                component='connector_xmon' + str(i),
                pin='c_pin_l')
        ),
            trace_width='4um',
            trace_gap='2um', ))
        if i != 19:
            RouteStraight(design, 'tunable_coupler' + str(i) + '_xy_line_part1',
                          options=Dict(pin_inputs=Dict(start_pin=Dict(  # 起始引脚定义
                              component='tunable_coupler' + str(i),
                              pin='Flux'),
                              end_pin=Dict(  # 结束引脚定义
                                  component='connector_tunable_coupler' + str(i),
                                  pin='c_pin_l')
                          ),
                              trace_width='4um',
                              trace_gap='2um', ))


    # ---------------------------------------------------------绘制最左边五个量子比特xmon_round6~10的谐振腔读取线耦合部分TQ6~TQ10--------------------------------------------#

    # 定义耦合器的偏移量
    offset_x = 30  # 偏移量的x分量（单位：um）（原-256um）
    coupling_length = 292
    coupling_space = 3
    over_length = (space - coupling_length) / 2

    # 创建TQ6到TQ10耦合器
    for i, pos_x in enumerate(positions):
        qubit_x_value = design.components['xmon_round' + str(i)].parse_options().pos_x * 1e3
        if 5 <= i <= 9:
            offset_y = -1950
            orientation = 180
            down_length = 400
        elif 15 <= i <= 19:
            offset_y = -1650
            orientation = 180
            down_length = 200
        else:
            offset_y = 1650
            orientation = 0
            down_length = 200

        # 计算耦合器的目标位置
        target_x = qubit_x_value + offset_x  # x坐标加上偏移量
        target_y = qubit_y + offset_y  # y坐标加上偏移量

        # 创建耦合器实例
        coupler_name = f"TQ{i}"
        MyCoupledLineTee(design, coupler_name, options=Dict(
            pos_x=str(target_x) + 'um',  # 耦合器的x坐标
            pos_y=str(target_y) + 'um',  # 耦合器的y坐标
            orientation=str(orientation),
            coupling_length=str(coupling_length) + 'um',  # 耦合区域的长度
            coupling_space=str(coupling_space) + 'um',  # 耦合区域的间距
            prime_width='10um',  # 主传输线的宽度
            prime_gap='5um',  # 主传输线的间隙
            second_width='10um',  # 次级传输线的宽度
            second_gap='5um',  # 次级传输线的间隙
            down_length=str(down_length) + 'um',  # 下拉长度（原200um）
            over_length=str(over_length) + 'um',
            fillet='34um',  # 圆角半径
            mirror=True,  # 是否镜像
            open_termination=False,  # 是否开放端
            hfss_wire_bonds=False  # 是否使用HFSS仿真
        ))
    gui.rebuild()

    # -------------------------------------------------绘制左边五个量子比特xmon_round1~5的谐振腔-------------------------------------------------#

    # 定义蛇形传输线的总长度列表（单位：毫米，取到小数点后四位）
    TQ_length_list = []
    for i in range(int(num_qubits)):
        TQ_length = design.components['TQ' + str(i)].parse_options().coupling_length + \
                    design.components['TQ' + str(i)].parse_options().down_length
        TQ_length_list.append(TQ_length)

    # if meander_length_list is not None:
    #     try:
    #         assert len(meander_length_list) == len(TQ_length_list)
    #     except:
    #         raise Exception("The length of meander_length_list must be equal to the number of qubits")
    #     total_lengths = np.array(meander_length_list) - np.array(TQ_length_list)
    # else:
    total_lengths = [3.3716, 3.5051, 3.4007, 3.5366, 3.4286, 3.5706, 3.4573, 3.6020, 3.4881, 3.6353, 3.4771,
                    3.3423, 3.2704, 3.1499, 3.2421, 3.1245, 3.2145, 3.0990, 3.1846, 3.0741]

    # 循环创建尾号为 1 到 5 的蛇形传输线
    for i in range(int(num_qubits)):
        # 定义蛇形传输线的参数模板
        options = Dict(
            total_length=str(total_lengths[i]) + "mm",  # 蛇形传输线的默认总长度
            hfss_wire_bonds=False,
            meander=Dict(
                spacing="68.01um",  # 蛇形传输线的间距
                asymmetry="0um"  # 蛇形传输线的不对称性
            ),
            pin_inputs=Dict(end_pin=Dict(component='TQ' + str(i),
                                         pin='second_end'),
                            start_pin=Dict(component='xmon_round' + str(i), pin='bus_02')),
            lead=Dict(
                start_straight="0.2mm",  # 起始直线段的长度
                # start_jogged_extension=OrderedDict([(0, ["R", "0um"])]),  # 起始弯曲
                # end_straight="50um"  # 结束直线部分长度为 577 微米（left_offset_y-leftmost_offset_y）
            ),
            fillet="34um",  # 圆角半径
            snap=True,  # 是否对齐到网格
            prevent_short_edges=True  # 是否防止短边
        )
        # 创建蛇形传输线实例
        StableRouteMeander(design, 'meander' + str(i), options=options)

    # -----------------------------------------------绘制读取线---------------------------------------------------------#
    # 创建 xmon_round0~4 量子比特的读取线
    readout_line_10 = RoutePathfinder(design, 'readout_line_10', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ0',
                pin='prime_start'),  # 起始引脚名称为 prime_start
            end_pin=Dict(  # 结束引脚定义
                component='launch_line03',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='20um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            # start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))
    jogs_start = OrderedDict()
    jogs_start[0] = ["L", '300um']
    jogs_start[1] = ["L", '550um']
    # jogs_start[2] = ["R", '990um']
    # jogs_start[3] = ["R", '650um']

    readout_line_11 = RoutePathfinder(design, 'readout_line_11', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ4',
                pin='prime_end'),  # 起始引脚名称为 prime_end
            end_pin=Dict(  # 结束引脚定义
                component='launch_line04',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '300um']
    jogs_start[1] = ["R", '900um']
    jogs_start[2] = ["L", '990um']
    # jogs_start[3] = ["R", '650um']

    readout_line_20 = RoutePathfinder(design, 'readout_line_20', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ10',
                pin='prime_start'),  # 起始引脚名称为 prime_end
            end_pin=Dict(  # 结束引脚定义
                component='launch_line33',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["L", '300um']
    jogs_start[1] = ["L", '900um']
    jogs_start[2] = ["R", '990um']
    # jogs_start[3] = ["R", '650um']

    readout_line_21 = RoutePathfinder(design, 'readout_line_21', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ14',
                pin='prime_end'),  # 起始引脚名称为 prime_end
            end_pin=Dict(  # 结束引脚定义
                component='launch_line34',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["L", '300um']
    jogs_start[1] = ["L", '900um']
    jogs_start[2] = ["R", '990um']
    # jogs_start[3] = ["R", '650um']

    readout_line_30 = RoutePathfinder(design, 'readout_line_30', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ5',
                pin='prime_end'),
            end_pin=Dict(  # 结束引脚定义
                component='launch_line14',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))
    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '300um']
    jogs_start[1] = ["R", '900um']
    jogs_start[2] = ["L", '990um']
    # jogs_start[3] = ["R", '650um']

    readout_line_31 = RoutePathfinder(design, 'readout_line_31', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ9',
                pin='prime_start'),
            end_pin=Dict(  # 结束引脚定义
                component='launch_line13',
                pin='tie')
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["L", '300um']
    jogs_start[1] = ["L", '550um']
    # jogs_start[3] = ["R", '650um']

    readout_line_40 = RoutePathfinder(design, 'readout_line_40', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='TQ15',
                pin='prime_end'),
            end_pin=Dict(  # 结束引脚定义
                component='launch_line24',
                pin='tie')  # 结束引脚名称为 tie
        ),
        lead=Dict(  # 定义引线部分
            start_straight='110um',  # 起始直线部分长度
            end_straight='100um',  # 结束直线部分长度
            start_jogged_extension=jogs_start  # 使用起始 Jog
        ),
        fillet='100um',  # 设置倒圆角半径
        trace_width='10um',  # 设置传输线的宽度
        trace_gap='5um',
        # 设置传输线中的间隙
    ))
    readout_line_41 = RoutePathfinder(design, 'readout_line_41', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='TQ19',
                pin='prime_start'),
            end_pin=Dict(
                component='launch_line23',
                pin='tie')
        ),
        lead=Dict(
            start_straight='110um',
            end_straight='100um',
            # start_jogged_extension=jogs_start
        ),
        fillet='100um',
        trace_width='10um',
        trace_gap='5um',
    ))

    # -------------------------------------------开始布线----------------------------------------------------------------
    # 最左边3根线
    line_space_y = 120
    initial_y = 100
    line_space_x = 150
    initial_x = 350
    for i in range(3):
        if i % 2 == 0:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'

        jogs_start = OrderedDict()
        jogs_start[0] = ["R", str(initial_x + i * (space / 2 + line_space_x)) + 'um']
        jogs_start[1] = ["R", '1000um']
        # jogs_start[3] = ["R", '650um']d
        RoutePathfinder(design, path_name + str(int(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(
                    component=name + str(int(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component='launch_line0' + str(2 - i),
                    pin='tie')
            ),
            lead=Dict(
                start_straight=str(initial_y + i * line_space_y) + 'um',
                end_straight='100um',
                start_jogged_extension=jogs_start
            ),
            fillet='80um',
            trace_width='10um',
            trace_gap='5um',

        ))

    # 左边第4根线
    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '800um']
    # jogs_start[1] = ["R", '1800um']
    # jogs_start[3] = ["R", '650um']
    RoutePathfinder(design, 'tunable_coupler' + str(1) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='connector_tunable_coupler' + str(1),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line111',
                pin='tie')
        ),
        lead=Dict(
            start_straight='460um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='80um',
        trace_width='10um',
        trace_gap='5um',
    ))

    # 第5根线，对齐接口和连接器的y值
    end_straight = 100
    y1 = design.components['launch_line110'].pins['tie']['middle'][1] * 1e3 + end_straight * math.cos(math.radians(45))
    y2 = design.components['connector_xmon2'].pins['c_pin_r']['middle'][1] * 1e3
    delta_y = abs(y1 - y2)

    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '800um']
    # jogs_start[1] = ["R", '1000um']
    # jogs_start[3] = ["R", '650um']d
    RoutePathfinder(design, 'xmon' + str(2) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_xmon' + str(2),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line110',
                pin='tie')
        ),
        lead=Dict(  # 定义引线部分
            start_straight=str(delta_y) + 'um',
            end_straight=str(end_straight) + 'um',
            start_jogged_extension=jogs_start
        ),
        fillet='80um',
        trace_width='10um',
        trace_gap='5um',
        # 设置传输线中的间隙
    ))
    # 第6-10根线
    for i in range(5, 10):
        if i % 2 == 0:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'

        jogs_start = OrderedDict()
        jogs_start[0] = ["R", '800um']
        # # jogs_start[1] = ["R", '1800um']
        # # jogs_start[3] = ["R", '650um']
        RoutePathfinder(design, path_name + str(int(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(  # 定义引脚输入
                start_pin=Dict(  # 起始引脚定义
                    component=name + str(int(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component='launch_line' + str(24 - i),
                    pin='tie')
            ),
            lead=Dict(  # 定义引线部分
                start_straight=str(delta_y + (i - 4) * line_space_y) + 'um',
                end_straight='100um',
                start_jogged_extension=jogs_start
            ),
            fillet='80um',
            trace_width='10um',
            trace_gap='5um',

        ))

    # 第11,12,13根线
    jogs_start = OrderedDict()
    jogs_start[0] = ["R45", '100um']
    jogs_start[1] = ["L45", '1000um']
    # jogs_start[3] = ["R", '650um']
    RoutePathfinder(design, 'xmon' + str(5) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_xmon' + str(5),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line05',
                pin='tie')
        ),
        lead=Dict(
            start_straight='1000um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='50um',
        trace_width='10um',
        trace_gap='5um',
        # 设置传输线中的间隙
    ))

    RoutePathfinder(design, 'tunable_coupler' + str(5) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_tunable_coupler' + str(5),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line06',
                pin='tie')
        ),
        lead=Dict(
            start_straight='1000um',
            end_straight='100um',
            # start_jogged_extension=jogs_start
        ),
        fillet='100um',
        trace_width='10um',
        trace_gap='5um',
    ))
    RoutePathfinder(design, 'xmon' + str(6) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='connector_xmon' + str(6),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line07',
                pin='tie')
        ),
        lead=Dict(
            start_straight='1000um',
            end_straight='100um',
            # start_jogged_extension=jogs_start
        ),
        fillet='100um',
        trace_width='10um',
        trace_gap='5um',
    ))

    # 14-20根线
    delta_y1 = 0
    delta_y2 = 350
    delta_x1 = 45
    delta_x2 = 30
    fillet = 100
    for i in range(7):
        skew_line_length = 400 - i * delta_x1
        if skew_line_length <= 2 * fillet:
            fillet = skew_line_length / 2 - 5
        if i % 2 == 1:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'
        if i < 3:
            launch_line_name = 'launch_line' + str(32 - i)
        else:
            launch_line_name = 'launch_line0' + str(14 - i)
        if i <= 4:
            jogs_start = OrderedDict()
            jogs_start[0] = ["L45", str(400 - i * delta_x1) + 'um']
            jogs_start[1] = ["R45", str(2000 + i * delta_y2) + 'um']
            jogs_start[2] = ["R", str(900 - delta_x2 * i) + 'um']
            jogs_start[3] = ["L", '100um']
        else:
            jogs_start = OrderedDict()
            jogs_start[0] = ["L45", str(400 - i * delta_x1) + 'um']
            jogs_start[1] = ["R45", str(2000) + 'um']
        RoutePathfinder(design, path_name + str(9 - int(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(  # 定义引脚输入
                start_pin=Dict(  # 起始引脚定义
                    component=name + str(9 - int(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component=launch_line_name,
                    pin='tie')
            ),
            lead=Dict(  # 定义引线部分
                start_straight=str(1100 - i * delta_y1) + 'um',
                end_straight='100um',
                start_jogged_extension=jogs_start
            ),
            fillet=str(fillet) + 'um',
            trace_width='10um',
            trace_gap='5um',

        ))

    # 第21,22,23根线
    jogs_start = OrderedDict()
    jogs_start[0] = ["L45", '100um']
    jogs_start[1] = ["R45", '1500um']
    jogs_start[2] = ["R", '800um']
    RoutePathfinder(design, 'xmon' + str(10) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_xmon' + str(10),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line12',
                pin='tie')
        ),
        lead=Dict(
            start_straight='1250um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='50um',
        trace_width='10um',
        trace_gap='5um',
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '800um']
    RoutePathfinder(design, 'tunable_coupler' + str(10) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_tunable_coupler' + str(10),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line11',
                pin='tie')
        ),
        lead=Dict(
            start_straight='3000um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='100um',
        trace_width='10um',
        trace_gap='5um',
    ))

    jogs_start = OrderedDict()
    jogs_start[0] = ["R45", '100um']
    jogs_start[1] = ["L45", '1500um']
    # jogs_start[2] = ["R", '800um']
    jogs_start = OrderedDict()
    jogs_start[0] = ["R", '800um']
    RoutePathfinder(design, 'xmon' + str(11) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='connector_xmon' + str(11),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line10',
                pin='tie')
        ),
        lead=Dict(
            start_straight='3200um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='100um',
        trace_width='10um',
        trace_gap='5um',
    ))

    # 24-30根线
    delta_y1 = 0
    delta_y2 = 350
    delta_x1 = 45
    delta_x2 = 30
    fillet = 80
    jog1 = 1000
    end_straight = 100
    for i in range(6):
        skew_line_length = 400 - i * delta_x1
        if skew_line_length <= 2 * fillet:
            fillet = skew_line_length / 2 - 5
        if i % 2 == 1:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'

        # if i == 6:
        #     jog1 = 2600
        launch_line_name = 'launch_line2' + str(5 + i)

        jogs_start = OrderedDict()
        jogs_start[0] = ["R45", str(450 - i * delta_x1) + 'um']
        jogs_start[1] = ["L45", str(jog1) + 'um']
        RoutePathfinder(design, path_name + str(14 - int(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(  # 定义引脚输入
                start_pin=Dict(  # 起始引脚定义
                    component=name + str(14 - int(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component=launch_line_name,
                    pin='tie')
            ),
            lead=Dict(
                start_straight=str(1100 - i * delta_y1) + 'um',
                end_straight=str(end_straight)+'um',
                start_jogged_extension=jogs_start
            ),
            fillet=str(fillet) + 'um',
            trace_width='10um',
            trace_gap='5um',
        ))
    jogs_start = OrderedDict()
    jogs_start[0] = ["R45", str(450 - 6 * delta_x1) + 'um']
    jogs_start[1] = ["L45", str(2000) + 'um']

    RoutePathfinder(design, 'tunable_coupler' + str(11) + '_xy_line_part2', options=Dict(
        pin_inputs=Dict(  # 定义引脚输入
            start_pin=Dict(  # 起始引脚定义
                component='connector_tunable_coupler' + str(11),
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line2' + str(11),
                pin='tie')
        ),
        lead=Dict(
            start_straight=str(1100) + 'um',
            end_straight=str(30) + 'um',
            start_jogged_extension=jogs_start,
            # end_jogged_extension=jogs_end
        ),
        fillet=str(29) + 'um',
        trace_width='10um',
        trace_gap='5um',
    ))

    # 第37,38,39（最右边）根线
    line_space_y = 120
    initial_y = 100
    line_space_x = 150
    initial_x = 350
    for i in range(3):
        if i % 2 == 0:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'

        jogs_start = OrderedDict()
        jogs_start[0] = ["R", str(initial_x + i * (space / 2 + line_space_x)) + 'um']
        jogs_start[1] = ["R", '500um']
        # jogs_start[3] = ["R", '650um']d
        RoutePathfinder(design, path_name + str(19 - math.ceil(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(
                    component=name + str(19 - math.ceil(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component='launch_line2' + str(2 - i),
                    pin='tie')
            ),
            lead=Dict(
                start_straight=str(initial_y + i * line_space_y) + 'um',
                end_straight='600um',
                start_jogged_extension=jogs_start
            ),
            fillet='50um',
            trace_width='10um',
            trace_gap='5um',
        ))

    # 32-36根线
    for i in range(5):
        if i % 2 == 1:
            name = 'connector_xmon'
            path_name = 'xmon'
        else:
            name = 'connector_tunable_coupler'
            path_name = 'tunable_coupler'

        RoutePathfinder(design, path_name + str(17 - int(i / 2)) + '_xy_line_part2', options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(
                    component=name + str(17 - int(i / 2)),
                    pin='c_pin_r'),
                end_pin=Dict(
                    component='launch_line3' + str(11 - i),
                    pin='tie')
            ),
            lead=Dict(
                start_straight='100um',
                end_straight='100um',
                # start_jogged_extension=jogs_start
            ),
            fillet='80um',
            trace_width='10um',
            trace_gap='5um',
        ))

    # 第31根线
    jogs_start = OrderedDict()
    jogs_start[0] = ["R45", '120um']
    jogs_start[1] = ["L45", '200um']
    # jogs_start[2] = ["R", '800um']
    RoutePathfinder(design, 'xmon15_xy_line_part2', options=Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='connector_xmon15',
                pin='c_pin_r'),
            end_pin=Dict(
                component='launch_line36',
                pin='tie')
        ),
        lead=Dict(
            start_straight='960um',
            end_straight='100um',
            start_jogged_extension=jogs_start
        ),
        fillet='60um',
        trace_width='10um',
        trace_gap='5um',
    ))
    if parameter_file_path is not None:
        parameter_import(design, convert_keys_to_int(load_json(parameter_file_path)))
        gui.rebuild()
        gui.autoscale()
    else:
        gui.rebuild()
        gui.autoscale()
    if jj_dict is not None:
        for i in range(int(num_qubits)):
            design.components['xmon_round' + str(i)].options.gds_cell_name = jj_dict['xmon_round' + str(i)]
            if i != int(num_qubits - 1):
                design.components['tunable_coupler' + str(i)].options.gds_cell_name = jj_dict[
                    'tunable_coupler' + str(i)]
    gui.rebuild()
    gui.autoscale()
    if airbridege is True:
        list0 = []
        list1 = []
        list2 = []
        for i in range(20):
            list0.append(design.components['meander' + str(i)])
        for i in range(1, 5):
            list1.append(design.components['readout_line_' + str(i) + '0'])
            list1.append(design.components['readout_line_' + str(i) + '1'])
        for i in range(20):
            list2.append(design.components['xmon' + str(i) + '_xy_line_part2'])
        for i in range(19):
            list2.append(design.components['tunable_coupler' + str(i) + '_xy_line_part2'])
        # list2.append(design.components['z1_part2'])
        # list2.append(design.components['z2_part2'])
        # list2.append(design.components['xy1_part2'])

        parameter_dict = Dict(pad_width='24 um', etch_residue='-3 um',
                              bridge_length='52um', pad_layer=3, etch_layer=4)
        build_airbridge(design,  list_meander=list0, parameter_dict=parameter_dict,list_controlLine=list1 + list2,control_bridgespace=0.24)

    return design, gui


def build_airbridge(design, list_meander, list_controlLine=None, parameter_dict=None, edge_space=0.15,
                    control_bridgespace=0.28):
    """"
    为版图搭建空气桥，分为两个模式，模式1为控制线模式，模式2为谐振腔模式，其中谐振腔模式包括读取线
    Default Options:
        * design: 设计版图类
        gui：设计版图图形接口
        list_meander:谐振腔名字列表
        list_controlLine:控制线名字列表
        parameter_dict:空气桥几何参数
        control_bridgespace:模式2中空气桥之间的距离
    """
    design.overwrite_enabled = True
    if parameter_dict is None:
        parameter_dict = Dict(pad_width='30 um', etch_residue='3 um',
                              bridge_length='60um', pad_layer=3, etch_layer=4)
    if list_controlLine != None:
        airbridge1 = AirbridgeGenerator(design, list_controlLine, mode=3, BRS1=edge_space, BRS2=control_bridgespace,
                                        options=parameter_dict)
    if list_meander != None:
        airbridge2 = AirbridgeGenerator(design, list_meander, mode=2, options=parameter_dict)

    # gui.rebuild()
