from qiskit_metal import designs, MetalGUI
from qiskit_metal.qlibrary.user_components.my_qcomponent import *
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.terminations.short_to_ground import ShortToGround
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder
from qiskit_metal.toolbox_metal.parsing import parse_value
from shapely.geometry import mapping, Point as ShapelyPoint, box as ShapelyBox
from collections import OrderedDict
from qiskit_metal.qlibrary.sample_shapes.rectangle import Rectangle
from qiskit_metal.qlibrary.user_components.save_load import *
from qiskit_metal.qlibrary.user_components.reader import *
import numpy as np
import math
import os
import re
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon


# def qubit_flipchip_layout(chip_size, pad_num=42, rotation_angle=45, qq_space=2.5, row=6, column=10, shift_x=0,
#                           shift_y=0, jj_dict=None,parameter_file_path=None):
#     # Initialise design
#     design = designs.DesignPlanar()
#     # Specify design name
#     design.metadata['design_name'] = 'FlipChip_Device'
#     # launch GUI
#     gui = MetalGUI(design)
#     # Allow running the same cell here multiple times to overwrite changes
#     design.overwrite_enabled = True
#
#     design.chips['main']['material'] = 'sapphire'
#     design.chips['main']['size']['size_x'] = str(chip_size) + 'mm'
#     design.chips['main']['size']['size_y'] = str(chip_size) + 'mm'
#     design.variables.cpw_gap = '3.4 um'
#     design.variables.cpw_width = '5 um'
#     # design.chips,design.variables
#     my_chip = MyCircle(design, 'my_chip', options=Dict(radius=str(chip_size + 2) + 'mm'))
#
#     # design the layout of launchpad
#     points = []
#     N = pad_num
#     size = chip_size - 2
#     pad_pad_space = 0.7
#     edge_gap = (size - (pad_pad_space * (N - 1))) / 2
#     for i in range(N):
#         shape = draw.Point(-size / 2 + edge_gap + i * pad_pad_space, size / 2)
#         points.append(shape)
#     # points.append()
#     # for i in range(N):
#     #     shape = draw.Point(size/2,size/2-i*size/N)
#     x = draw.shapely.geometrycollections(points)
#     x0 = draw.rotate(x, 90, origin=(0, 0))
#     x1 = draw.rotate(x0, 90, origin=(0, 0))
#     x2 = draw.rotate(x1, 90, origin=(0, 0))
#     square = draw.shapely.geometrycollections([x, x0, x1, x2])
#     square = draw.rotate(square, rotation_angle, origin=(0, 0))
#     square_coords = []
#     for i in range(4):
#         for j in range(N):
#             square_coords.append(square.geoms[i].geoms[j].coords[0])
#
#     opt = Dict(pos_x=0, pos_y=0, orientation=str(-90 + rotation_angle), pad_width='245 um', pad_height='245 um',
#                pad_gap='100 um',
#                lead_length='50 um', chip='main')
#     opt_a = Dict(pos_x=0, pos_y=0, orientation=str(rotation_angle), pad_width='245 um', pad_height='245 um',
#                  pad_gap='100 um',
#                  lead_length='50 um', chip='main')
#     opt_b = Dict(pos_x=0, pos_y=0, orientation=str(rotation_angle + 90), pad_width='245 um', pad_height='245 um',
#                  pad_gap='100 um',
#                  lead_length='50 um', chip='main')
#     opt_c = Dict(pos_x=0, pos_y=0, orientation=str(rotation_angle + 180), pad_width='245 um', pad_height='245 um',
#                  pad_gap='100 um',
#                  lead_length='50 um', chip='main')
#     # test = OpenToGround(design, 'open01', options=Dict(pos_x='-3 mm',  pos_y=pos_y_zline+0.02, orientation='-45', chip ='C_chip'),)
#     launch_zline = LaunchpadWirebond(design, 'launch_zline', options=opt)
#     launch_zline_a = LaunchpadWirebond(design, 'launch_zline_a', options=opt_a)
#     launch_zline_b = LaunchpadWirebond(design, 'launch_zline_b', options=opt_b)
#     launch_zline_c = LaunchpadWirebond(design, 'launch_zline_c', options=opt_c)
#
#     q0_x = 0
#     q0_y = 0
#     cross_length = 200
#     cross_width = 24
#     cross_gap = 30
#     jj_pos_x = -0.5
#     angle = 45
#
#     options = Dict(
#         pos_x=str(q0_x) + 'mm',
#         pos_y=str(q0_y) + 'mm',  # 使用定义的qubit_y
#         orientation=str(angle),
#         layer="2",
#         cross_width=str(cross_width) + 'um',
#         cross_length=str(cross_length) + 'um',
#         cross_length1=str(cross_length) + 'um',
#         cross_gap=str(cross_gap) + 'um',
#         radius='2um',
#         rect_width='0um',
#         rect_height='32um',
#         jj_pos_x=str(jj_pos_x),
#         jj_pad_width='8um',
#         jj_pad_height='6um',
#         jj_etch_length='4um',
#         jj_etch_pad1_width='2um',
#         jj_etch_pad2_width='5um',
#         jj_pad2_height='8um',
#         chip='main',
#     )
#     q0 = XmonFlipChip01(design, 'qubit0', options=options)
#
#     design.delete_all_components()
#     launch_list = []
#     for i in range(4):
#         for j in range(N):
#             if (i == 0):
#                 launch_list.append(design.copy_qcomponent(launch_zline, 'launch_zline' + str(i) + str(j),
#                                                           Dict(pos_x=square_coords[i * N + j][0],
#                                                                pos_y=square_coords[i * N + j][1])))
#             elif (i == 1):
#                 launch_list.append(design.copy_qcomponent(launch_zline_a, 'launch_zline' + str(i) + str(j),
#                                                           Dict(pos_x=square_coords[i * N + j][0],
#                                                                pos_y=square_coords[i * N + j][1])))
#             elif (i == 2):
#                 launch_list.append(design.copy_qcomponent(launch_zline_b, 'launch_zline' + str(i) + str(j),
#                                                           Dict(pos_x=square_coords[i * N + j][0],
#                                                                pos_y=square_coords[i * N + j][1])))
#             else:
#                 launch_list.append(design.copy_qcomponent(launch_zline_c, 'launch_zline' + str(i) + str(j),
#                                                           Dict(pos_x=square_coords[i * N + j][0],
#                                                                pos_y=square_coords[i * N + j][1])))
#
#     # design the 56 qubits layout
#     d = qq_space * math.sqrt(2) / 2
#     Nx = column
#     Ny = row
#     shift_x = shift_x * 1e-3
#     shift_y = shift_y * 1e-3
#     q0_x = -((Nx - 1) / 2) * d * 2 + shift_x
#     q0_y = Ny / 2 * d + shift_y
#     total_qubit_num = Nx * Ny
#     qubit_pos_list = []
#     q0_x_list = []
#
#     for i in range(Ny):
#         q0_x_list.append(q0_x)
#         q0_x = q0_x - (-1) ** int(i / 2) * d
#
#     for i in range(Ny):
#         for j in range(Nx):
#             q_x = q0_x_list[i] + j * 2 * d
#             q_y = q0_y - i * d
#             qubit_pos_list.append((q_x, q_y))
#
#     for i in range(int(total_qubit_num)):
#         design.copy_qcomponent(q0, 'Q' + str(i + 1),
#                                Dict(pos_x=str(qubit_pos_list[i][0]) + 'mm', pos_y=str(qubit_pos_list[i][1]) + 'mm'))
#
#     # draw flux line
#     control_line_cpw_width0 = '5 um'
#     control_line_cpw_gap0 = '3.4 um'
#     control_line_cpw_width = '5 um'
#     control_line_cpw_gap = '3.4 um'
#     opt = Dict(inverse=True, mirror=True, end_horizontal_length='20 um', flux_cpw_width0=control_line_cpw_width0,
#                flux_cpw_gap0=control_line_cpw_gap0, flux_cpw_width=control_line_cpw_width, flux_cpw_gap=control_line_cpw_gap,
#                angle='-60', angle_end='-30', end_yposition='80um')
#     for i in range(1, int(total_qubit_num) + 1):
#         flux_pos_x = design.components['Q' + str(i)].parse_options().pos_x + jj_pos_x * cross_length * math.cos(
#             math.radians(angle)) * 1e-3 \
#                      - (design.components['Q' + str(i)].parse_options().jj_pad_width + design.components[
#             'Q' + str(i)].parse_options().cross_width / 2.0
#                         + design.components['Q' + str(i)].parse_options().cross_gap / 2.0) * math.sin(
#             math.radians(angle))
#         flux_pos_y = design.components['Q' + str(i)].parse_options().pos_y + jj_pos_x * cross_length * math.sin(
#             math.radians(angle)) * 1e-3 \
#                      + (design.components['Q' + str(i)].parse_options().jj_pad_width + design.components[
#             'Q' + str(i)].parse_options().cross_width / 2.0
#                         + design.components['Q' + str(i)].parse_options().cross_gap / 2.0) * math.cos(
#             math.radians(angle))
#         MyFluxLine02(design, 'flux_line' + str(i), options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, **opt))
#
#     # #indium stop sign
#     # pos_x1 = design.components['Q' + str(1)].parse_options().pos_x + 1
#     # pos_y1 = design.components['Q' + str(1)].parse_options().pos_y + 2
#     # pos_x2 = design.components['Q' + str(Nx*Ny)].parse_options().pos_x - 1
#     # pos_y2 = design.components['Q' + str(Nx*Ny)].parse_options().pos_y - 2
#     # stop_sign_width = 1400
#     # stop_sign_height = 900
#     # # pos_x3 = design.components['Q' + str(Nx*(Ny-1)+1)].parse_options().pos_x + 0.3
#     # # pos_y3 = design.components['Q' + str(Nx*(Ny-1)+1)].parse_options().pos_y - 2
#     # # pos_x4 = design.components['Q' + str(Nx*Ny)].parse_options().pos_x - 0.3
#     # # pos_y4 = design.components['Q' + str(Nx*Ny)].parse_options().pos_y - 2
#     # options = Dict(pos_x=pos_x1,pos_y=pos_y1,width=str(stop_sign_width)+'um',
#     #                height=str(stop_sign_height)+'um',
#     #                subtract='False',
#     #                helper='False')
#     # Rectangle(design, 'rectangle1', options=options)
#     #
#     # options = Dict(pos_x=pos_x2,pos_y=pos_y1,width=str(stop_sign_width)+'um',
#     #                height=str(stop_sign_height)+'um',
#     #                subtract='False',
#     #                helper='False')
#     # Rectangle(design, 'rectangle2', options=options)
#     #
#     # options = Dict(pos_x=pos_x1,pos_y=pos_y2,width=str(stop_sign_width)+'um',
#     #                height=str(stop_sign_height)+'um',
#     #                subtract='False',
#     #                helper='False')
#     # Rectangle(design, 'rectangle3', options=options)
#     #
#     # options = Dict(pos_x=pos_x2,pos_y=pos_y2,width=str(stop_sign_width)+'um',
#     #                height=str(stop_sign_height)+'um',
#     #                subtract='False',
#     #                helper='False')
#     # Rectangle(design, 'rectangle4', options=options)
#
#     # transmission line layout
#     tc_x_offset = 0.4
#     tc_y_offset = 0.1
#     for i in range(Ny):
#         pos_x = design.components['Q' + str(1 + i * Nx)].parse_options().pos_x - tc_x_offset
#         pos_y = design.components['Q' + str(1 + i * Nx)].parse_options().pos_y + d / 2 - tc_y_offset
#         ShortToGround(design, 'tl_l' + str(i + 1), options=Dict(pos_x=pos_x, pos_y=pos_y, orientation='180'))
#         ShortToGround(design, 'readout_line_' + str(i + 1) + '_left',
#                       options=Dict(pos_x=pos_x, pos_y=pos_y, orientation='0'))
#         pos_x = design.components['Q' + str((i + 1) * Nx)].parse_options().pos_x + tc_x_offset
#         ShortToGround(design, 'tl_r' + str(i + 1), options=Dict(pos_x=pos_x, pos_y=pos_y, orientation='0'))
#         ShortToGround(design, 'readout_line_' + str(i + 1) + '_right',
#                       options=Dict(pos_x=pos_x, pos_y=pos_y, orientation='180'))
#
#         pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='tl_l' + str(i + 1), pin='short'),
#                                        end_pin=Dict(component='tl_r' + str(i + 1), pin='short'), ), chip='main')
#         RouteStraight(design, 'readout_line_' + str(i + 1), options=pin_opt)
#
#     # draw tunable coupler
#     p1_width = 20
#     pp_space = 15
#     cross_length = 200
#     cross_width = 24
#     cross_gap = 30
#     coupling_length = 70
#     coupling_width = 50
#     finger_p_width = 50
#     finger_pc_space = 3
#     finger_c_width = 50
#     jj_pad_height = 35
#     c_width = 15
#     c_gap = 130
#     c_gap1 = 40
#     qc_space = (coupling_width - p1_width - cross_width) / 2
#     p1_length = p2_length = qq_space / 2 * 1e3 - cross_length - pp_space / 2 - p1_width - qc_space
#     flux_line_vector_length = p1_width / 2
#     options = Dict(p1_length=str(p1_length) + 'um',
#                    p1_width=str(p1_width) + 'um',
#                    p2_length=str(p2_length) + 'um',
#                    p2_width=str(p1_width) + 'um',
#                    coupling_width=str(coupling_width) + 'um',
#                    coupling_length=str(coupling_length) + 'um',
#                    finger_p_length='5um',
#                    finger_p_width=str(finger_p_width) + 'um',
#                    finger_pp_length='100um',
#                    finger_pp_width='5um',
#                    finger_c_length='5um',
#                    finger_c_width=str(finger_c_width) + 'um',
#                    finger_pc_space=str(finger_pc_space) + 'um',
#                    finger_pp_space='3um',
#                    finger_n='6',
#                    finger_pp_n='3',
#                    c_width=str(c_width) + 'um',
#                    c_gap=str(c_gap) + 'um',
#                    c_gap1=str(c_gap1) + 'um',
#                    pp_space=str(pp_space) + 'um',
#                    jj_pad_width='10um',
#                    jj_pad_height=str(jj_pad_height) + 'um',
#                    jj_etch_length='4um',
#                    jj_etch_pad1_width='2um',
#                    jj_etch_pad2_width='5um',
#                    # jj_sub_rect_width='100um',
#                    # jj_sub_rect_height='100um',
#                    fl_length='0um',
#                    fl_gap='2um',
#                    fl_ground='3um',
#                    fl_width='10um',
#                    fillet='1um',
#                    layer='2'
#                    )
#     opt = Dict(inverse=True, mirror=True, end_horizontal_length='20 um', flux_cpw_width0=control_line_cpw_width0,
#                flux_cpw_gap0=control_line_cpw_gap0,
#                flux_cpw_width=control_line_cpw_width, flux_cpw_gap=control_line_cpw_gap, angle='-60', angle_end='-30',
#                end_yposition='80um')
#     cycle_num = 2
#     L1 = (finger_p_width + finger_pc_space + c_width + jj_pad_height) * 1e-3
#     L = p1_width * 1e-3 / 2 + L1
#     L_res = c_gap * 1e-3 - L1
#     Lc = L + L_res / 2
#     angle = 45
#     opt = Dict(inverse=True, end_horizontal_length='10 um', flux_cpw_width0=control_line_cpw_width0,
#                flux_cpw_gap0=control_line_cpw_gap0,
#                flux_cpw_width=control_line_cpw_width, flux_cpw_gap=control_line_cpw_gap, c_length='0 um', angle='-60',
#                angle_end='-30', end_yposition='60 um', fillet='8 um')
#     opt1 = Dict(inverse=True, end_horizontal_length='10 um', flux_cpw_width0=control_line_cpw_width0,
#                 flux_cpw_gap0=control_line_cpw_gap0,
#                 flux_cpw_width=control_line_cpw_width, flux_cpw_gap=control_line_cpw_gap, c_length='0 um', angle='60',
#                 angle_end='30', end_yposition='60 um', fillet='8 um')
#     for i in range(1, int(total_qubit_num - (Nx - 1))):
#         criterion = int((int((i - 1) / Nx)) / cycle_num) % 2  # 周期性左右臂交错
#         if criterion == 0:
#             pos_x = (design.components['Q' + str(i)].parse_options().pos_x + design.components[
#                 'Q' + str(i + Nx)].parse_options().pos_x) / 2
#             pos_y = (design.components['Q' + str(i)].parse_options().pos_y + design.components[
#                 'Q' + str(i + Nx)].parse_options().pos_y) / 2
#             LongRangeTunableCoupler01(design, 'long_range_tc_' + str(i) + '_' + str(i + Nx),
#                                       options=Dict(pos_x=pos_x, pos_y=pos_y, orientation=str(angle), **options))
#             flux_pos_x = pos_x - Lc * math.sin(math.radians(angle))
#             flux_pos_y = pos_y + Lc * math.cos(math.radians(angle))
#             if i % Nx <= round(Nx / 2) and i % Nx != 0:
#                 MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx),
#                              options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=True, **opt))
#             else:
#                 MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx),
#                              options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=True, **opt1))
#             # 右臂可调耦合器
#             if i % Nx != 0:
#                 pos_x = (design.components['Q' + str(i)].parse_options().pos_x + design.components[
#                     'Q' + str(i + Nx + 1)].parse_options().pos_x) / 2
#                 pos_y = (design.components['Q' + str(i)].parse_options().pos_y + design.components[
#                     'Q' + str(i + Nx + 1)].parse_options().pos_y) / 2
#                 LongRangeTunableCoupler01(design, 'long_range_tc_' + str(i) + '_' + str(i + Nx + 1),
#                                           options=Dict(pos_x=pos_x, pos_y=pos_y, orientation=str(-angle), **options))
#                 flux_pos_x = pos_x - Lc * math.sin(math.radians(-angle))
#                 flux_pos_y = pos_y + Lc * math.cos(math.radians(-angle))
#                 if i % Nx < round(Nx / 2):
#                     MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx + 1),
#                                  options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=False, **opt1))
#                 else:
#                     MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx + 1),
#                                  options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=False, **opt))
#         else:
#             pos_x = (design.components['Q' + str(i)].parse_options().pos_x + design.components[
#                 'Q' + str(i + Nx)].parse_options().pos_x) / 2
#             pos_y = (design.components['Q' + str(i)].parse_options().pos_y + design.components[
#                 'Q' + str(i + Nx)].parse_options().pos_y) / 2
#             LongRangeTunableCoupler01(design, 'long_range_tc_' + str(i) + '_' + str(i + Nx),
#                                       options=Dict(pos_x=pos_x, pos_y=pos_y, orientation=str(-angle), **options))
#             flux_pos_x = pos_x - Lc * math.sin(math.radians(-angle))
#             flux_pos_y = pos_y + Lc * math.cos(math.radians(-angle))
#             if (i - 1) % Nx < int(Nx / 2):
#                 MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx),
#                              options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=False, **opt1))
#             else:
#                 MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx),
#                              options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=False, **opt))
#             if (i - 1) % Nx != 0:
#                 pos_x = (design.components['Q' + str(i)].parse_options().pos_x + design.components[
#                     'Q' + str(i + Nx - 1)].parse_options().pos_x) / 2
#                 pos_y = (design.components['Q' + str(i)].parse_options().pos_y + design.components[
#                     'Q' + str(i + Nx - 1)].parse_options().pos_y) / 2
#                 LongRangeTunableCoupler01(design, 'long_range_tc_' + str(i) + '_' + str(i + Nx - 1),
#                                           options=Dict(pos_x=pos_x, pos_y=pos_y, orientation=str(angle), **options))
#                 flux_pos_x = pos_x - Lc * math.sin(math.radians(angle))
#                 flux_pos_y = pos_y + Lc * math.cos(math.radians(angle))
#                 if (i - 1) % Nx <= int(Nx / 2):
#                     MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx - 1),
#                                  options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=True, **opt))
#                 else:
#                     MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx - 1),
#                                  options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=True, **opt1))
#
#             # # add the readout resonators
#     rr_edge = 0.003
#     readout_cpw_width = 10
#     readout_cpw_gap = 6.28
#     rr_space = (rr_edge + parse_value(design.variables.cpw_gap, None)
#                 + parse_value(design.variables.cpw_width, None) / 2
#                 + (readout_cpw_width / 2 + readout_cpw_gap) * 1e-3)
#     readout_radius = 30
#     readout_cpw_turnradius = 15
#     vertical_start_length = 100
#     meander_round = 6
#
#     r_0 = readout_radius * 1e-3
#     r = readout_cpw_turnradius * 1e-3
#     l_2 = vertical_start_length * 1e-3
#     # l_6 = vertical_end_length*1e-3
#     turn_round_n = meander_round
#     vertical_end_length = (design.components['tl_l1'].parse_options().pos_y - rr_space - design.components[
#         'Q1'].parse_options().pos_y - r_0 - l_2 - 2 * r * (turn_round_n + 2.5)) * 1e3
#
#     options = Dict(
#         readout_radius=str(readout_radius)+'um',
#         readout_cpw_width=str(readout_cpw_width)+'um',
#         readout_cpw_gap=str(readout_cpw_gap)+'um',
#         readout_cpw_turnradius=str(readout_cpw_turnradius) + 'um',
#         vertical_start_length=str(vertical_start_length) + 'um',
#         vertical_end_length=str(vertical_end_length) + 'um',
#         horizontal_start_length01='200 um',
#         # horizontal_start_length02 = '400 um',
#         horizontal_end_length='200 um',
#         total_length='3600 um',
#         arc_step='1 um',
#         meander_round=str(meander_round),
#         orientation='0',
#         layer='1',
#         layer_subtract='1',
#         inverse=True,
#         mirror=False,
#         subtract=True,
#         chip='main',
#     )
#     location_x = 0
#     # the resonator is set to have its origin at the center of the circular patch.
#     # So we set the qubit and the resonator to share the same coordinate (q1_x, q1_y)
#     for i in range(int(total_qubit_num)):
#         MyReadoutRes01(design, 'R' + str(i + 1),
#                        options=Dict(pos_x=design.components['Q' + str(i + 1)].parse_options().pos_x + location_x,
#                                     pos_y=design.components['Q' + str(i + 1)].parse_options().pos_y, **options))
#     if parameter_file_path is not None:
#         parameter_import(design, convert_keys_to_int(load_json(parameter_file_path)))
#         gui.rebuild()
#         gui.autoscale()
#     else:
#         gui.rebuild()
#         gui.autoscale()
#     if jj_dict is not None:
#         for component_name, component in design.components.items():
#             if component_name.startswith('Q'):
#                 design.components[component_name].options.gds_cell_name = jj_dict[component_name]
#             if component_name.startswith('long_range'):
#                 design.components[component_name].options.gds_cell_name = jj_dict[component_name]
#     gui.rebuild()
#     gui.autoscale()
#     return design, gui


