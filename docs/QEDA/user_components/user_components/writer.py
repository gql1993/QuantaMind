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
from qiskit_metal.qlibrary.user_components.writer import *
from qiskit_metal.qlibrary.user_components.cell import *
from qiskit_metal.qlibrary.user_components.chip_information import *
from qiskit_metal.qlibrary.user_components.layout import *
import klayout.db as db
import matplotlib.pyplot as plt
import re
import csv


def writer_planar(design, jj_path: str, chip_name='main', cheese_size='4um', negative_mask=None, cheese_space='50um',
                  edge_nocheese='500um', no_cheese_buffer='200um', cheese_view=None):
    """
    定义将设计写入gds版图的写入器参数选项，参数定义参考qiskit-metal里的 gds render
    """
    if cheese_view is None:
        cheese_view = {1: False, }
    if negative_mask is None:
        negative_mask = []
    a_gds = design.renderers.gds
    a_gds.options['path_filename'] = jj_path
    a_gds.options['short_segments_to_not_fillet'] = 'True'
    a_gds.options['fabricate'] = 'True'
    a_gds.options['max_points'] = '1000'
    scale_fillet = 1.0
    a_gds.options['check_short_segments_by_scaling_fillet'] = scale_fillet
    a_gds.options.negative_mask = {chip_name: negative_mask}
    a_gds.options.cheese.shape = '0'
    a_gds.options.cheese.cheese_0_x = cheese_size
    a_gds.options.cheese.cheese_0_y = cheese_size
    a_gds.options.cheese.delta_x = cheese_space
    a_gds.options.cheese.delta_y = cheese_space
    a_gds.options.cheese.edge_nocheese = edge_nocheese
    a_gds.options.no_cheese.buffer = no_cheese_buffer
    # a_gds.options.cheese.cheese_1_radius = '25 um'
    a_gds.options.cheese.view_in_file = {chip_name:cheese_view, }
    a_gds.options.no_cheese.view_in_file = {chip_name: cheese_view, }
    return a_gds


def layout_generation(design_list, template_path, output_path, jj_path, output_name='design_combined',
                      gds_cell_list=['TOP_main_1'], row=4, column=4, delta_x=6000, delta_y=6000, rotation=45):
    template = gdspy.GdsLibrary(infile=template_path)
    for i in range(row*column):
        layout = db.Layout()
        cheese_view = {1: False, 2: False, 3: False, 4: False, }
        # 设置输出文件选项
        a_gds = writer_planar(design_list[i], jj_path, negative_mask=[1, 2, 3], cheese_view=cheese_view)
        # a_gds = writer_planar(design_list[i],jj_path,negative_mask=[1,2])
        a_gds.export_to_gds(output_path+'design_temp'+str(i)+'.gds')
        print(f'gds{i} is finished')
        layout.read(output_path+'design_temp'+str(i)+'.gds')
        db.SaveLayoutOptions.gds2_user_units=0.001
        layout.write(output_path+'design_temp'+str(i)+'.gds')
        gds_cell_list = gds_cell_list
        gds = gdspy.GdsLibrary(infile=output_path+'design_temp'+str(i)+'.gds')
        cell_add(gds, template, delta_x*(1-column)/2+(i % column)*delta_x, delta_y*(row-1)/2-int(i/row)*delta_y,
                 rotation=rotation, gds_cell_list=gds_cell_list)
    template.write_gds(output_path+output_name+'.gds')
    print("GDS files combined successfully generated")


def get_position_dict(design):
    components_dict = {}
    path = 'position.json'
    for component_name, component in design.components.items():
        if component_name.startswith('Q') or component_name.startswith('long_range'):
            # Get the component's parameters
            params = {'pos_x': design.components[component_name].parse_options().get('pos_x'),
                      'pos_y': design.components[component_name].parse_options().get('pos_y')
                      }
            components_dict[component_name] = params
    return components_dict


def draw_qubit_layout(data):
    # 创建绘图器
    plotter = QuantumChipPlotter(data)

    # 打印数据摘要和名称映射
    plotter.print_data_summary()
    plotter.print_coupler_mapping()

    # 绘制图形（使用简化名称）
    print("\n正在绘制图形（使用简化耦合器名称）...")

    fig, ax = plotter.draw_chip_layout(
        figsize=(16, 12),
        dpi=100,
        show_connections=True,
        show_labels=True,
        qubit_size=350,
        coupler_size=(0.5, 0.25),
        simplified_coupler_names=True  # 使用简化名称
    )

    # 显示图形
    plt.show()

    # 保存图形和数据
    save_option = input("\n是否保存图形和数据? (y/n): ").strip().lower()
    if save_option == 'y':
        # 保存图形（使用简化名称）
        plotter.save_plot('quantum_chip_layout_simplified.png', simplified_names=True)

        # 保存图形（使用原始名称，用于对比）
        save_full_names = input("是否也保存使用完整名称的版本? (y/n): ").strip().lower()
        if save_full_names == 'y':
            fig_full, ax_full = plotter.draw_chip_layout(
                figsize=(16, 12),
                simplified_coupler_names=False  # 不使用简化名称
            )
            fig_full.savefig('quantum_chip_layout_full_names.png', dpi=300,
                             bbox_inches='tight', facecolor='white')
            plt.close(fig_full)
            print("完整名称版本已保存为: quantum_chip_layout_full_names.png")

        # # 保存连接数据
        # plotter.save_connection_data('coupler_connections.csv', include_simplified_names=True)
        # print("保存完成!")

    print("\n程序结束")


def pin_information_writer(route_file_path):
    # 读取文件内容
    with open(route_file_path, 'r') as f:
        lines = f.readlines()

    # 第一步：提取引脚连接信息
    connections = []
    for line in lines:
        line = line.strip()
        if line:
            # 分割引脚连接信息
            if ':' in line:
                parts = line.split(':')
                left_part = parts[0]
                right_part = parts[1].split(',')[0]  # 只取逗号前的引脚名称

                # 提取右侧引脚的数字部分
                pin_match = re.search(r'launch_zline(\d+)', right_part)
                if pin_match:
                    internal_pin = pin_match.group(1)
                    connections.append((left_part, internal_pin))

    processed_connections = []
    for left_pin, internal_pin in connections:
        renamed_left = rename_left_pin(left_pin)
        external_pin = map_internal_to_external(internal_pin)
        processed_connections.append((external_pin, renamed_left))

    # 按照外部引脚号排序
    processed_connections.sort(key=lambda x: x[0])

    # 写入CSV文件
    with open('pin_mapping.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['chip_port', 'line_name'])
        for external_pin, line_name in processed_connections:
            writer.writerow([external_pin, line_name])

    print(f"处理完成！共找到 {len(processed_connections)} 个引脚连接")
    print("CSV文件已生成: pin_mapping.csv")
    print("\n前10个连接示例:")
    for i in range(min(10, len(processed_connections))):
        print(f"  外部引脚{processed_connections[i][0]:3d}: {processed_connections[i][1]}")

    print("\n注：外部引脚映射函数需要根据实际芯片布局进行调整")
    print("当前的map_internal_to_external函数只是示例，需要完善实际的映射逻辑")