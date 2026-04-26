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

import qiskit_metal as metal
from qiskit_metal import designs
from qiskit_metal import MetalGUI, Dict
from qiskit_metal.qlibrary.user_components.my_qcomponent import *
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
# from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from collections import OrderedDict
from qiskit_metal.toolbox_metal.parsing import parse_value


def xmon_hfss_layout():
    design = designs.DesignPlanar()
    design.chips['main']['material'] = 'sapphire'
    design.chips.main.size['size_x'] = '4mm'
    design.chips.main.size['size_y'] = '4mm'
    design.chips['main']['size']['sample_holder_top'] = '500um'
    design.chips['main']['size']['sample_holder_bottom'] = '500um'
    design.chips['main']['size']['size_z'] = '-500um'
    design.variables.cpw_gap = '5 um'
    gui = MetalGUI(design)

    cross_width = 16
    cross_gap = 16
    TQ_pos_y = -2.4
    coupling_length_qubit = 280
    down_length_qubit = 900
    xmon_round1 = TransmonCrossRound_v1(design, 'xmon_round1',
                                        options=Dict(pos_x=str(0) + 'um', orientation='90', radius='1 um',
                                                     cross_width=str(cross_width) + 'um',
                                                     cross_gap=str(cross_gap) + 'um',
                                                     rect_width=str(cross_width) + 'um', rect_height='0um',
                                                     connection_pads=dict(
                                                         bus_02=dict(claw_length='100um', ground_spacing='3um',
                                                                     claw_width='10um', claw_gap='5um',coupling_gap='4um',
                                                                     connector_location='-90'),
                                                     )))

    TQ1 = CoupledLineTee(design,
                         'TQ1',
                         options=Dict(pos_x=str(0) + 'mm', pos_y=str(TQ_pos_y) + 'mm',
                                      orientation='180',
                                      coupling_length=str(coupling_length_qubit) + 'um',
                                      down_length=str(down_length_qubit) + 'um',
                                      coupling_space='3um',
                                      prime_width='10um',
                                      prime_gap='5um',
                                      second_width='10um',
                                      second_gap='5um',
                                      open_termination=False,
                                      mirror=False))

    jogsS = OrderedDict()
    jogsS[0] = ["L", '0um']
    spacing = 0.1
    ops = dict(fillet=spacing / 2 - 0.001)
    asymmetry = 0
    start_straight = 0.2
    total_length = 3.91
    options1 = Dict(total_length=str(total_length) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(start_pin=Dict(component='TQ1',
                                                   pin='second_end'),
                                    end_pin=Dict(component='xmon_round1', pin='bus_02')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander1 = RouteMeander(design, 'meander1', options=options1)
    gui.rebuild()

    return design, gui


def tunable_coupler_hfss_layout():
    design = designs.DesignPlanar()
    design.chips['main']['material'] = 'sapphire'
    design.chips.main.size['size_x'] = '4mm'
    design.chips.main.size['size_y'] = '4mm'
    design.chips['main']['size']['sample_holder_top'] = '500um'
    design.chips['main']['size']['sample_holder_bottom'] = '500um'
    design.chips['main']['size']['size_z'] = '-500um'
    design.variables.cpw_gap = '5 um'
    gui = MetalGUI(design)

    cross_width = 16
    cross_gap = 16
    space = 400
    rc_gap = 3
    cq_gap = 2
    l_gap = 20
    cp_gap = 5
    l_width = 15
    a_height = 30
    t_l_ratio = 7
    c_width = space - 2 * (cross_gap + cq_gap + l_gap) - cross_width
    pos_y = -(cross_width / 2 + cross_gap + cq_gap + l_gap + l_width / 2) * 1e-3
    cp_arm_length = a_height - l_width / 2 + rc_gap - rc_gap
    total_length = 3.0

    options = Dict(pos_x='0mm',
                   pos_y=str(pos_y) + 'mm',
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
                   fl_width='5um',
                   fl_gap='3um',
                   fl_length='10um',
                   fl_ground='2um',
                   jj_pad_width='8um',
                   jj_pad_height='6um',
                   jj_etch_length='4um',
                   jj_etch_pad1_width='2um',
                   jj_etch_pad2_width='5um',
                   jj_sub_rect_width='100um',
                   jj_sub_rect_height='100um',
                   t_l_ratio=str(t_l_ratio))
    tunable_coupler = MyTunableCoupler03(design, 'tunable_coupler', options=options)

    TQ_pos_y = 0.25
    T = CoupledLineTee(design,
                       'T',
                       options=Dict(pos_x=str(0) + 'mm', pos_y=str(TQ_pos_y) + 'mm',
                                    orientation='180',
                                    coupling_length='280um',
                                    down_length='600um',
                                    coupling_space='3um',
                                    prime_width='10um',
                                    prime_gap='5um',
                                    second_width='10um',
                                    second_gap='5um',
                                    open_termination=False,
                                    mirror=False))
    jogsS = OrderedDict()
    jogsS[0] = ["R", '0um']
    spacing = 0.1
    ops = dict(fillet=spacing / 2 - 0.001)
    asymmetry = 0
    start_straight = 0.2
    # total_length = total_length[1]
    options1 = Dict(total_length=str(total_length) + 'mm',
                    hfss_wire_bonds=False,
                    pin_inputs=Dict(end_pin=Dict(component='T',
                                                 pin='second_end'),
                                    start_pin=Dict(component='tunable_coupler', pin='Control')),
                    lead=Dict(start_straight=start_straight, start_jogged_extension=jogsS),
                    meander=Dict(spacing=spacing, asymmetry=asymmetry),
                    **ops)
    meander = RouteMeander(design, 'meander', options=options1)
    gui.rebuild()

    return design, gui


def readoutline_hfss_layout():
    design = metal.designs.DesignFlipChip()
    gui = metal.MetalGUI(design)

    design.chips['C_chip']['material'] = 'sapphire'
    design.chips['C_chip']['size']['size_z'] = '-500um'
    design.chips['Q_chip']['material'] = 'sapphire'
    design.chips['Q_chip']['size']['center_z'] = '8um'
    design.chips['Q_chip']['size']['size_z'] = '500um'
    design.variables['sample_holder_top'] = '510um'
    design.variables['sample_holder_bottom'] = '500um'
    design.variables.cpw_gap = '7 um'
    design.variables.cpw_width = '10 um'
    design.overwrite_enabled = True

    q0_x = 0.0
    q0_y = 0.0
    # rr_space = 0.025
    rr_edge = 0.003
    rr_space = rr_edge + 2 * parse_value(design.variables.cpw_gap, None) + parse_value(design.variables.cpw_width, None)
    pin_edge_space = 0.3
    cross_length_x_0 = 1.34

    xmon_round0 = New_Transmon_Cross(design, 'Q0', options=Dict(pos_x=q0_x, pos_y=q0_y, gap='41.76165119um',
                                                                cross_inside_width='25um', inner_corner_radius='40um',
                                                                cross_length_x=cross_length_x_0,
                                                                cross_length_y='1340um', hfss_inductance='8nH',
                                                                chip='Q_chip'))

    options = Dict(readout_coupling_width='80 um',
                   readout_coupling_height='100 um',
                   readout_cpw_width='10 um',
                   readout_cpw_gap='7 um',
                   readout_cpw_turnradius='27 um',
                   vertical_start_length='40 um',
                   vertical_end_length='300 um',
                   horizontal_start_length01='400 um',
                   horizontal_start_length02='400 um',
                   horizontal_end_length='500 um',
                   total_length='4728.81163 um',
                   arc_step='1 um',
                   meander_round='5',
                   orientation='0',
                   fillet='5 um',
                   layer='1',
                   layer_subtract='1',
                   horizontal_end_direction='1',
                   inverse=False,
                   mirror=False,
                   subtract=True,
                   chip='C_chip',
                   )
    location_x = 0.31
    r0 = MyReadoutRes02(design, 'R0', options=Dict(pos_x=design.components['Q0'].parse_options().pos_x + location_x,
                                                   pos_y=design.components['Q0'].parse_options().pos_y, **options))

    qq_space = 0.015
    cross_length_x_1 = 1.34
    q1_x = q0_x + (cross_length_x_1 + cross_length_x_0) / 2 + qq_space
    q1_y = q0_y
    readout_cpw_turnradius = 0.027
    vertical_end_length = design.components['R0'].parse_options().vertical_end_length - readout_cpw_turnradius * 2

    xmon_round1 = New_Transmon_Cross(design, 'Q1',
                                     options=Dict(pos_x=q1_x, pos_y=q1_y, gap='15um', cross_inside_width='25um',
                                                  inner_corner_radius='22um', cross_length_x=cross_length_x_1,
                                                  cross_length_y='1340um', hfss_inductance='9nH', chip='Q_chip'))

    options = Dict(readout_coupling_width='80 um',
                   readout_coupling_height='100 um',
                   readout_cpw_width='10 um',
                   readout_cpw_gap='7 um',
                   readout_cpw_turnradius=readout_cpw_turnradius,
                   vertical_start_length='40 um',
                   vertical_end_length=vertical_end_length,
                   horizontal_start_length01='400 um',
                   horizontal_start_length02='400 um',
                   horizontal_end_length='500 um',
                   total_length='3200 um',
                   arc_step='1 um',
                   meander_round='6',
                   orientation='0',
                   fillet='5 um',
                   layer='1',
                   layer_subtract='1',
                   horizontal_end_direction='1',
                   inverse=False,
                   mirror=False,
                   subtract=True,
                   chip='C_chip',
                   )
    location_x = 0.31
    r1 = MyReadoutRes02(design, 'R1', options=Dict(pos_x=design.components['Q1'].parse_options().pos_x + location_x,
                                                   pos_y=design.components['Q1'].parse_options().pos_y, **options))

    qq_space = 0.015
    cross_length_x_2 = 1.34
    q2_x = q0_x - ((cross_length_x_2 + cross_length_x_0) / 2 + qq_space)
    q2_y = q0_y

    xmon_round2 = New_Transmon_Cross(design, 'Q2',
                                     options=Dict(pos_x=q2_x, pos_y=q2_y, gap='15um', cross_inside_width='25um',
                                                  inner_corner_radius='22um', cross_length_x=cross_length_x_2,
                                                  cross_length_y='1340um', chip='Q_chip'))

    options = Dict(readout_coupling_width='80 um',
                   readout_coupling_height='100 um',
                   readout_cpw_width='10 um',
                   readout_cpw_gap='7 um',
                   readout_cpw_turnradius='27 um',
                   vertical_start_length='40 um',
                   vertical_end_length='300 um',
                   horizontal_start_length01='400 um',
                   horizontal_start_length02='400 um',
                   horizontal_end_length='500 um',
                   total_length='3200 um',
                   arc_step='1 um',
                   meander_round='5',
                   orientation='0',
                   fillet='5 um',
                   layer='1',
                   layer_subtract='1',
                   horizontal_end_direction='1',
                   inverse=False,
                   mirror=False,
                   subtract=True,
                   chip='C_chip',
                   )
    location_x = 0.31
    r2 = MyReadoutRes02(design, 'R2', options=Dict(pos_x=design.components['Q2'].parse_options().pos_x + location_x,
                                                   pos_y=design.components['Q2'].parse_options().pos_y, **options))

    qq_space = 0.015
    cross_length_x_3 = 1.34
    q3_x = q0_x
    q3_y = q0_y - ((cross_length_x_3 + cross_length_x_0) / 2 + qq_space)

    xmon_round3 = New_Transmon_Cross(design, 'Q3',
                                     options=Dict(pos_x=q3_x, pos_y=q3_y, gap='15um', cross_inside_width='25um',
                                                  inner_corner_radius='22um', cross_length_x=cross_length_x_3,
                                                  cross_length_y='1340um', chip='Q_chip'))

    options = Dict(readout_coupling_width='80 um',
                   readout_coupling_height='100 um',
                   readout_cpw_width='10 um',
                   readout_cpw_gap='7 um',
                   readout_cpw_turnradius='27 um',
                   vertical_start_length='40 um',
                   vertical_end_length='300 um',
                   horizontal_start_length01='400 um',
                   horizontal_start_length02='400 um',
                   horizontal_end_length='500 um',
                   total_length='3200 um',
                   arc_step='1 um',
                   meander_round='3',
                   orientation='0',
                   fillet='5 um',
                   layer='1',
                   layer_subtract='1',
                   horizontal_end_direction='1',
                   inverse=True,
                   mirror=False,
                   subtract=True,
                   chip='C_chip',
                   )
    location_x = 0.31
    r3 = MyReadoutRes02(design, 'R3', options=Dict(pos_x=design.components['Q3'].parse_options().pos_x - location_x,
                                                   pos_y=design.components['Q3'].parse_options().pos_y, **options))

    r_0 = design.components['R3'].parse_options().readout_coupling_height / 2
    r = design.components['R3'].parse_options().readout_cpw_turnradius
    l_2 = design.components['R3'].parse_options().vertical_start_length
    l_6 = design.components['R3'].parse_options().vertical_end_length
    turn_round_n = design.components['R3'].parse_options().meander_round

    l_v = design.components['R0'].pins.readout.middle[1] - 2 * rr_space - design.components[
        'R3'].parse_options().pos_y - r_0 - l_2 - 2 * r * (turn_round_n + 2.5)
    design.components['R3'].options.vertical_end_length = l_v

    # otg_pos_x =  design.components['R0'].pins.readout.middle[0]-0.01
    # otg_pos_y =  design.components['R0'].pins.readout.middle[1]
    # otg_res = OpenToGround(design, 'open_pin', options=Dict(pos_x=otg_pos_x,  pos_y=otg_pos_y, width='10um',gap='7um', orientation='180',chip = 'C_chip'))
    #
    # pin_opt = Dict( pin_inputs=Dict(start_pin=Dict(component='R0',pin='readout'),
    #                          end_pin=Dict(component='open_pin',pin='open'),),chip = 'C_chip')
    # open_line = RoutePathfinder(design,'open_line',options=pin_opt)

    pos_start_x = design.components['Q2'].parse_options().pos_x - design.components[
        'Q2'].parse_options().cross_length_x / 2 - pin_edge_space
    pos_start_x1 = design.components['Q2'].parse_options().pos_x + design.components[
        'Q2'].parse_options().cross_length_x / 2 + qq_space / 2 - 0.1
    pos_start_y = design.components['R0'].pins.readout.middle[1] - rr_space

    # otg2 = OpenToGround(design, 'open_readout_line2', options=Dict(pos_x=pos_start_x,  pos_y=pos_start_y, width='10um',gap='7um', orientation='180',chip = 'C_chip'))
    otg2r = OpenToGround(design, 'open_readout_line2_r',
                         options=Dict(pos_x=pos_start_x1, pos_y=pos_start_y, width='10um', gap='7um', orientation='0',
                                      chip='C_chip'))
    otg0 = OpenToGround(design, 'open_readout_line0',
                        options=Dict(pos_x=pos_start_x1, pos_y=pos_start_y, width='10um', gap='7um', orientation='180',
                                     chip='C_chip'))
    otg0r = OpenToGround(design, 'open_readout_line0_r',
                         options=Dict(pos_x=-pos_start_x1, pos_y=pos_start_y, width='10um', gap='7um', orientation='0',
                                      chip='C_chip'))
    otg1 = OpenToGround(design, 'open_readout_line1',
                        options=Dict(pos_x=-pos_start_x1, pos_y=pos_start_y, width='10um', gap='7um', orientation='180',
                                     chip='C_chip'))
    otg1r = OpenToGround(design, 'open_readout_line1_r',
                         options=Dict(pos_x=-pos_start_x, pos_y=pos_start_y, width='10um', gap='7um', orientation='0',
                                      chip='C_chip'))

    pos_launchpad_x = 19.393
    pos_launchpad_y = pos_start_y
    opt1 = Dict(pos_x=str(-pos_launchpad_x) + 'mm', pos_y=str(pos_start_y) + 'mm', pad_width='250 um',
                pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='0', chip='C_chip')
    launchpad1 = LaunchpadWirebond(design, 'launchpad1', options=opt1)

    opt2 = Dict(pos_x=str(pos_launchpad_x) + 'mm', pos_y=str(pos_start_y) + 'mm', pad_width='250 um',
                pad_height='250 um', lead_length='176 um', pad_gap='100 um', orientation='180', chip='C_chip')
    launchpad2 = LaunchpadWirebond(design, 'launchpad2', options=opt2)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='launchpad1', pin='tie'),
                                   end_pin=Dict(component='open_readout_line2_r', pin='open'), ),
                   lead=Dict(start_straight='100um',
                             end_straight='100um', ), chip='C_chip')
    readout_line2 = RoutePathfinder(design, 'readout_line2', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='open_readout_line0', pin='open'),
                                   end_pin=Dict(component='open_readout_line0_r', pin='open'), ),
                   lead=Dict(start_straight='100um',
                             end_straight='100um', ), chip='C_chip')
    readout_line0 = RoutePathfinder(design, 'readout_line0', options=pin_opt)

    pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='open_readout_line1', pin='open'),
                                   end_pin=Dict(component='launchpad2', pin='tie'), ), lead=Dict(start_straight='100um',
                                                                                                 end_straight='100um', ),
                   chip='C_chip')
    readout_line1 = RoutePathfinder(design, 'readout_line1', options=pin_opt)
    gui.rebuild()
    return design, gui