def qubit_flipchip_layout(chip_size, pad_num=42, rotation_angle=45, qq_space=2.5, row=6, column=10, shift_x=0,
                          shift_y=0, add_connector=False,jj_dict=None,parameter_file_path=None):
    # Initialise design
    design = designs.DesignPlanar()
    # Specify design name
    design.metadata['design_name'] = 'FlipChip_Device'
    # launch GUI
    gui = MetalGUI(design)
    # Allow running the same cell here multiple times to overwrite changes
    design.overwrite_enabled = True

    design.chips['main']['material'] = 'sapphire'
    design.chips['main']['size']['size_x'] = str(chip_size) + 'mm'
    design.chips['main']['size']['size_y'] = str(chip_size) + 'mm'
    design.variables.cpw_gap = '4 um'
    design.variables.cpw_width = '4 um'
    # design.chips,design.variables
    my_chip = MyCircle(design, 'my_chip', options=Dict(radius=str(chip_size + 2) + 'mm'))

    # design the layout of launchpad
    points = []
    N = pad_num
    size = chip_size - 2
    pad_pad_space = 0.7
    edge_gap = (size - (pad_pad_space * (N - 1))) / 2
    for i in range(N):
        shape = draw.Point(-size / 2 + edge_gap + i * pad_pad_space, size / 2)
        points.append(shape)
    # points.append()
    # for i in range(N):
    #     shape = draw.Point(size/2,size/2-i*size/N)
    x = draw.shapely.geometrycollections(points)
    x0 = draw.rotate(x, 90, origin=(0, 0))
    x1 = draw.rotate(x0, 90, origin=(0, 0))
    x2 = draw.rotate(x1, 90, origin=(0, 0))
    square = draw.shapely.geometrycollections([x, x0, x1, x2])
    square = draw.rotate(square, rotation_angle, origin=(0, 0))
    square_coords = []
    for i in range(4):
        for j in range(N):
            square_coords.append(square.geoms[i].geoms[j].coords[0])

    opt = Dict(pos_x=0, pos_y=0, orientation=str(-90 + rotation_angle), pad_width='245 um', pad_height='245 um',
               pad_gap='100 um',
               lead_length='50 um', chip='main')
    opt_a = Dict(pos_x=0, pos_y=0, orientation=str(rotation_angle), pad_width='245 um', pad_height='245 um',
                 pad_gap='100 um',
                 lead_length='50 um', chip='main')
    opt_b = Dict(pos_x=0, pos_y=0, orientation=str(rotation_angle + 90), pad_width='245 um', pad_height='245 um',
                 pad_gap='100 um',
                 lead_length='50 um', chip='main')
    opt_c = Dict(pos_x=0, pos_y=0, orientation=str(rotation_angle + 180), pad_width='245 um', pad_height='245 um',
                 pad_gap='100 um',
                 lead_length='50 um', chip='main')
    # test = OpenToGround(design, 'open01', options=Dict(pos_x='-3 mm',  pos_y=pos_y_zline+0.02, orientation='-45', chip ='C_chip'),)
    launch_zline = LaunchpadWirebond(design, 'launch_zline', options=opt)
    launch_zline_a = LaunchpadWirebond(design, 'launch_zline_a', options=opt_a)
    launch_zline_b = LaunchpadWirebond(design, 'launch_zline_b', options=opt_b)
    launch_zline_c = LaunchpadWirebond(design, 'launch_zline_c', options=opt_c)

    q0_x = 0
    q0_y = 0
    cross_length = 140
    cross_width = 24
    cross_gap = 30
    jj_pos_x = -0.42
    angle = 45

    options = Dict(
        pos_x=str(q0_x) + 'mm',
        pos_y=str(q0_y) + 'mm',  # 使用定义的qubit_y
        orientation=str(angle),
        layer="2",
        cross_width=str(cross_width) + 'um',
        cross_length=str(cross_length) + 'um',
        cross_length1=str(cross_length) + 'um',
        cross_gap=str(cross_gap) + 'um',
        radius='2um',
        rect_width='0um',
        rect_height='32um',
        jj_pos_x=str(jj_pos_x),
        jj_pad_width='8um',
        jj_pad_height='18um',
        jj_etch_length='4um',
        jj_etch_pad1_width='2um',
        jj_etch_pad2_width='5um',
        jj_pad2_height='8um',
        chip='main',
    )
    q0 = XmonFlipChip01(design, 'qubit0', options=options)

    design.delete_all_components()
    launch_list = []
    for i in range(4):
        for j in range(N):
            if (i == 0):
                launch_list.append(design.copy_qcomponent(launch_zline, 'launch_zline' + str(i) + str(j),
                                                          Dict(pos_x=square_coords[i * N + j][0],
                                                               pos_y=square_coords[i * N + j][1])))
            elif (i == 1):
                launch_list.append(design.copy_qcomponent(launch_zline_a, 'launch_zline' + str(i) + str(j),
                                                          Dict(pos_x=square_coords[i * N + j][0],
                                                               pos_y=square_coords[i * N + j][1])))
            elif (i == 2):
                launch_list.append(design.copy_qcomponent(launch_zline_b, 'launch_zline' + str(i) + str(j),
                                                          Dict(pos_x=square_coords[i * N + j][0],
                                                               pos_y=square_coords[i * N + j][1])))
            else:
                launch_list.append(design.copy_qcomponent(launch_zline_c, 'launch_zline' + str(i) + str(j),
                                                          Dict(pos_x=square_coords[i * N + j][0],
                                                               pos_y=square_coords[i * N + j][1])))

    # design the 56 qubits layout
    d = qq_space * math.sqrt(2) / 2
    Nx = column
    Ny = row
    shift_x = shift_x * 1e-3
    shift_y = shift_y * 1e-3
    q0_x = -((Nx - 1) / 2) * d * 2 + shift_x
    q0_y = Ny / 2 * d + shift_y
    total_qubit_num = Nx * Ny
    qubit_pos_list = []
    q0_x_list = []

    for i in range(Ny):
        q0_x_list.append(q0_x)
        q0_x = q0_x - (-1) ** int(i / 2) * d

    for i in range(Ny):
        for j in range(Nx):
            q_x = q0_x_list[i] + j * 2 * d
            q_y = q0_y - i * d
            qubit_pos_list.append((q_x, q_y))

    for i in range(int(total_qubit_num)):
        design.copy_qcomponent(q0, 'Q' + str(i + 1),
                               Dict(pos_x=str(qubit_pos_list[i][0]) + 'mm', pos_y=str(qubit_pos_list[i][1]) + 'mm'))

    # draw flux line
    control_line_cpw_width0 = '4 um'
    control_line_cpw_gap0 = '4 um'
    control_line_cpw_width = '4 um'
    control_line_cpw_gap = '4 um'
    opt = Dict(inverse=True, mirror=True, end_horizontal_length='20 um', flux_cpw_width0=control_line_cpw_width0,
               flux_cpw_gap0=control_line_cpw_gap0, flux_cpw_width=control_line_cpw_width, flux_cpw_gap=control_line_cpw_gap,
               angle='-60', angle_end='-30', end_yposition='80um',fillet='10um')
    for i in range(1, int(total_qubit_num) + 1):
        flux_pos_x = design.components['Q' + str(i)].parse_options().pos_x + jj_pos_x * cross_length * math.cos(
            math.radians(angle)) * 1e-3 \
                     - (design.components['Q' + str(i)].parse_options().jj_pad_width + design.components[
            'Q' + str(i)].parse_options().cross_width / 2.0
                        + design.components['Q' + str(i)].parse_options().cross_gap / 2.0) * math.sin(
            math.radians(angle))
        flux_pos_y = design.components['Q' + str(i)].parse_options().pos_y + jj_pos_x * cross_length * math.sin(
            math.radians(angle)) * 1e-3 \
                     + (design.components['Q' + str(i)].parse_options().jj_pad_width + design.components[
            'Q' + str(i)].parse_options().cross_width / 2.0
                        + design.components['Q' + str(i)].parse_options().cross_gap / 2.0) * math.cos(
            math.radians(angle))
        MyFluxLine02(design, 'flux_line' + str(i), options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, **opt))

    # #indium stop sign
    # pos_x1 = design.components['Q' + str(1)].parse_options().pos_x + 1
    # pos_y1 = design.components['Q' + str(1)].parse_options().pos_y + 2
    # pos_x2 = design.components['Q' + str(Nx*Ny)].parse_options().pos_x - 1
    # pos_y2 = design.components['Q' + str(Nx*Ny)].parse_options().pos_y - 2
    # stop_sign_width = 1400
    # stop_sign_height = 900
    # # pos_x3 = design.components['Q' + str(Nx*(Ny-1)+1)].parse_options().pos_x + 0.3
    # # pos_y3 = design.components['Q' + str(Nx*(Ny-1)+1)].parse_options().pos_y - 2
    # # pos_x4 = design.components['Q' + str(Nx*Ny)].parse_options().pos_x - 0.3
    # # pos_y4 = design.components['Q' + str(Nx*Ny)].parse_options().pos_y - 2
    # options = Dict(pos_x=pos_x1,pos_y=pos_y1,width=str(stop_sign_width)+'um',
    #                height=str(stop_sign_height)+'um',
    #                subtract='False',
    #                helper='False')
    # Rectangle(design, 'rectangle1', options=options)
    #
    # options = Dict(pos_x=pos_x2,pos_y=pos_y1,width=str(stop_sign_width)+'um',
    #                height=str(stop_sign_height)+'um',
    #                subtract='False',
    #                helper='False')
    # Rectangle(design, 'rectangle2', options=options)
    #
    # options = Dict(pos_x=pos_x1,pos_y=pos_y2,width=str(stop_sign_width)+'um',
    #                height=str(stop_sign_height)+'um',
    #                subtract='False',
    #                helper='False')
    # Rectangle(design, 'rectangle3', options=options)
    #
    # options = Dict(pos_x=pos_x2,pos_y=pos_y2,width=str(stop_sign_width)+'um',
    #                height=str(stop_sign_height)+'um',
    #                subtract='False',
    #                helper='False')
    # Rectangle(design, 'rectangle4', options=options)

    # transmission line layout
    tc_x_offset = 0.4
    tc_y_offset = 0.1
    for i in range(Ny):
        pos_x = design.components['Q' + str(1 + i * Nx)].parse_options().pos_x - tc_x_offset
        pos_y = design.components['Q' + str(1 + i * Nx)].parse_options().pos_y + d / 2 - tc_y_offset
        ShortToGround(design, 'tl_l' + str(i + 1), options=Dict(pos_x=pos_x, pos_y=pos_y, orientation='180'))
        ShortToGround(design, 'readout_line_' + str(i + 1) + '_left',
                      options=Dict(pos_x=pos_x, pos_y=pos_y, orientation='0'))
        pos_x = design.components['Q' + str((i + 1) * Nx)].parse_options().pos_x + tc_x_offset
        ShortToGround(design, 'tl_r' + str(i + 1), options=Dict(pos_x=pos_x, pos_y=pos_y, orientation='0'))
        ShortToGround(design, 'readout_line_' + str(i + 1) + '_right',
                      options=Dict(pos_x=pos_x, pos_y=pos_y, orientation='180'))

        pin_opt = Dict(pin_inputs=Dict(start_pin=Dict(component='tl_l' + str(i + 1), pin='short'),
                                       end_pin=Dict(component='tl_r' + str(i + 1), pin='short'), ),
                       trace_width='8um', trace_gap='4um', chip='main')
        RouteStraight(design, 'readout_line_' + str(i + 1), options=pin_opt)

    # draw tunable coupler
    p1_width = 10
    pp_space = 15
    cross_length = 140
    cross_width = 24
    cross_gap = 30
    coupling_length = 64
    coupling_width = 40
    finger_p_width = 40
    finger_pc_space = 3
    finger_c_width = 40
    jj_pad_height = 71
    c_width = 4
    c_gap = 130
    c_gap1 = 40
    qc_space = (coupling_width - p1_width - cross_width) / 2
    p1_length = p2_length = qq_space / 2 * 1e3 - cross_length - pp_space / 2 - p1_width - qc_space
    flux_line_vector_length = p1_width / 2
    options = Dict(p1_length=str(p1_length) + 'um',
                   p1_width=str(p1_width) + 'um',
                   p2_length=str(p2_length) + 'um',
                   p2_width=str(p1_width) + 'um',
                   coupling_width=str(coupling_width) + 'um',
                   coupling_length=str(coupling_length) + 'um',
                   finger_p_length='3um',
                   finger_p_width=str(finger_p_width) + 'um',
                   finger_pp_length='100um',
                   finger_pp_width='4um',
                   finger_c_length='4um',
                   finger_c_width=str(finger_c_width) + 'um',
                   finger_pc_space=str(finger_pc_space) + 'um',
                   finger_pp_space='3um',
                   finger_n='8',
                   finger_pp_n='2',
                   c_width=str(c_width) + 'um',
                   c_gap=str(c_gap) + 'um',
                   c_gap1=str(c_gap1) + 'um',
                   pp_space=str(pp_space) + 'um',
                   jj_pad_width='10um',
                   jj_pad_height=str(jj_pad_height) + 'um',
                   jj_etch_length='4um',
                   jj_etch_pad1_width='2um',
                   jj_etch_pad2_width='5um',
                   # jj_sub_rect_width='100um',
                   # jj_sub_rect_height='100um',
                   fl_length='0um',
                   fl_gap='2um',
                   fl_ground='3um',
                   fl_width='10um',
                   fillet='1um',
                   layer='2'
                   )
    opt = Dict(inverse=True, mirror=True, end_horizontal_length='20 um', flux_cpw_width0=control_line_cpw_width0,
               flux_cpw_gap0=control_line_cpw_gap0,
               flux_cpw_width=control_line_cpw_width, flux_cpw_gap=control_line_cpw_gap, angle='-60', angle_end='-30',
               end_yposition='80um')
    cycle_num = 2
    L1 = (finger_p_width + finger_pc_space + c_width + jj_pad_height) * 1e-3
    L = p1_width * 1e-3 / 2 + L1
    L_res = c_gap * 1e-3 - L1
    Lc = L + L_res / 2
    angle = 45
    opt = Dict(inverse=True, end_horizontal_length='10 um', flux_cpw_width0=control_line_cpw_width0,
               flux_cpw_gap0=control_line_cpw_gap0,
               flux_cpw_width=control_line_cpw_width, flux_cpw_gap=control_line_cpw_gap, c_length='0 um', angle='-60',
               angle_end='-30', end_yposition='60 um', fillet='1 um')
    opt1 = Dict(inverse=True, end_horizontal_length='10 um', flux_cpw_width0=control_line_cpw_width0,
                flux_cpw_gap0=control_line_cpw_gap0,
                flux_cpw_width=control_line_cpw_width, flux_cpw_gap=control_line_cpw_gap, c_length='0 um', angle='60',
                angle_end='30', end_yposition='60 um', fillet='1 um')
    for i in range(1, int(total_qubit_num - (Nx - 1))):
        criterion = int((int((i - 1) / Nx)) / cycle_num) % 2  # 周期性左右臂交错
        if criterion == 0:
            pos_x = (design.components['Q' + str(i)].parse_options().pos_x + design.components[
                'Q' + str(i + Nx)].parse_options().pos_x) / 2
            pos_y = (design.components['Q' + str(i)].parse_options().pos_y + design.components[
                'Q' + str(i + Nx)].parse_options().pos_y) / 2
            LongRangeTunableCoupler01(design, 'long_range_tc_' + str(i) + '_' + str(i + Nx),
                                      options=Dict(pos_x=pos_x, pos_y=pos_y, orientation=str(angle), **options))
            flux_pos_x = pos_x - Lc * math.sin(math.radians(angle))
            flux_pos_y = pos_y + Lc * math.cos(math.radians(angle))
            if i % Nx <= round(Nx / 2) and i % Nx != 0:
                MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx),
                             options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=True, **opt))
            else:
                MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx),
                             options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=True, **opt1))
            # 右臂可调耦合器
            if i % Nx != 0:
                pos_x = (design.components['Q' + str(i)].parse_options().pos_x + design.components[
                    'Q' + str(i + Nx + 1)].parse_options().pos_x) / 2
                pos_y = (design.components['Q' + str(i)].parse_options().pos_y + design.components[
                    'Q' + str(i + Nx + 1)].parse_options().pos_y) / 2
                LongRangeTunableCoupler01(design, 'long_range_tc_' + str(i) + '_' + str(i + Nx + 1),
                                          options=Dict(pos_x=pos_x, pos_y=pos_y, orientation=str(-angle), **options))
                flux_pos_x = pos_x - Lc * math.sin(math.radians(-angle))
                flux_pos_y = pos_y + Lc * math.cos(math.radians(-angle))
                if i % Nx < round(Nx / 2):
                    MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx + 1),
                                 options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=False, **opt1))
                else:
                    MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx + 1),
                                 options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=False, **opt))
        else:
            pos_x = (design.components['Q' + str(i)].parse_options().pos_x + design.components[
                'Q' + str(i + Nx)].parse_options().pos_x) / 2
            pos_y = (design.components['Q' + str(i)].parse_options().pos_y + design.components[
                'Q' + str(i + Nx)].parse_options().pos_y) / 2
            LongRangeTunableCoupler01(design, 'long_range_tc_' + str(i) + '_' + str(i + Nx),
                                      options=Dict(pos_x=pos_x, pos_y=pos_y, orientation=str(-angle), **options))
            flux_pos_x = pos_x - Lc * math.sin(math.radians(-angle))
            flux_pos_y = pos_y + Lc * math.cos(math.radians(-angle))
            if (i - 1) % Nx < int(Nx / 2):
                MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx),
                             options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=False, **opt1))
            else:
                MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx),
                             options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=False, **opt))
            if (i - 1) % Nx != 0:
                pos_x = (design.components['Q' + str(i)].parse_options().pos_x + design.components[
                    'Q' + str(i + Nx - 1)].parse_options().pos_x) / 2
                pos_y = (design.components['Q' + str(i)].parse_options().pos_y + design.components[
                    'Q' + str(i + Nx - 1)].parse_options().pos_y) / 2
                LongRangeTunableCoupler01(design, 'long_range_tc_' + str(i) + '_' + str(i + Nx - 1),
                                          options=Dict(pos_x=pos_x, pos_y=pos_y, orientation=str(angle), **options))
                flux_pos_x = pos_x - Lc * math.sin(math.radians(angle))
                flux_pos_y = pos_y + Lc * math.cos(math.radians(angle))
                if (i - 1) % Nx <= int(Nx / 2):
                    MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx - 1),
                                 options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=True, **opt))
                else:
                    MyFluxLine02(design, 'flux_line_c' + str(i) + '_' + str(i + Nx - 1),
                                 options=Dict(pos_x=flux_pos_x, pos_y=flux_pos_y, mirror=True, **opt1))

    for component_name, component in design.components.items():
        if component_name.startswith('Q'):
            design.components[component_name].options.gds_cell_name = 'FakeJunction_00'
            # design.components[component_name].options.jj_pad_height = '18um'
        if component_name.startswith('long_range_tc'):
            # design.components[component_name].options.jj_pad_height = '71um'
            if design.components[component_name].options.orientation == '45':
                design.components[component_name].options.gds_cell_name = 'FakeJunction_01'
            elif design.components[component_name].options.orientation == '-45':
                design.components[component_name].options.gds_cell_name = 'FakeJunction_02'
            # # add the readout resonators
    rr_edge = 0.003
    readout_cpw_width = 10
    readout_cpw_gap = 6.28
    rr_space = (rr_edge + parse_value(design.variables.cpw_gap, None)
                + parse_value(design.variables.cpw_width, None) / 2
                + (readout_cpw_width / 2 + readout_cpw_gap) * 1e-3)
    readout_radius = 30
    readout_cpw_turnradius = 25
    vertical_start_length = 100
    meander_round = 4

    r_0 = readout_radius * 1e-3
    r = readout_cpw_turnradius * 1e-3
    l_2 = vertical_start_length * 1e-3
    # l_6 = vertical_end_length*1e-3
    turn_round_n = meander_round
    vertical_end_length = (design.components['tl_l1'].parse_options().pos_y - rr_space - design.components[
        'Q1'].parse_options().pos_y - r_0 - l_2 - 2 * r * (turn_round_n + 2.5)) * 1e3

    options = Dict(
        readout_radius=str(readout_radius)+'um',
        readout_cpw_width=str(readout_cpw_width)+'um',
        readout_cpw_gap=str(readout_cpw_gap)+'um',
        readout_cpw_turnradius=str(readout_cpw_turnradius) + 'um',
        vertical_start_length=str(vertical_start_length) + 'um',
        vertical_end_length=str(vertical_end_length) + 'um',
        horizontal_start_length01='200 um',
        # horizontal_start_length02 = '400 um',
        horizontal_end_length='200 um',
        total_length='3600 um',
        arc_step='1 um',
        meander_round=str(meander_round),
        orientation='0',
        layer='1',
        layer_subtract='1',
        inverse=True,
        mirror=False,
        subtract=True,
        chip='main',
    )
    location_x = 0
    # the resonator is set to have its origin at the center of the circular patch.
    # So we set the qubit and the resonator to share the same coordinate (q1_x, q1_y)
    total_length = [4529.7028148789905, 4345.706273034945, 4497.227412721164, 4404.390789948849, 4466.666350763531,
                         4376.6455845918, 4435.806264106092,
                         4510.99088545463, 4332.517312711658, 4479.541163427934, 4389.407696034727, 4448.798408849052,
                         4360.528991199287, 4419.923479317982,
                         4536.127939174699, 4342.77061281077, 4501.0881253468915, 4402.731072264635, 4467.177039819279,
                         4372.1913349376055, 4434.39217359186,
                         4512.309524698308, 4326.279795804026, 4479.926222346395, 4386.093559877532, 4448.097361042293,
                         4355.914039216872, 4416.820578186006,
                         4532.5730923234105, 4339.889997439598, 4497.646265825621, 4399.626676333424, 4463.847914328028,
                         4369.198945336413, 4431.175534030628,
                         4509.046176189466, 4323.346277543871, 4476.718425712333, 4383.051007467814, 4444.944877683013,
                         4352.926113681935, 4413.7231748015065,
                         4529.029555825124, 4337.020547021426, 4494.215691057353, 4396.533491555214, 4460.53004838978,
                         4366.217743488223, 4427.970129722399,
                         4505.788393828101, 4320.418188131193, 4473.51617102575, 4380.013927705574, 4441.79791287121,
                         4349.943638694477, 4410.6312665644855,
                         4525.497326979837, 4334.162259256257, 4490.796398542087, 4393.451515730007, 4457.223439704533,
                         4363.247727193035, 4424.775958167172,
                         4502.5361751142145, 4317.4955253659955, 4470.319456086644, 4376.982318390813,
                         4438.656464106887, 4346.966611954498, 4407.544851474943,
                         4563.47303440772, 4366.5376136537325, 4527.881573214903, 4427.760754737617, 4493.40044012228,
                         4396.598111945577, 4460.027523029851,
                         4540.641106933034, 4353.518626114406, 4508.118022843729, 4413.763014662694, 4476.131978402238,
                         4383.376198364644, 4444.680965108559,
                         4559.863862379929, 4363.592106706057, 4524.383530317131, 4424.594837829904, 4490.013313154528,
                         4393.542497967883, 4456.7511031921185,
                         4537.364573650453, 4350.561905680513, 4504.895285135928, 4410.700463479237, 4472.962833469219,
                         4380.366655955968, 4441.56521435032,
                         4556.26581300514, 4360.657599911386, 4520.896588572362, 4421.439960175193, 4486.637266139778,
                         4390.497903343193, 4453.485742807388]

    horizontal_end_length = [185.7107435, 155.9976719, 179.6109385, 163.8185916, 172.7795686, 157.719691,
                                  167.4299987,
                                  236.6168377, 208.4931721, 232.2317998, 218.2255159, 227.7005492, 213.5124798,
                                  221.8622283,
                                  175.3748736, 155.7322517, 171.9577578, 162.0406738, 168.594689, 158.8545827,
                                  165.2881762,
                                  231.6894885, 211.4584319, 228.2941064, 218.155244, 224.905038, 214.7990992,
                                  221.5246459,
                                  175.0308026, 155.4236144, 171.618977, 161.719262, 168.2614517, 158.5394421,
                                  164.9607305,
                                  231.3497346, 211.1253006, 227.9548761, 217.8189959, 224.5665699, 214.4642997,
                                  221.1871733,
                                  174.687249, 155.1156399, 171.2807392, 161.3984668, 167.9287826, 158.2249415,
                                  164.6338773,
                                  231.0100221, 210.792348, 227.6157114, 217.4828827, 224.2281908, 214.1296572,
                                  220.8498131,
                                  174.3442155, 154.8083305, 170.9430469, 161.0782904, 167.596684, 157.9110831,
                                  164.3076191,
                                  230.6703535, 210.4595763, 227.2766145, 217.1469066, 223.8899032, 213.795174,
                                  220.5125673,
                                  149.9836727, 133.5643126, 147.0590655, 138.7283306, 144.2069055, 136.1060062,
                                  141.4293048,
                                  205.1615603, 185.8550292, 201.8779222, 192.1772923, 198.6179992, 189.0004054,
                                  195.3837998,
                                  149.688013, 133.314653, 146.7705542, 138.4625259, 143.9257558, 135.8481761,
                                  141.1557255,
                                  204.8321874, 185.5422963, 201.5508292, 191.8582392, 198.2933889, 188.684419,
                                  195.0618708,
                                  149.3930584, 133.065821, 146.4827695, 138.1975097, 143.6453539, 135.5911544,
                                  140.8829145]
    # print(f'total_length = {total_length}')

    # the resonator is set to have its origin at the center of the circular patch.
    # So we set the qubit and the resonator to share the same coordinate (q1_x, q1_y)
    for i in range(int(total_qubit_num)):
        # total_length_V01
        options['total_length'] = str(total_length[i]) + 'um'
        options['horizontal_end_length'] = f'{horizontal_end_length[i]} um'

        MyReadoutRes01(design, 'R' + str(i + 1),
                       options=Dict(pos_x=design.components['Q' + str(i + 1)].parse_options().pos_x + location_x,
                                    pos_y=design.components['Q' + str(i + 1)].parse_options().pos_y, **options))
        if i % 7 == 0:
            design.components['R'+str(i+1)].options.mirror = True
    if add_connector is True:
        connector_shift_x = 1.73
        spacing = 0.1
        left_connector_pos_x = design.components['Q15'].parse_options().pos_x - connector_shift_x
        right_connector_pos_x = design.components['Q7'].parse_options().pos_x + connector_shift_x
        num_connectors_left_list = [10,12,12,11,10,12,12,11,10,12,12,11,10,12,5]
        num_connectors_right_list = [12,10,10,11,12,10,10,11,12,10,10,11,12,10,4]
        readout_distance =(design.components['tl_l'+str(2)].parse_options().pos_y -
                               design.components['tl_l'+str(1)].parse_options().pos_y)/2
        for i in range(1,row+1):
            connector_pos_y0 = design.components['tl_l'+str(i)].parse_options().pos_y + readout_distance

            # print(connector_pos_y0)
            for j in range(1,num_connectors_left_list[i-1]+1):
                offset = (j - 1 - (num_connectors_left_list[i-1] - 1) / 2.0) * spacing
                left_connector_pos_y = connector_pos_y0 + offset
                MyConnector(design, f'left_connector_{i}_{j}',
                                         options=Dict(pos_x=left_connector_pos_x, pos_y=left_connector_pos_y, width='4um',
                                                      gap=str(4) + 'um',
                                                      width0='10um', gap0='5um', length='10um', orientation='0'))
            for j in range(1,num_connectors_right_list[i-1]+1):
                offset = (j - 1 - (num_connectors_right_list[i-1] - 1) / 2.0) * spacing
                right_connector_pos_y = connector_pos_y0 + offset
                MyConnector(design, f'right_connector{i}_{j}',
                                         options=Dict(pos_x=right_connector_pos_x, pos_y=right_connector_pos_y, width='4um',
                                                      gap=str(4) + 'um',
                                                      width0='10um', gap0='5um', length='10um', orientation='180'))




    if parameter_file_path is not None:
        parameter_import(design, convert_keys_to_int(load_json(parameter_file_path)))
        gui.rebuild()
        gui.autoscale()
    else:
        gui.rebuild()
        gui.autoscale()
    if jj_dict is not None:
        for component_name, component in design.components.items():
            if component_name.startswith('Q'):
                design.components[component_name].options.gds_cell_name = jj_dict[component_name]
            if component_name.startswith('long_range'):
                design.components[component_name].options.gds_cell_name = jj_dict[component_name]
    gui.rebuild()
    gui.autoscale()
    return design, gui

