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
from .base import QuantumChip
from qiskit_metal import draw, Dict, designs, MetalGUI
from qiskit_metal.qlibrary.user_components.my_qcomponent import *
from qiskit_metal.qlibrary.user_components.airbridge import AirbridgeGenerator
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder
from collections import OrderedDict
from qiskit_metal.qlibrary.user_components.save_load import *
from qiskit_metal.qlibrary.user_components.reader import *
import re
import numpy as np


class SingleQubitChip(QuantumChip):
    def __init__(self, design, gui, jj_dict: dict, parameter_file_path=None, version='1.00'):
        super().__init__(design, parameter_file_path)
        self.jj_dict = jj_dict
        self.version = version
        self.name = "Q1"

    def build(self, style='standard', **kwargs):
        """
        统一的对外接口。
        :param style: 决定画哪种版图 ('standard' 或 'small')
        :param kwargs: 传递给具体版图函数的额外参数
        """
        if style == 'standard':
            self._build_standard(self, **kwargs)
        elif style == 'small':
            self._build_small(self, **kwargs)
        elif style == 'large':
            self._build_large(self, **kwargs)
        else:
            raise ValueError(f"Unknown layout style: {style}")

    # --- 具体的版图实现 (作为类的成员函数) ---

    def _build_standard(self, x, y):
        """对应原来的 single_qubit_layout"""
        print(f"[{self.name}] Drawing STANDARD layout at ({x}, {y})...")

        pass

    def _build_small(self):
        """"
        含有5个比特和9个谐振腔的单比特版图，其中4个谐振腔为测试用途
        Default Options:
            * jj_dict: {'Q1':'FakeJunction_01','Q2':'FakeJunction_01'}- 每个比特的约瑟夫森结组成的字典
        """
        if self.jj_dict is None:
            jj_dict = {'Q1': 'FakeJunction_01', 'Q2': 'FakeJunction_02', 'Q3': 'FakeJunction_03',
                       'Q4': 'FakeJunction_04',
                       'Q5': 'FakeJunction_05', }

        self.design.chips['main']['material'] = 'sapphire'
        self.design.chips.main.size['size_x'] = '6mm'
        self.design.chips.main.size['size_y'] = '6mm'
        self.design.chips['main']['size']['sample_holder_top'] = '500um'
        self.design.chips['main']['size']['sample_holder_bottom'] = '500um'
        self.design.chips['main']['size']['size_z'] = '-500um'
        self.design.variables.cpw_gap = '5um'

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
        LaunchpadWirebond(self.design, launch_pad_name + str(1), options=opt1)

        opt2 = Dict(pos_x=str(pos_x) + 'mm', pos_y=0, orientation='180', pad_width=str(pad_width) + 'mm',
                    pad_height=str(pad_height) + 'mm', pad_gap=str(pad_gap) + 'mm',
                    taper_height=str(taper_height) + 'mm', lead_length=str(lead_length) + 'mm', )
        LaunchpadWirebond(self.design, launch_pad_name + str(2), options=opt2)

        if version != '0.00':
            options = {
                'number': number,
                'decimal1': decimal1,
                'decimal2': decimal2,
                'width': '20um',  # 笔画宽度
                'height': '100um',  # 数字高度
                'pos_x': str(0.95 * pos_x) + 'mm',
                'pos_y': str(-1.19 * pos_x) + 'mm',
                'spacing': '30um',
            }
            NumberComponent(self.design, name='number1', options=options)

        # draw transmon qubit
        ql_distance = 1.65
        qq_space = 0.75
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

        transmon = TransmonPocketRoundTeeth(self.design, 'Q1', options=transmon_options)

        self.design.copy_qcomponent(transmon, 'Q2', Dict(pos_x=-2 * qq_space, pos_y=-ql_distance))
        self.design.copy_qcomponent(transmon, 'Q3', Dict(pos_x=2 * qq_space, pos_y=-ql_distance))
        self.design.copy_qcomponent(transmon, 'Q4', Dict(pos_x=-qq_space, pos_y=ql_distance))
        self.design.copy_qcomponent(transmon, 'Q5', Dict(pos_x=qq_space, pos_y=ql_distance))
        self.design.components['Q4'].options.orientation = '180'
        self.design.components['Q5'].options.orientation = '180'
        self.design.components['Q2'].options.gds_cell_name = jj_dict['Q2']
        self.design.components['Q3'].options.gds_cell_name = jj_dict['Q3']
        self.design.components['Q4'].options.gds_cell_name = jj_dict['Q4']
        self.design.components['Q5'].options.gds_cell_name = jj_dict['Q5']

        # draw read line and coupledLineTee
        shift = 0.054
        rr_space1 = 0.317
        shift1 = 0.6
        # rr_space2 = 0.574

        TQ1 = CoupledLineTee(self.design,
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
        TQ2 = CoupledLineTee(self.design,
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
        TQ3 = CoupledLineTee(self.design,
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
        TQ4 = CoupledLineTee(self.design,
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
        TQ5 = CoupledLineTee(self.design,
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

        ops_oL = Dict(hfss_wire_bonds=False,
                      pin_inputs=Dict(start_pin=Dict(component='launch_zline1',
                                                     pin='tie'),
                                      end_pin=Dict(component='TQ2', pin='prime_start')), trace_width='10um',
                      trace_gap='5um')
        cpw_openLeft = RouteStraight(self.design, 'cpw_openLeft', options=ops_oL)

        ops_3 = Dict(hfss_wire_bonds=False,
                     pin_inputs=Dict(start_pin=Dict(component='TQ2', pin='prime_end'),
                                     end_pin=Dict(component='TQ4', pin='prime_end')), trace_width='10um',
                     trace_gap='5um')
        cpw_3 = RouteStraight(self.design, 'cpw_3', options=ops_3)

        ops_4 = Dict(hfss_wire_bonds=False,
                     pin_inputs=Dict(start_pin=Dict(component='TQ4', pin='prime_start'),
                                     end_pin=Dict(component='TQ1', pin='prime_start')), trace_width='10um',
                     trace_gap='5um')
        cpw_4 = RouteStraight(self.design, 'cpw_4', options=ops_4)

        ops_5 = Dict(hfss_wire_bonds=False,
                     pin_inputs=Dict(start_pin=Dict(component='TQ1', pin='prime_end'),
                                     end_pin=Dict(component='TQ5', pin='prime_end')), trace_width='10um',
                     trace_gap='5um')
        cpw_5 = RouteStraight(self.design, 'cpw_5', options=ops_5)

        ops_6 = Dict(hfss_wire_bonds=False,
                     pin_inputs=Dict(start_pin=Dict(component='TQ5', pin='prime_start'),
                                     end_pin=Dict(component='TQ3', pin='prime_start')), trace_width='10um',
                     trace_gap='5um')
        cpw_6 = RouteStraight(self.design, 'cpw_6', options=ops_6)

        ops_oR = Dict(hfss_wire_bonds=False,
                      pin_inputs=Dict(start_pin=Dict(component='launch_zline2', pin='tie'),
                                      end_pin=Dict(component='TQ3', pin='prime_end')), trace_width='10um',
                      trace_gap='5um')
        cpw_openRight = RouteStraight(self.design, 'cpw_openRight', options=ops_oR)

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
        meanderQ1 = RouteMeander(self.design, 'meanderQ1', options=options1)

        options2 = Dict(total_length='4.2699mm',
                        hfss_wire_bonds=False,
                        pin_inputs=Dict(end_pin=Dict(component='TQ2',
                                                     pin='second_end'),
                                        start_pin=Dict(component='Q2', pin='readout')),
                        lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                        meander=Dict(spacing=spacing, asymmetry=asymmetry),
                        **ops)
        meanderQ2 = RouteMeander(self.design, 'meanderQ2', options=options2)

        options3 = Dict(total_length='4.1996mm',
                        hfss_wire_bonds=False,
                        pin_inputs=Dict(end_pin=Dict(component='TQ3',
                                                     pin='second_end'),
                                        start_pin=Dict(component='Q3', pin='readout')),
                        lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                        meander=Dict(spacing=spacing, asymmetry=asymmetry),
                        **ops)
        meanderQ3 = RouteMeander(self.design, 'meanderQ3', options=options3)

        options4 = Dict(total_length='4.0657mm',
                        hfss_wire_bonds=False,
                        pin_inputs=Dict(end_pin=Dict(component='TQ4',
                                                     pin='second_end'),
                                        start_pin=Dict(component='Q4', pin='readout')),
                        lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                        meander=Dict(spacing=spacing, asymmetry=asymmetry),
                        **ops)
        meanderQ4 = RouteMeander(self.design, 'meanderQ4', options=options4)

        options5 = Dict(total_length='4.1316mm',
                        hfss_wire_bonds=False,
                        pin_inputs=Dict(end_pin=Dict(component='TQ5',
                                                     pin='second_end'),
                                        start_pin=Dict(component='Q5', pin='readout')),
                        lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                        meander=Dict(spacing=spacing, asymmetry=asymmetry),
                        **ops)
        meanderQ5 = RouteMeander(self.design, 'meanderQ5', options=options5)

        if self.parameter_file_path is not None:
            parameter_import(self.design, convert_keys_to_int(load_json(self.parameter_file_path)))
        self.gui.rebuild()
        self.gui.autoscale()

    # def _build_small(self, x, y, gap_size='10um'):
    #     """对应原来的 small_single_qubit_layout"""
    #     print(f"[{self.name}] Drawing SMALL layout at ({x}, {y}) with gap {gap_size}...")
    #
    #     # 你的小型版代码放这里
    #     # q = TransmonSmall(self.design, self.name, options=self.jj_dict)
    #     # ...
    #     pass
    # pass

    def _build_standard(self, x, y):
        """对应原来的 single_qubit_layout"""
        print(f"[{self.name}] Drawing STANDARD layout at ({x}, {y})...")

        pass

    def run_simulation(self):
        """
        单比特特定的仿真流程。
        调用父类的 simulate_q3d，但自动填入单比特特定的参数。
        """
        print("Running Single Qubit Specific Simulation...")

        # 自动指定只渲染这个比特
        comps_to_render = [self.q_comp_name]

        # 调用父类的通用仿真方法
        super().simulate_q3d(
            setup_name="SingleQubit_Sim",
            max_passes=15,  # 可以覆盖父类默认值
            percent_error=0.02,
            render_qcomps=comps_to_render
        )