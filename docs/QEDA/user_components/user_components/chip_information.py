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

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Qubit:
    """比特数据类"""
    name: str
    x: float
    y: float


@dataclass
class Coupler:
    """耦合器数据类"""
    name: str
    x: float
    y: float
    qubits: List[str] = None


class QuantumChipPlotter:
    """
    量子芯片比特排布图绘制器

    参数:
    - data: 从JSON加载的数据字典
    """

    def __init__(self, data: Dict):
        self.data = data
        self.qubits = self._extract_qubits()
        self.couplers = self._extract_couplers()
        self.qubit_dict = {q.name: (q.x, q.y) for q in self.qubits}

    def _extract_qubits(self) -> List[Qubit]:
        """从数据中提取比特信息"""
        qubits = []
        for key, value in self.data.items():
            # 如果键以'Q'开头且包含'pos_x'和'pos_y'，则是比特
            if key.startswith('Q') and 'pos_x' in value and 'pos_y' in value:
                qubit = Qubit(
                    name=key,
                    x=value['pos_x'],
                    y=value['pos_y']
                )
                qubits.append(qubit)
        return qubits

    def _extract_couplers(self) -> List[Coupler]:
        """从数据中提取耦合器信息"""
        couplers = []
        for key, value in self.data.items():
            # 如果键包含'tc'（可调耦合器）且包含'pos_x'和'pos_y'，则是耦合器
            if 'tc' in key.lower() and 'pos_x' in value and 'pos_y' in value:
                # 从名称中提取连接的比特
                connected_qubits = self.extract_qubits_from_coupler_name(key)

                coupler = Coupler(
                    name=key,
                    x=value['pos_x'],
                    y=value['pos_y'],
                    qubits=connected_qubits
                )
                couplers.append(coupler)
        return couplers

    def extract_qubits_from_coupler_name(self, coupler_name: str) -> List[str]:
        """
        从耦合器名称中提取连接的比特
        """
        # 使用正则表达式提取所有数字
        numbers = re.findall(r'\d+', coupler_name)

        if len(numbers) >= 2:
            # 提取前两个数字作为比特编号
            qubit_nums = numbers[:2]
            return [f'Q{num}' for num in qubit_nums]
        else:
            # 尝试其他模式
            patterns = [
                r'[Qq](\d+)[_-][Qq](\d+)',  # Q1_Q2 或 q1-q2
                r'(\d+)[_-](\d+)',  # 1-2 或 1_2
            ]

            for pattern in patterns:
                match = re.search(pattern, coupler_name)
                if match:
                    return [f'Q{match.group(1)}', f'Q{match.group(2)}']

            # 如果都找不到，返回空列表
            return []

    def get_simplified_coupler_name(self, coupler_name: str) -> str:
        """
        获取简化的耦合器显示名称

        对于long_range_tc，只显示'tc'
        对于其他耦合器，显示简短名称
        """
        # 转换为小写以进行匹配
        name_lower = coupler_name.lower()

        # 如果是long_range_tc，只显示'tc'
        if 'long_range_tc' in name_lower:
            return 'TC'
        # 如果是nearest_tc，显示'TC'
        elif 'nearest_tc' in name_lower:
            return 'TC'
        # 如果是其他类型的tc，显示'TC'
        elif 'tc' in name_lower:
            return 'TC'
        # 如果是coupler，显示'C'
        elif 'coupler' in name_lower:
            return 'C'
        # 其他情况，显示原名称的前4个字符
        else:
            return coupler_name[:4] + '...' if len(coupler_name) > 4 else coupler_name

    def draw_chip_layout(self, figsize=(16, 12), dpi=100,
                         show_connections=True, show_labels=True,
                         qubit_size=300, coupler_size=(0.6, 0.3),
                         simplified_coupler_names=True):
        """
        绘制芯片布局图

        参数:
        - figsize: 图形大小
        - dpi: 分辨率
        - show_connections: 是否显示连接线
        - show_labels: 是否显示标签
        - qubit_size: 比特点的大小
        - coupler_size: 耦合器矩形的尺寸 (width, height)
        - simplified_coupler_names: 是否使用简化的耦合器名称
        """
        # 创建图形
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # 设置背景和网格
        ax.set_facecolor('#f0f5ff')
        ax.grid(True, linestyle='--', alpha=0.3, linewidth=0.5, color='#cccccc')

        # 绘制比特
        self._draw_qubits(ax, qubit_size, show_labels)

        # 绘制可调耦合器
        if self.couplers:
            if show_connections:
                self._draw_all_coupler_connections(ax)

            self._draw_couplers(ax, coupler_size, show_labels, simplified_coupler_names)

        # 设置坐标轴
        self._set_axes_limits(ax, margin=2.0)

        # 设置标签和标题
        self._set_labels_and_title(ax)

        # 添加图例
        self._add_legend(ax, simplified_coupler_names)

        # 添加统计信息
        self._add_stats_info(ax)

        # 添加连接信息说明
        if self.couplers and show_labels:
            self._add_connection_info(ax)

        plt.tight_layout()
        return fig, ax

    def _draw_qubits(self, ax, qubit_size=300, show_labels=True):
        """绘制比特"""
        if not self.qubits:
            return

        # 提取坐标
        qubit_x = [q.x for q in self.qubits]
        qubit_y = [q.y for q in self.qubits]
        qubit_names = [q.name for q in self.qubits]

        # 绘制比特点
        scatter = ax.scatter(qubit_x, qubit_y,
                             s=qubit_size,
                             c='#1e88e5',  # 蓝色系
                             edgecolors='#0d47a1',
                             linewidths=2,
                             marker='o',
                             zorder=10,
                             label='Qubits')

        # 添加比特标签
        if show_labels:
            for qubit in self.qubits:
                # 稍微偏移标签位置以避免覆盖
                offset_x = 0.2
                offset_y = 0.2

                ax.annotate(qubit.name,
                            xy=(qubit.x, qubit.y),
                            xytext=(qubit.x + offset_x, qubit.y + offset_y),
                            fontsize=11,
                            fontweight='bold',
                            color='#0d47a1',
                            bbox=dict(boxstyle="round,pad=0.3",
                                      facecolor='white',
                                      edgecolor='#0d47a1',
                                      alpha=0.9,
                                      linewidth=1.5),
                            zorder=12)

    def _draw_all_coupler_connections(self, ax):
        """绘制所有耦合器的连接线"""
        for coupler in self.couplers:
            self._draw_coupler_connection(ax, coupler)

    def _draw_coupler_connection(self, ax, coupler):
        """绘制单个耦合器的连接线"""
        if not coupler.qubits or len(coupler.qubits) < 2:
            return

        qubit1_name, qubit2_name = coupler.qubits[0], coupler.qubits[1]

        if qubit1_name in self.qubit_dict and qubit2_name in self.qubit_dict:
            x1, y1 = self.qubit_dict[qubit1_name]
            x2, y2 = self.qubit_dict[qubit2_name]

            # 计算中点
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2

            # 绘制连接线
            linewidth = 1.5
            color = '#ff9800'  # 橙色

            # 如果是长程连接，用不同的样式
            if 'long_range' in coupler.name.lower():
                color = '#e91e63'  # 粉色
                linewidth = 2.0

            # 绘制直线连接
            ax.plot([x1, x2], [y1, y2],
                    linestyle='-',
                    color=color,
                    linewidth=linewidth,
                    alpha=0.7,
                    zorder=1)

    def _draw_couplers(self, ax, coupler_size=(0.6, 0.3), show_labels=True, simplified_names=True):
        """绘制所有耦合器"""
        rect_width, rect_height = coupler_size

        for coupler in self.couplers:
            # 绘制耦合器矩形
            rectangle = patches.Rectangle((coupler.x - rect_width / 2, coupler.y - rect_height / 2),
                                          rect_width, rect_height,
                                          linewidth=2,
                                          edgecolor='#d32f2f',  # 红色边框
                                          facecolor='#ffcdd2',  # 浅红色填充
                                          alpha=0.9,
                                          zorder=5)
            ax.add_patch(rectangle)

            # 添加耦合器标签
            if show_labels:
                # 获取显示名称
                if simplified_names:
                    display_name = self.get_simplified_coupler_name(coupler.name)
                else:
                    display_name = coupler.name
                    # 如果名称太长，简化显示
                    if len(display_name) > 15:
                        if coupler.qubits and len(coupler.qubits) >= 2:
                            q1_num = coupler.qubits[0][1:] if coupler.qubits[0].startswith('Q') else coupler.qubits[0]
                            q2_num = coupler.qubits[1][1:] if coupler.qubits[1].startswith('Q') else coupler.qubits[1]
                            display_name = f"TC_{q1_num}_{q2_num}"
                        else:
                            display_name = coupler.name[:12] + "..."

                # 确定标签位置
                label_offset = -0.1  # 增加偏移量，避免与连接线重叠

                # 为TC标签添加背景，使其更清晰可见
                bbox_props = dict(
                    boxstyle="round,pad=0.3",
                    facecolor='white',
                    edgecolor='#d32f2f',
                    alpha=0.9,
                    linewidth=1.5
                )

                ax.annotate(display_name,
                            xy=(coupler.x, coupler.y),
                            xytext=(coupler.x, coupler.y - label_offset),
                            fontsize=5,  # 增大字体
                            fontweight='bold',
                            color='#d32f2f',
                            ha='center',
                            va='top',
                            bbox=bbox_props,
                            zorder=12)

    def _set_axes_limits(self, ax, margin=1.5):
        """设置坐标轴范围"""
        if not self.qubits:
            return

        qubit_x = [q.x for q in self.qubits]
        qubit_y = [q.y for q in self.qubits]

        x_min, x_max = min(qubit_x) - margin, max(qubit_x) + margin
        y_min, y_max = min(qubit_y) - margin, max(qubit_y) + margin

        # 如果耦合器在更远的位置，调整坐标轴范围
        if self.couplers:
            coupler_x = [c.x for c in self.couplers]
            coupler_y = [c.y for c in self.couplers]

            x_min = min(x_min, min(coupler_x) - margin)
            x_max = max(x_max, max(coupler_x) + margin)
            y_min = min(y_min, min(coupler_y) - margin)
            y_max = max(y_max, max(coupler_y) + margin)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        # 设置纵横比为相等，确保图形不扭曲
        ax.set_aspect('equal', adjustable='box')

    def _set_labels_and_title(self, ax):
        """设置标签和标题"""
        ax.set_xlabel('X Position (mm)', fontsize=12)
        ax.set_ylabel('Y Position (mm)', fontsize=12)
        ax.set_title('Quantum Chip Qubit Layout', fontsize=16, fontweight='bold', pad=20)

    def _add_legend(self, ax, simplified_names=True):
        """添加图例"""
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D

        # 根据是否使用简化名称来调整图例标签
        if simplified_names:
            coupler_label = 'TC (Tunable Coupler)'
        else:
            coupler_label = 'Tunable Coupler'

        legend_elements = [
            Patch(facecolor='#1e88e5', edgecolor='#0d47a1', label='Qubit'),
            Patch(facecolor='#ffcdd2', edgecolor='#d32f2f', label=coupler_label),
            # Line2D([0], [0], color='#ff9800', linestyle='-', linewidth=2, label='Nearest Coupling'),
            Line2D([0], [0], color='#e91e63', linestyle='-', linewidth=2, label='Long-range Coupling')
        ]

        ax.legend(handles=legend_elements,
                  loc='upper right',
                  fontsize=10,
                  framealpha=0.9,
                  fancybox=True,
                  shadow=True,
                  borderpad=1)

    def _add_stats_info(self, ax):
        """添加统计信息"""
        total_connections = sum(1 for c in self.couplers if c.qubits and len(c.qubits) >= 2)
        long_range_count = sum(1 for c in self.couplers if 'long_range' in c.name.lower())
        nearest_count = len(self.couplers) - long_range_count

        info_text = (
            f'Total Qubits: {len(self.qubits)}\n'
            f'Total Couplers: {len(self.couplers)}\n'
            f'  - Nearest: {nearest_count}\n'
            f'  - Long-range: {long_range_count}\n'
            f'Active Connections: {total_connections}'
        )

        ax.text(0.02, 0.98, info_text,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.5",
                          facecolor='white',
                          edgecolor='#607d8b',
                          alpha=0.9,
                          linewidth=1.5))

    def _add_connection_info(self, ax):
        """添加连接信息说明"""
        if not self.couplers:
            return

        # 显示前几个耦合器的连接信息
        info_lines = ["Coupler Connections (sample):"]

        # 显示几个不同类型的耦合器作为示例
        sample_couplers = []

        # 先找长程耦合器
        for coupler in self.couplers:
            if 'long_range' in coupler.name.lower():
                sample_couplers.append(coupler)
                if len(sample_couplers) >= 3:
                    break

        # 如果不够，再添加其他耦合器
        if len(sample_couplers) < 3:
            for coupler in self.couplers:
                if coupler not in sample_couplers:
                    sample_couplers.append(coupler)
                    if len(sample_couplers) >= 3:
                        break

        for coupler in sample_couplers:
            if coupler.qubits and len(coupler.qubits) >= 2:
                # 显示简化名称和连接关系
                simple_name = self.get_simplified_coupler_name(coupler.name)
                info_lines.append(f"{simple_name}: {coupler.qubits[0]}↔{coupler.qubits[1]}")
            else:
                info_lines.append(f"{coupler.name}: Not connected")

        if len(self.couplers) > 3:
            info_lines.append(f"... and {len(self.couplers) - 3} more couplers")

        info_text = "\n".join(info_lines)

        ax.text(0.98, 0.02, info_text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='bottom',
                horizontalalignment='right',
                bbox=dict(boxstyle="round,pad=0.5",
                          facecolor='white',
                          edgecolor='#607d8b',
                          alpha=0.9,
                          linewidth=1.5))

    def print_coupler_mapping(self):
        """打印耦合器名称映射关系（原始名称 -> 简化名称）"""
        print("耦合器名称映射:")
        print("-" * 50)
        for coupler in self.couplers[:10]:  # 只显示前10个
            simple_name = self.get_simplified_coupler_name(coupler.name)
            connection_info = f"{coupler.qubits[0]}↔{coupler.qubits[1]}" if coupler.qubits and len(
                coupler.qubits) >= 2 else "未连接"
            print(f"  {coupler.name:30} -> {simple_name:5} ({connection_info})")

        if len(self.couplers) > 10:
            print(f"  ... 还有 {len(self.couplers) - 10} 个耦合器")
        print("-" * 50)

    def get_coupler_connections(self) -> List[Dict]:
        """获取所有耦合器的连接关系"""
        connections = []
        for coupler in self.couplers:
            if coupler.qubits and len(coupler.qubits) >= 2:
                connections.append({
                    'coupler': coupler.name,
                    'simplified_name': self.get_simplified_coupler_name(coupler.name),
                    'qubit1': coupler.qubits[0],
                    'qubit2': coupler.qubits[1],
                    'x': coupler.x,
                    'y': coupler.y
                })
        return connections

    def print_data_summary(self):
        """打印数据摘要"""
        print("=" * 60)
        print("量子芯片数据摘要")
        print("=" * 60)
        print(f"比特数量: {len(self.qubits)}")
        print(f"耦合器数量: {len(self.couplers)}")

        # 比特坐标范围
        if self.qubits:
            qubit_x = [q.x for q in self.qubits]
            qubit_y = [q.y for q in self.qubits]
            print(f"\n比特坐标范围:")
            print(f"  X: {min(qubit_x):.2f} 到 {max(qubit_x):.2f} mm")
            print(f"  Y: {min(qubit_y):.2f} 到 {max(qubit_y):.2f} mm")

        # 耦合器类型统计
        if self.couplers:
            long_range_count = sum(1 for c in self.couplers if 'long_range' in c.name.lower())
            nearest_count = len(self.couplers) - long_range_count
            print(f"\n耦合器类型:")
            print(f"  最近邻耦合器: {nearest_count}")
            print(f"  长程耦合器: {long_range_count}")

        # 显示前几个比特
        print(f"\n前5个比特:")
        for i, qubit in enumerate(self.qubits[:5]):
            print(f"  {qubit.name}: ({qubit.x:.3f}, {qubit.y:.3f})")

        if self.couplers:
            print(f"\n前5个耦合器 (原始名称 -> 简化名称):")
            for i, coupler in enumerate(self.couplers[:5]):
                simple_name = self.get_simplified_coupler_name(coupler.name)
                connection_info = f"{coupler.qubits[0]}↔{coupler.qubits[1]}" if coupler.qubits else "未连接"
                print(f"  {coupler.name:25} -> {simple_name:5} ({coupler.x:.3f}, {coupler.y:.3f}) - {connection_info}")

        print("=" * 60)

    def save_plot(self, filename='quantum_chip_layout.png', dpi=300, simplified_names=True):
        """保存图形"""
        fig, _ = self.draw_chip_layout(simplified_coupler_names=simplified_names)
        fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"图形已保存为: {filename}")

    def save_connection_data(self, filename='coupler_connections.csv', include_simplified_names=True):
        """保存耦合器连接数据到CSV文件"""
        import csv

        connections = []
        for coupler in self.couplers:
            if coupler.qubits and len(coupler.qubits) >= 2:
                conn_data = {
                    'coupler_name': coupler.name,
                    'qubit1': coupler.qubits[0],
                    'qubit2': coupler.qubits[1],
                    'x_mm': coupler.x,
                    'y_mm': coupler.y
                }

                if include_simplified_names:
                    conn_data['simplified_name'] = self.get_simplified_coupler_name(coupler.name)

                connections.append(conn_data)

        with open(filename, 'w', newline='') as csvfile:
            if include_simplified_names:
                fieldnames = ['coupler_name', 'simplified_name', 'qubit1', 'qubit2', 'x_mm', 'y_mm']
            else:
                fieldnames = ['coupler_name', 'qubit1', 'qubit2', 'x_mm', 'y_mm']

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for conn in connections:
                writer.writerow(conn)

        print(f"连接数据已保存为: {filename}")