def qubit_delete(design, gui, qubit_delete_file_path):
    """Delete specified qubits and their associated components"""
    delete_list = []
    with open(qubit_delete_file_path, 'r') as file:
        even_numbers_from_file = [int(line.strip()) for line in file]
    for i in even_numbers_from_file:
        pattern = rf'(?<!\d){i}(?!\d)'
        delete_list.append('Q'+str(i))
        delete_list.append('flux_line'+str(i))
        # design.delete_component('R'+str(i))
        # design.delete_component('flux_line'+str(i))
        for name in design.components:
            if re.search(pattern, name) and (name.startswith('long_range_tc') or name.startswith('flux_line_c')):
                delete_list.append(name)
    for name in delete_list:
        if name in design.components:
            design.delete_component(name)
    gui.rebuild()
    gui.autoscale()
    return design, gui


def launchpad_coord(design, out_file='end_lanuch.txt'):
    # 初始化一个空列表来存储所有焊盘的 'middle' 属性
    middle_points_coordinates = []

    # 遍历设计中的所有组件
    for component_name, component in design.components.items():
        # 检查组件名称是否以 'launch_zline' 开头，这假设所有焊盘组件都以此命名
        if component_name.startswith('launch_zline'):
            # 遍历焊盘的所有引脚
            for pin_name, pin in component.pins.items():
                # 检查引脚是否有 'middle' 属性
                if 'middle' in pin:
                    # 提取 'middle' 属性的坐标
                    middle_point = pin['middle']
                    direction = pin['normal']
                    # 将组件名称和 'middle' 点的坐标添加到列表中
                    middle_points_coordinates.append(
                        (component_name, middle_point[0], middle_point[1], list(direction)))

    # 对列表进行排序，根据组件名称中的数字进行排序
    middle_points_coordinates.sort(key=lambda x: int(x[0].replace('launch_zline', '')))
    folder_name = 'data'

    # 打印所有焊盘的 'middle' 点的坐标
    for coord in middle_points_coordinates:
        print(f"Component: {coord[0]}, Middle Point X: {coord[1]}, Middle Point Y: {coord[2]},Direction: {coord[3]}")
    if not os.path.exists(folder_name):
        # Create the folder if it does not exist
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created.")

        # 将这些坐标导出到同文件夹下的文件end_launch.txt中
    with open(folder_name + '/' + out_file, 'w') as file:
        for coord in middle_points_coordinates:
            file.write(
                f"Component: {coord[0]}, Middle Point X: {coord[1]}, Middle Point Y: {coord[2]}, Direction: {coord[3]}\n")


def end_connector_coord(design, out_file='end_connector.txt'):
    # 初始化一个空列表来存储所有焊盘的 'middle' 属性
    middle_points_coordinates = []

    # 遍历设计中的所有组件
    for component_name, component in design.components.items():
        # 检查组件名称是否以 'launch_zline' 开头，这假设所有焊盘组件都以此命名
        if component_name.startswith('left_connector'):
            # 遍历焊盘的所有引脚
            for pin_name, pin in component.pins.items():
                if pin_name == 'c_pin_r':
                    # 检查引脚是否有 'middle' 属性
                    if 'middle' in pin:
                        # 提取 'middle' 属性的坐标
                        middle_point = pin['middle']
                        direction = pin['normal']
                        # 将组件名称和 'middle' 点的坐标添加到列表中
                        middle_points_coordinates.append(
                            (component_name, middle_point[0], middle_point[1], list(direction)))

        if component_name.startswith('right_connector'):
            # 遍历焊盘的所有引脚
            for pin_name, pin in component.pins.items():
                if pin_name == 'c_pin_l':
                    # 检查引脚是否有 'middle' 属性
                    if 'middle' in pin:
                        # 提取 'middle' 属性的坐标
                        middle_point = pin['middle']
                        direction = pin['normal']
                        # 将组件名称和 'middle' 点的坐标添加到列表中
                        middle_points_coordinates.append(
                            (component_name, middle_point[0], middle_point[1], list(direction)))

    # 对列表进行排序，根据组件名称中的数字进行排序
    # middle_points_coordinates.sort(key=lambda x: int(x[0].replace('left_connector', '')))
    folder_name = 'data'

    # 打印所有焊盘的 'middle' 点的坐标
    for coord in middle_points_coordinates:
        print(f"Component: {coord[0]}, Middle Point X: {coord[1]}, Middle Point Y: {coord[2]},Direction: {coord[3]}")
    if not os.path.exists(folder_name):
        # Create the folder if it does not exist
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created.")

        # 将这些坐标导出到同文件夹下的文件end_launch.txt中
    with open(folder_name + '/' + out_file, 'w') as file:
        for coord in middle_points_coordinates:
            file.write(
                f"Component: {coord[0]}, Middle Point X: {coord[1]}, Middle Point Y: {coord[2]}, Direction: {coord[3]}\n")