def rename_left_pin(original_name):
    # 处理 readout_line_*_right 和 readout_line_*_left
    if original_name.startswith('readout_line_'):
        match = re.search(r'readout_line_(\d+)_(right|left)', original_name)
        if match:
            num = match.group(1).zfill(2)
            direction = match.group(2)
            if direction == 'right':
                return f'bus{num}_out'
            else:
                return f'bus{num}_in'

    # 处理 flux_line_c*_*（连接线）
    elif original_name.startswith('flux_line_c'):
        match = re.search(r'flux_line_c(\d+)_(\d+)', original_name)
        if match:
            num1 = match.group(1).zfill(3)
            num2 = match.group(2).zfill(3)
            return f'c_{num1}_{num2}'

    # 处理 flux_line*（普通flux线）
    elif original_name.startswith('flux_line'):
        # 先检查是否是flux_line_c*格式
        if not original_name.startswith('flux_line_c'):
            match = re.search(r'flux_line(\d+)', original_name)
            if match:
                num = match.group(1).zfill(3)
                return f'xyz_q{num}'

    # 如果都不匹配，返回原名称
    return original_name


def map_internal_to_external(internal_pin_str, region_list=None, pin_num_each_side=42):
    if region_list is None:
        region = [0, 3, 2, 1]
    try:
        pin_int = int(internal_pin_str[1:])
    except ValueError:
        print(f"错误：引脚编号 '{internal_pin_str}' 不是有效的数字")
        return 0

    # 基本规则映射
    # 区域1: 00-041 -> 1-42
    # 区域2: 30-341 -> 43-84
    # 区域3: 20-241 -> 85-126
    # 区域4: 10-141 -> 127-168

    # 区域1：以0开头的引脚
    if internal_pin_str.startswith(str(region[0])):
        if pin_int <= pin_num_each_side - 1:
            return 1 + pin_int  # 011 -> 12, 001 -> 2
        else:
            # 以0开头但大于41，如042？
            return 0

    # 区域2：以3开头的引脚
    elif internal_pin_str.startswith(str(region[1])):
        if pin_int <= pin_num_each_side - 1:
            return pin_num_each_side + pin_int + 1
        else:
            return 0

    # 区域4：以2开头的引脚
    elif internal_pin_str.startswith(str(region[2])):
        if pin_int <= pin_num_each_side - 1:
            return 2 * pin_num_each_side + pin_int + 1
        else:
            return 0

    # 区域3：三位数200-241
    elif internal_pin_str.startswith(str(region[3])):
        if pin_int <= pin_num_each_side - 1:
            return 3 * pin_num_each_side + pin_int + 1
        else:
            return 0
    else:
        # 其他情况
        print(f"警告：引脚 {internal_pin_str} 没有明确的映射规则")