def start_connector_coord(design, out_file='start_connector.txt'):
    # 初始化一个空列表来存储所有焊盘的 'middle' 属性
    middle_points_coordinates = []
    # 遍历设计中的所有组件
    for component_name, component in design.components.items():
        # 检查组件名称是否以 'launch_zline' 开头，这假设所有焊盘组件都以此命名
        if component_name.startswith('left_connector'):
            # 遍历焊盘的所有引脚
            for pin_name, pin in component.pins.items():
                if pin_name == 'c_pin_l':
                    # 检查引脚是否有 'middle' 属性
                    if 'middle' in pin:
                        # 提取 'middle' 属性的坐标
                        middle_point = pin['middle']
                        direction = pin['normal']
                        # 将组件名称和 'middle' 点的坐标添加到列表中
                        middle_points_coordinates.append(
                            (component_name, middle_point[0], middle_point[1], list(direction)))

        if component_name.startswith('right_connector'):
            # 遍历焊盘的所有引脚
            for pin_name, pin in component.pins.items():
                if pin_name == 'c_pin_r':
                    # 检查引脚是否有 'middle' 属性
                    if 'middle' in pin:
                        # 提取 'middle' 属性的坐标
                        middle_point = pin['middle']
                        direction = pin['normal']
                        # 将组件名称和 'middle' 点的坐标添加到列表中
                        middle_points_coordinates.append(
                            (component_name, middle_point[0], middle_point[1], list(direction)))

    # 对列表进行排序，根据组件名称中的数字进行排序
    # middle_points_coordinates.sort(key=lambda x: int(x[0].replace('left_connector', '')))
    folder_name = 'data'

    # 打印所有焊盘的 'middle' 点的坐标
    for coord in middle_points_coordinates:
        print(f"Component: {coord[0]}, Middle Point X: {coord[1]}, Middle Point Y: {coord[2]},Direction: {coord[3]}")
    if not os.path.exists(folder_name):
        # Create the folder if it does not exist
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created.")

        # 将这些坐标导出到同文件夹下的文件end_launch.txt中
    with open(folder_name + '/' + out_file, 'w') as file:
        for coord in middle_points_coordinates:
            file.write(
                f"Component: {coord[0]}, Middle Point X: {coord[1]}, Middle Point Y: {coord[2]}, Direction: {coord[3]}\n")


# 定义一个函数来提取极端坐标
def extract_extreme_coordinates_qbits(design, row, column, excluded_qubits=[], table_name='poly'):
    total_qubit_num = row * column
    all_extreme_coords = {}
    pos_x1 = design.components['Q' + str(1)].parse_options().pos_x + 1
    pos_y1 = design.components['Q' + str(1)].parse_options().pos_y + 2
    pos_x2 = design.components['Q' + str(row*column)].parse_options().pos_x - 1
    pos_y2 = design.components['Q' + str(row*column)].parse_options().pos_y - 2
    stop_sign_width = 1500*1e-3
    stop_sign_height = 1500*1e-3
    all_extreme_coords['rectangle1'] = [((pos_x1-stop_sign_width/2,pos_y1-stop_sign_height/2),
                                        (pos_x1-stop_sign_width/2,pos_y1+stop_sign_height/2),
                                        (pos_x1+stop_sign_width/2,pos_y1-stop_sign_height/2),
                                        (pos_x1+stop_sign_width/2,pos_y1+stop_sign_height/2))]
    all_extreme_coords['rectangle2'] = [((pos_x2-stop_sign_width/2,pos_y1-stop_sign_height/2),
                                        (pos_x2-stop_sign_width/2,pos_y1+stop_sign_height/2),
                                        (pos_x2+stop_sign_width/2,pos_y1-stop_sign_height/2),
                                        (pos_x2+stop_sign_width/2,pos_y1+stop_sign_height/2))]
    all_extreme_coords['rectangle3'] = [((pos_x1-stop_sign_width/2,pos_y2-stop_sign_height/2),
                                        (pos_x1-stop_sign_width/2,pos_y2+stop_sign_height/2),
                                        (pos_x1+stop_sign_width/2,pos_y2-stop_sign_height/2),
                                        (pos_x1+stop_sign_width/2,pos_y2+stop_sign_height/2))]
    all_extreme_coords['rectangle4'] = [((pos_x2-stop_sign_width/2,pos_y2-stop_sign_height/2),
                                        (pos_x2-stop_sign_width/2,pos_y2+stop_sign_height/2),
                                        (pos_x2+stop_sign_width/2,pos_y2-stop_sign_height/2),
                                        (pos_x2+stop_sign_width/2,pos_y2+stop_sign_height/2))]

    for i in range(1, int(total_qubit_num) + 1):  # 从 Q0 到 Q100
        component_name = f'Q{i}'
        poly_geometry_dict = design.qgeometry.get_component_geometry_dict(name=component_name,
                                                                          table_name=table_name)

        if poly_geometry_dict and i not in excluded_qubits:
            geometry_dict = {key: mapping(value) for key, value in poly_geometry_dict.items()}
            extreme_coords = []
            for key, value in geometry_dict.items():
                if key == 'cross_etch':
                    coordinates = value['coordinates'][0]  # 假设每个几何对象只有一个外环
                    x_values = [coord[0] for coord in coordinates]
                    y_values = [coord[1] for coord in coordinates]

                    min_x = min(x_values)
                    max_x = max(x_values)
                    min_y = min(y_values)
                    max_y = max(y_values)

                    # min_x_coords = [coord for coord in coordinates if coord[0] == min_x]
                    # max_x_coords = [coord for coord in coordinates if coord[0] == max_x]
                    # min_y_coords = [coord for coord in coordinates if coord[1] == min_y]
                    # max_y_coords = [coord for coord in coordinates if coord[1] == max_y]
                    #
                    # min_x_min_y_coord = min(min_x_coords, key=lambda coord: coord[1])
                    # min_x_max_y_coord = max(min_x_coords, key=lambda coord: coord[1])
                    # max_x_min_y_coord = min(max_x_coords, key=lambda coord: coord[1])
                    # max_x_max_y_coord = max(max_x_coords, key=lambda coord: coord[1])
                    #
                    # min_y_min_x_coord = min(min_y_coords, key=lambda coord: coord[0])
                    # min_y_max_x_coord = max(min_y_coords, key=lambda coord: coord[0])
                    # max_y_min_x_coord = min(max_y_coords, key=lambda coord: coord[0])
                    # max_y_max_x_coord = max(max_y_coords, key=lambda coord: coord[0])

                    extreme_coords.append(
                        ((min_x,min_y), (max_x,min_y), (max_x,max_y), (min_x,max_y)))

                    # # 如果当前量子比特不在排除列表中，添加纵向矩形顶点坐标
                    # if i not in excluded_qubits:
                    #     extreme_coords.append(
                    #         ((), (), max_y_min_x_coord, max_y_max_x_coord))
            all_extreme_coords[component_name] = extreme_coords
        else:
            print(f"量子比特 {component_name} 的几何对象为空或不存在。")

    return all_extreme_coords


def qubit_forbidden_zone(design, row, column, excluded_qubits=[],outfile='Qubit_forbidden_zone.txt'):
    # excluded_qubits = []
    folder_name = 'data'
    # 提取所有量子比特的极端坐标
    all_extreme_coords = extract_extreme_coordinates_qbits(design, row, column,excluded_qubits=excluded_qubits)
    # 打印输出
    for component_name, extreme_coords in all_extreme_coords.items():
        if component_name.startswith('Q'):
            for idx, coords in enumerate(extreme_coords, start=1):
                # if idx == 1:
                print(f"量子比特{component_name}不可布线区域： {', '.join(map(str, coords))}")
        elif component_name.startswith('rectangle'):
            for idx, coords in enumerate(extreme_coords, start=1):
                # if idx == 1:
                print(f"停止柱{component_name}不可布线区域： {', '.join(map(str, coords))}\n")
    if not os.path.exists(folder_name):
        # Create the folder if it does not exist
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created.")
    # 将输出内容保存到文件
    with open(folder_name + '/' + outfile, 'w') as file:
        for component_name, extreme_coords in all_extreme_coords.items():
            if component_name.startswith('Q'):
                for idx, coords in enumerate(extreme_coords, start=1):
                    # if idx == 1:
                    file.write(f"量子比特{component_name}不可布线区域： {', '.join(map(str, coords))}\n")
            elif component_name.startswith('rectangle'):
                for idx, coords in enumerate(extreme_coords, start=1):
                    # if idx == 1:
                    file.write(f"停止柱{component_name}不可布线区域： {', '.join(map(str, coords))}\n")




def extract_extreme_coordinates_resonator_category(geometry_dict):
    extreme_coords = {}
    for key, value in geometry_dict.items():
        coordinates = value['coordinates'][0]  # 假设每个几何对象只有一个外环
        x_values = [coord[0] for coord in coordinates]
        y_values = [coord[1] for coord in coordinates]

        min_x = min(x_values)
        max_x = max(x_values)
        min_y = min(y_values)
        max_y = max(y_values)

        min_x_coords = [coord for coord in coordinates if coord[0] == min_x]
        max_x_coords = [coord for coord in coordinates if coord[0] == max_x]
        min_y_coords = [coord for coord in coordinates if coord[1] == min_y]
        max_y_coords = [coord for coord in coordinates if coord[1] == max_y]

        min_x_min_y_coord = min(min_x_coords, key=lambda coord: coord[1])
        min_x_max_y_coord = max(min_x_coords, key=lambda coord: coord[1])
        max_x_min_y_coord = min(max_x_coords, key=lambda coord: coord[1])
        max_x_max_y_coord = max(max_x_coords, key=lambda coord: coord[1])

        min_y_min_x_coord = min(min_y_coords, key=lambda coord: coord[0])
        min_y_max_x_coord = max(min_y_coords, key=lambda coord: coord[0])
        max_y_min_x_coord = min(max_y_coords, key=lambda coord: coord[0])
        max_y_max_x_coord = max(max_y_coords, key=lambda coord: coord[0])

        extreme_coords[key] = {
            'min_x_min_y': min_x_min_y_coord,
            'min_x_max_y': min_x_max_y_coord,
            'max_x_min_y': max_x_min_y_coord,
            'max_x_max_y': max_x_max_y_coord,
            'min_y_min_x': min_y_min_x_coord,
            'min_y_max_x': min_y_max_x_coord,
            'max_y_min_x': max_y_min_x_coord,
            'max_y_max_x': max_y_max_x_coord
        }
    return extreme_coords


def _compute_resonator_forbidden_rects(design, resonator):
    """Compute two forbidden-zone rectangles for a resonator by splitting at
    the first bend: rect1 = coupling pad + stem, rect2 = meander section.
    Returns a list of rectangles [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]."""
    p = design.components[resonator].parse_options()
    poly_geometry_dict = design.qgeometry.get_component_geometry_dict(
        name=resonator, table_name='poly')
    if 'ro' not in poly_geometry_dict:
        return []

    ro_polygon = poly_geometry_dict['ro']
    bx = ro_polygon.bounds  # (min_x, min_y, max_x, max_y)

    r = p.readout_radius
    l_2 = p.vertical_start_length
    turnradius = p.readout_cpw_turnradius
    w = p.readout_cpw_width
    g = p.readout_cpw_gap
    bend_offset = r + l_2 + turnradius
    # The first horizontal line sits at bend_y and is buffered by w/2+g.
    # Shift the clip boundary by this margin so the horizontal line's
    # buffer stays entirely in the meander rectangle.
    margin = w / 2 + g

    # inverse=False (default): negate applied, stem goes DOWN → bend below pad
    # inverse=True: double negate cancels, stem goes UP → bend above pad
    if p.inverse:
        bend_y = p.pos_y + bend_offset
        clip_y = bend_y - margin
        stem_clip = ShapelyBox(bx[0] - 1, bx[1] - 1, bx[2] + 1, clip_y)
        meander_clip = ShapelyBox(bx[0] - 1, clip_y, bx[2] + 1, bx[3] + 1)
    else:
        bend_y = p.pos_y - bend_offset
        clip_y = bend_y + margin
        stem_clip = ShapelyBox(bx[0] - 1, clip_y, bx[2] + 1, bx[3] + 1)
        meander_clip = ShapelyBox(bx[0] - 1, bx[1] - 1, bx[2] + 1, clip_y)

    rects = []
    for clip in [stem_clip, meander_clip]:
        part = ro_polygon.intersection(clip)
        if part.is_empty:
            continue
        if part.geom_type == 'GeometryCollection':
            polys = [g for g in part.geoms
                     if g.geom_type in ('Polygon', 'MultiPolygon')]
            if not polys:
                continue
            from shapely.ops import unary_union
            part = unary_union(polys)
        b = part.bounds  # (min_x, min_y, max_x, max_y)
        rects.append([(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])])
    return rects


def process_resonator_category(design, resonator, output_file):
    rects = _compute_resonator_forbidden_rects(design, resonator)
    for idx, rect in enumerate(rects, start=1):
        rect_str = ', '.join(f'({x}, {y})' for x, y in rect)
        output_str = f"谐振腔{resonator}不可布线矩形区域{idx}的顶点坐标为：{rect_str}"
        print(output_str)
        output_file.write(output_str + '\n')


def resonator_forbidden_zone(design, row, column):
    total_qubit_num = row * column
    category = []
    folder_name = 'data'
    # 遍历 R0 到 R100 的谐振腔
    for i in range(1, int(total_qubit_num) + 1):  # 从 R0 到 R100，共101个
        resonator_name = f'R{i}'
        category.append(resonator_name)
    if not os.path.exists(folder_name):
        # Create the folder if it does not exist
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created.")
    # 打开文件用于写入
    with open(folder_name + '/' + 'resonators_forbidden_zone.txt', 'w') as output_file:
        for resonator in category:
            process_resonator_category(design, resonator, output_file)


def control_readout_line_coord(design, excluded_qubits=[]):
    # 导出Flux Line（磁通量线）控制线起点坐标
    # 初始化一个空列表来存储所有 flux_line 的 'middle' 属性
    all_middle_points_flux = []
    delete_list = []
    for i in excluded_qubits:
        pattern = rf'(?<!\d){i}(?!\d)'
        delete_list.append('flux_line' + str(i))
        for name in design.components:
            if re.search(pattern, name) and name.startswith('flux_line_c'):
                delete_list.append(name)
    # 遍历设计中的所有组件
    for component_name, component in design.components.items():
        # 检查组件名称是否以 'flux_line' 开头，这假设所有 flux_line 组件都以此命名；同时排除控制线起始部分末端与虚拟引脚之间的连线
        if component_name.startswith('flux_line') and 'virtual' not in component_name and component_name not in delete_list:
            # 遍历 flux_line 的所有引脚
            for pin_name, pin in component.pins.items():
                # 检查引脚是否有 'middle' 属性
                if 'middle' in pin:
                    # 提取 'middle' 属性的坐标
                    middle_point = pin['middle']
                    direction = pin['normal']
                    # 将组件名称和 'middle' 点的坐标添加到列表中
                    all_middle_points_flux.append((component_name, middle_point[0], middle_point[1], list(direction)))

    # # 对列表进行排序，根据组件名称中的数字进行排序
    # all_middle_points_flux.sort(key=lambda x: int(x[0].replace('flux_line', '')))

    # ************************************************************************************************
    # 导出XY Line（XY线）控制线起点坐标
    # 初始化一个空列表来存储所有 xy_line 的 'middle' 属性
    all_middle_points_xy = []

    # 遍历设计中的所有组件
    for component_name, component in design.components.items():
        # 检查组件名称是否以 'xy_line' 开头，这假设所有 xy_line 组件都以此命名；同时排除控制线起始部分末端与虚拟引脚之间的连线
        if component_name.startswith('xy_line') and 'virtual' not in component_name:
            # 遍历 xy_line 的所有引脚
            for pin_name, pin in component.pins.items():
                # 检查引脚是否有 'middle' 属性
                if 'middle' in pin:
                    # 提取 'middle' 属性的坐标
                    middle_point = pin['middle']
                    direction = pin['normal']
                    # 将组件名称和 'middle' 点的坐标添加到列表中
                    all_middle_points_xy.append((component_name, middle_point[0], middle_point[1], list(direction)))

    # 对列表进行排序，根据组件名称中的数字进行排序
    all_middle_points_xy.sort(key=lambda x: int(x[0].replace('xy_line', '')))

    # *************************************************************************************************
    # 导出readout_line（读出线）端点坐标
    # 初始化一个空列表来存储读出线的起始和结束坐标
    all_points_readout = []

    # 遍历 readout_line_list 获取每个读出线的 RoutePathfinder 对象
    for component_name, component in design.components.items():
        if component_name.startswith('readout_line') and not component_name.endswith('left') and not component_name.endswith('right'):
            # 获取起始引脚和结束引脚的组件名称和引脚名称
            start_component = component.options['pin_inputs']['start_pin']['component']
            end_component = component.options['pin_inputs']['end_pin']['component']

            # 获取起始引脚的坐标
            start_pin_options = design.components[start_component].parse_options()
            start_pin_x = start_pin_options.pos_x  # 起始引脚的x坐标存储在pos_x中
            start_pin_y = start_pin_options.pos_y  # 起始引脚的y坐标存储在pos_y中

            # 获取结束引脚的坐标
            end_pin_options = design.components[end_component].parse_options()
            end_pin_x = end_pin_options.pos_x
            end_pin_y = end_pin_options.pos_y

            # 将起始和结束引脚的坐标信息作为一个元组追加到列表中
            all_points_readout.append((component.name, start_pin_x, start_pin_y, end_pin_x, end_pin_y))

    # *********************************************************************************************************************************#
    # -----------把所有控制线布线起点坐标写入start_control_line.txt中-----------#
    folder_name = 'data'
    if not os.path.exists(folder_name):
        # Create the folder if it does not exist
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created.")
    with open(folder_name + '/' + 'start_control_line.txt', 'w') as file:
        # 写入并打印 flux_line 的 'middle' 点的坐标
        for name, x, y, z in all_middle_points_flux:
            output = f"Component: {name}({name}), Middle Point X: {x}, Middle Point Y: {y}, Direction: {z}"
            file.write(output + "\n")
            print(output)

        # 写入并打印 xy_line 的 'middle' 点的坐标
        for name, x, y in all_middle_points_xy:
            output = f"Component: {name}({name}), Middle Point X: {x}, Middle Point Y: {y}, Direction: {z}"
            file.write(output + "\n")
            print(output)

    # -------------把所有读取线布线起点坐标写入start_readout_line.txt中-----------#
    with open(folder_name + '/' + 'start_readout_line.txt', 'w') as file:
        # 写入并打印 readout_line 的 'start' 和 'end' 点的坐标
        for name, start_x, start_y, end_x, end_y in all_points_readout:
            # 判断读取线两侧的起始点/结束点的相对位置
            if start_x < end_x:
                start_output = f"Component: {name}({name}_left), Start Point X: {start_x}, Start Point Y: {start_y}"
                end_output = f"Component: {name}({name}_right), End Point X: {end_x}, End Point Y: {end_y}"
            elif start_x > end_x:
                start_output = f"Component: {name}({name}_right), Start Point X: {start_x}, Start Point Y: {start_y}"
                end_output = f"Component: {name}({name}_left), End Point X: {end_x}, End Point Y: {end_y}"
            else:
                # 如果 x 坐标相同，则不添加左右标识
                start_output = f"Component: {name}, Start Point X: {start_x}, Start Point Y: {start_y}"
                end_output = f"Component: {name}, End Point X: {end_x}, End Point Y: {end_y}"

            file.write(start_output + "\n" + end_output + "\n")
            print(start_output)
            print(end_output)

    # *********************************************************************************
    # 导出控制线起始部分占用的不可布线区域坐标

    # 假设 design.qgeometry.get_component_geometry_dict 是一个可以获取几何字典的方法


def get_geometry_dict(design, name, table_name='poly'):
    return design.qgeometry.get_component_geometry_dict(name=name, table_name=table_name)


def extract_extreme_coordinates_control_lines(geometry_dict):
    # 初始化变量以存储所有坐标的最小和最大值
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    # 遍历每个几何对象的坐标
    for value in geometry_dict.values():
        for coord in value['coordinates'][0]:  # 假设每个几何对象只有一个外环
            x = coord[0]
            y = coord[1]

            # 更新最小和最大x值
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x

            # 更新最小和最大y值
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

    # 构建极端坐标
    extreme_coords = {
        'min_x_min_y': [min_x, min_y],
        'min_x_max_y': [min_x, max_y],
        'max_x_min_y': [max_x, min_y],
        'max_x_max_y': [max_x, max_y]
    }

    return extreme_coords


def process_control_lines(design, prefixes, output_file, excluded_qubits=[]):
    # 获取所有控制线组件的名称
    delete_list = []
    all_components = {getattr(comp, 'name', None) for comp in design.components.values()}
    for i in excluded_qubits:
        pattern = rf'(?<!\d){i}(?!\d)'
        delete_list.append('flux_line' + str(i))
        for name in design.components:
            if re.search(pattern, name) and name.startswith('flux_line_c'):
                delete_list.append(name)

    # 过滤出以指定前缀开头的控制线组件
    # control_lines = [name for name in all_components if any(name.startswith(prefix) for prefix in prefixes)]
    control_lines = []
    for comp in design.components.values():
        for start_name in prefixes:
            if comp.name.startswith(start_name) and comp.name not in delete_list:
                control_lines.append(comp.name)

    # 处理每个控制线组件
    with open(output_file, 'w') as f:
        for line_name in control_lines:
            # 获取几何字典
            poly_geometry_dict = get_geometry_dict(design, name=line_name)

            # 将几何对象转换为字典
            geometry_dict = {key: mapping(value) for key, value in poly_geometry_dict.items()}

            # 提取极端坐标
            extreme_coords = extract_extreme_coordinates_control_lines(geometry_dict)

            # 构建矩形的四个顶点坐标
            rect_vertices = [
                extreme_coords['min_x_min_y'],
                extreme_coords['min_x_max_y'],
                extreme_coords['max_x_max_y'],
                extreme_coords['max_x_min_y']
            ]

            # 格式化输出
            rect_vertices_str = ', '.join(f'({x}, {y})' for x, y in rect_vertices)
            output_str = f"{line_name}不可布线矩形区域的顶点坐标为：{rect_vertices_str}"
            print(output_str)  # 打印到控制台
            f.write(output_str + '\n')  # 写入文件


def generate_new_coordinates(x1, y1, x2, y2, cpw_width, cpw_gap):
    # 计算 y 坐标的偏移量
    offset = (cpw_width / 2000) + (cpw_gap / 1000)

    # 生成四个新坐标
    coord1 = (x1, y1 + offset)
    coord2 = (x1, y1 - offset)
    coord3 = (x2, y2 + offset)
    coord4 = (x2, y2 - offset)

    return [coord1, coord2, coord3, coord4]


def control_readout_forbidden_zone(design, excluded_qubits=[],output_file1='control_line_forbidden_zone.txt',
                                   output_file2='readout_line_forbidden_zone.txt'):
    folder_name = 'data'
    prefixes = ['flux_line']
    all_points_readout = []
    output_file1 = folder_name + '/' + output_file1
    output_file2 = folder_name + '/' + output_file2

    if not os.path.exists(folder_name):
        # Create the folder if it does not exist
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created.")

    # 处理所有控制线
    process_control_lines(design, prefixes, output_file1,excluded_qubits)

    for component_name, component in design.components.items():
        if component_name.startswith('readout_line') and not component_name.endswith('left') and not component_name.endswith('right'):
            # 获取起始引脚和结束引脚的组件名称和引脚名称
            start_component = component.options['pin_inputs']['start_pin']['component']
            end_component = component.options['pin_inputs']['end_pin']['component']

            # 获取起始引脚的坐标
            start_pin_options = design.components[start_component].parse_options()
            start_pin_x = start_pin_options.pos_x  # 起始引脚的x坐标存储在pos_x中
            start_pin_y = start_pin_options.pos_y  # 起始引脚的y坐标存储在pos_y中

            # 获取结束引脚的坐标
            end_pin_options = design.components[end_component].parse_options()
            end_pin_x = end_pin_options.pos_x
            end_pin_y = end_pin_options.pos_y

            # 将起始和结束引脚的坐标信息作为一个元组追加到列表中
            all_points_readout.append((component.name, start_pin_x, start_pin_y, end_pin_x, end_pin_y))

    # *********************************************************************************
    # 导出读出线起始部分占用的不可布线区域坐标

    # 假设 design.variables.cpw_width 和 design.variables.cpw_gap 已经定义
    cpw_width_str = design.variables.cpw_width  # 例如 '10 um'
    cpw_gap_str = design.variables.cpw_gap  # 例如 '7 um'

    # 从字符串中提取数值部分并转换为浮点数
    cpw_width = float(cpw_width_str.split()[0])  # 提取数值部分并转换为浮点数
    cpw_gap = float(cpw_gap_str.split()[0])  # 提取数值部分并转换为浮点数

    # 处理每个读出线
    with open(output_file2, 'w') as f:
        for line_name, x1, y1, x2, y2 in all_points_readout:  # all_points_readout在上一部分生成读取线端点坐标时候得到
            # 生成新坐标
            new_coords = generate_new_coordinates(x1, y1, x2, y2, cpw_width, cpw_gap)

            # 格式化输出
            new_coords_str = ', '.join(f'({x}, {y})' for x, y in new_coords)
            output_str = f"{line_name}不可布线矩形区域的顶点坐标为：{new_coords_str}"
            print(output_str)  # 打印到控制台
            f.write(output_str + '\n')  # 写入文件


def forbidden_zone_and_pins(design, row, column,excluded_qubits_path='', add_connector=False):
    if excluded_qubits_path == '':
        excluded_qubits = []
    else:
        with open(excluded_qubits_path, 'r') as file:
            excluded_qubits = [int(line.strip()) for line in file]
    launchpad_coord(design)
    qubit_forbidden_zone(design, row, column,excluded_qubits=excluded_qubits)
    resonator_forbidden_zone(design, row, column)
    control_readout_line_coord(design,excluded_qubits=excluded_qubits)
    control_readout_forbidden_zone(design,excluded_qubits=excluded_qubits)
    if add_connector:
        start_connector_coord(design)
        end_connector_coord(design)



def plot_all_forbidden_zones(design, row, column, excluded_qubits=[], figsize=(24, 24)):
    """Plot all forbidden (no-routing) zones: qubits, resonators, control lines, readout lines."""
    total_qubit_num = row * column
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    drawn_labels = set()
    skipped = []

    def _add_rect(vertices, color, label):
        verts = [(v[0], v[1]) for v in vertices]
        show_label = label if label not in drawn_labels else None
        patch = MplPolygon(verts, closed=True, facecolor=color, edgecolor='black',
                           alpha=0.3, linewidth=0.5, label=show_label)
        ax.add_patch(patch)
        drawn_labels.add(label)

    # ---- 1. Qubit & stop-sign forbidden zones ----
    try:
        qubit_zones = extract_extreme_coordinates_qbits(
            design, row, column, excluded_qubits=excluded_qubits)
        for name, coords_list in qubit_zones.items():
            for coords in coords_list:
                if name.startswith('Q'):
                    _add_rect(coords, '#4169E1', 'Qubit')
                elif name.startswith('rectangle'):
                    _add_rect(coords, '#808080', 'Stop sign')
    except Exception as e:
        print(f'[WARNING] Failed to plot qubit forbidden zones: {e}')

    # ---- 2. Resonator forbidden zones ----
    for i in range(1, int(total_qubit_num) + 1):
        resonator = f'R{i}'
        if resonator not in design.components:
            continue
        try:
            rects = _compute_resonator_forbidden_rects(design, resonator)
            for rect in rects:
                _add_rect(rect, '#DC143C', 'Resonator')
        except Exception as e:
            skipped.append(resonator)
            print(f'[WARNING] Skipped {resonator}: {e}')

    # ---- 3. Control line (flux line) forbidden zones ----
    fl_delete_list = []
    for i in excluded_qubits:
        pattern = rf'(?<!\d){i}(?!\d)'
        fl_delete_list.append('flux_line' + str(i))
        for name in design.components:
            if re.search(pattern, name) and name.startswith('flux_line_c'):
                fl_delete_list.append(name)
    for comp in design.components.values():
        if comp.name.startswith('flux_line') and comp.name not in fl_delete_list:
            try:
                poly_gd = get_geometry_dict(design, name=comp.name)
                gd = {key: mapping(value) for key, value in poly_gd.items()}
                ec = extract_extreme_coordinates_control_lines(gd)
                _add_rect([ec['min_x_min_y'], ec['min_x_max_y'],
                            ec['max_x_max_y'], ec['max_x_min_y']], '#2E8B57', 'Control line')
            except Exception as e:
                skipped.append(comp.name)
                print(f'[WARNING] Skipped {comp.name}: {e}')

    # ---- 4. Readout line forbidden zones ----
    try:
        cpw_width = float(design.variables.cpw_width.split()[0])
        cpw_gap = float(design.variables.cpw_gap.split()[0])
        for comp_name, comp in design.components.items():
            if (comp_name.startswith('readout_line')
                    and not comp_name.endswith('left')
                    and not comp_name.endswith('right')):
                try:
                    sc = comp.options['pin_inputs']['start_pin']['component']
                    ec_name = comp.options['pin_inputs']['end_pin']['component']
                    sp = design.components[sc].parse_options()
                    ep = design.components[ec_name].parse_options()
                    new_coords = generate_new_coordinates(
                        sp.pos_x, sp.pos_y, ep.pos_x, ep.pos_y, cpw_width, cpw_gap)
                    _add_rect(new_coords, '#FF8C00', 'Readout line')
                except Exception as e:
                    skipped.append(comp_name)
                    print(f'[WARNING] Skipped {comp_name}: {e}')
    except Exception as e:
        print(f'[WARNING] Failed to plot readout line forbidden zones: {e}')

    if skipped:
        print(f'[INFO] {len(skipped)} component(s) skipped due to errors: {skipped}')

    ax.set_aspect('equal')
    ax.autoscale()
    ax.legend(loc='upper right', fontsize=12)
    ax.set_title('All Forbidden Zones', fontsize=16)
    ax.set_xlabel('X (mm)', fontsize=12)
    ax.set_ylabel('Y (mm)', fontsize=12)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    return fig, ax


def components_pin(design,name):
    pin = list(design.components[name].pins.keys())[0]
    return pin


# def preprocess_file_simple(input_filename, output_filename):
#     """
#     简单的文件预处理函数
#     """
#     with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
#         for line in infile:
#             # 替换 readout_line_x_left -> tl_lx
#             line = re.sub(r'readout_line_(\d+)_left', r'tl_l\1', line)
#
#             # 替换 readout_line_x_right -> tl_rx
#             line = re.sub(r'readout_line_(\d+)_right', r'tl_r\1', line)
#
#             outfile.write(line)
#
#
# def parse_and_route(filename, design, gui):
#     with open(filename, 'r') as file:
#         for line in file:
#             line = line.strip()
#             if not line:
#                 continue
#
#             # 解析行
#             pattern = r'^([^:]+):([^,]+),\((.*)\)$'
#             match = re.match(pattern, line)
#
#             if match:
#                 start_component = match.group(1)
#                 end_component = match.group(2)
#
#                 # 处理坐标
#                 coords_str = match.group(3)
#                 anchors = OrderedDict()
#                 coord_pairs = coords_str.split(') (')
#
#                 for i, pair in enumerate(coord_pairs):
#                     pair = pair.replace('(', '').replace(')', '').strip()
#                     if pair:
#                         x, y = pair.split(', ')
#                         anchors[i] = np.array([x, y])
#                 # return start_component,end_component,anchors
#                 # 创建路由选项
#                 options = {'pin_inputs':
#                                {'start_pin': {'component': start_component, 'pin': components_pin(design, start_component)},
#                                 'end_pin': {'component': end_component, 'pin': components_pin(design, end_component)}},
#                            'step_size': '0.1mm',
#                            'anchors': anchors,
#                            'fillet': '1um'
#                            }
#
#                 # 执行路由
#                 RoutePathfinder(design, 'line_' + start_component + '_' + end_component, options)
#     gui.rebuild()
#     gui.autoscale()

# def parse_and_route(filename, design, gui):
#     with open(filename, 'r') as file:
#         for line in file:
#             line = line.strip()
#             if not line:
#                 continue
#
#             # 解析行
#             pattern = r'^([^:]+):([^,]+),\((.*)\)$'
#             match = re.match(pattern, line)
#
#             if match:
#                 start_component = match.group(1)
#                 end_component = match.group(2)
#
#                 # 处理坐标
#                 coords_str = match.group(3)
#                 anchors = OrderedDict()
#                 coord_pairs = coords_str.split(') (')
#
#                 for i, pair in enumerate(coord_pairs):
#                     pair = pair.replace('(', '').replace(')', '').strip()
#                     if pair:
#                         x, y = pair.split(', ')
#                         anchors[i] = np.array([x, y])
#                 # return start_component,end_component,anchors
#                 # 创建路由选项
#                 options = {'pin_inputs':
#                                {'start_pin': {'component': start_component, 'pin': components_pin(design, start_component)},
#                                 'end_pin': {'component': end_component, 'pin': components_pin(design, end_component)}},
#                            'step_size': '0.1mm',
#                            'anchors': anchors,
#                            'fillet': '30um'
#                            }
#
#                 # 执行路由
#                 RoutePathfinder(design, 'line_' + start_component + '_' + end_component, options)
#     gui.rebuild()
#     gui.autoscale()


def relative_direction(vector1, vector2):
    """
    Returns:
    -1 if vector2 is clockwise from vector1
     0 if vectors are colinear
     1 if vector2 is counter-clockwise from vector1
    """
    cross_product = np.cross(vector1, vector2)
    if cross_product > 0:
        return 'L'  # Counter-clockwise
    elif cross_product < 0:
        return 'R'  # Clockwise
    else:
        return 0  # Colinear


def components_pin(design,name):
    pin = list(design.components[name].pins.keys())[0]
    return pin


def parse_and_route(filename, design, gui, fillet=30):
    with open(filename, 'r') as file:
        total_lines = sum(1 for line in file)  # 先计算总行数
        file.seek(0)  # 重新定位文件指针到文件开头
        for i, line in enumerate(file, 1):
            line = line.strip()
            if not line:
                continue
            # print(line)
            # 计算并输出进度
            progress = (i / total_lines) * 100
            print(f"进度: {progress:.2f}% ({i}/{total_lines} lines)", end="\r")

            # 解析行
            pattern = r'^([^:]+):([^,]+),\((.*)\)$'
            match = re.match(pattern, line)

            if match:
                start_component = match.group(1)
                end_component = match.group(2)

                # 处理坐标
                coords_str = match.group(3)
                anchors = OrderedDict()
                anchors[0] = design.components[start_component].pins[components_pin(design,start_component)]['middle']
                coord_pairs = coords_str.split(') (')

                for i, pair in enumerate(coord_pairs):
                    pair = pair.replace('(', '').replace(')', '').strip()
                    if pair:
                        x, y = pair.split(', ')
                        anchors[i + 1] = np.array([float(x), float(y)])

                # return start_component,end_component,anchors
                #             coord = design.components[start_component].pins[components_pin(start_component)]['middle']
                start_straight = np.linalg.norm(anchors[1] - anchors[0])
                temp_anchors = OrderedDict()
                for i in range(len(anchors) - 1):
                    temp_anchors[i] = anchors[i + 1] - anchors[i]
                temp_anchors[len(anchors) - 1] = design.components[end_component].pins[components_pin(design,end_component)][
                                                     'middle'] - anchors[len(anchors) - 1]

                jogsS = OrderedDict()
                for i in range(len(temp_anchors) - 2):
                    jogsS[i] = [relative_direction(temp_anchors[i], temp_anchors[i + 1]),
                                str(np.linalg.norm(temp_anchors[i + 1])) + 'mm']
                jogsS[len(temp_anchors) - 2] = [
                    relative_direction(temp_anchors[len(anchors) - 2], temp_anchors[len(anchors) - 1]), '0um']
                # print(jogsS)
                # 创建路由选项
                if start_component.startswith('readout'):
                    options = {'pin_inputs':
                                   {'start_pin': {'component': start_component,
                                                  'pin': components_pin(design, start_component)},
                                    'end_pin': {'component': end_component,
                                                'pin': components_pin(design, end_component)}},
                               'lead': {'start_straight': str(start_straight) + 'mm', 'start_jogged_extension': jogsS,
                                        'end_straight': '120um'},
                               'trace_width': '8um',
                               'trace_gap': '4um',
                               'fillet': str(fillet) + 'um',
                               'advanced': Dict(avoid_collision='true')

                               }
                else:
                    options = {'pin_inputs':
                                   {'start_pin': {'component': start_component, 'pin': components_pin(design,start_component)},
                                    'end_pin': {'component': end_component, 'pin': components_pin(design,end_component)}},
                               'lead': {'start_straight': str(start_straight) + 'mm', 'start_jogged_extension': jogsS,
                                        'end_straight': '120um'},
                               # 'step_size': '0.2mm',
                               # 'anchors': anchors,
                               'fillet': str(fillet) + 'um',
                               'advanced': Dict(avoid_collision='true')

                               }
                # print(start_straight, jogsS)

                # 执行路由
                RoutePathfinder(design, 'line_' + start_component + '_' + end_component, options)

    # return start_straight,jogsS
    # gui.rebuild()
    # gui.autoscale()


def delete_all_lines(design, gui):
    for component_name, component in design.components.items():
        if component_name.startswith('line'):
            design.delete_component(component_name)
    # gui.rebuild()
    # gui.autoscale()
