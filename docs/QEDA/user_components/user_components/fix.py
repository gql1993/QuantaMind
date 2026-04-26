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
import pya


def check_and_fix_geometry(gds_path, output_path):
    """
    检查并自动修复几何问题
    """
    layout = pya.Layout()
    layout.read(gds_path)

    print("开始几何检查和修复...")

    for cell in layout.each_cell():
        print(f"处理单元格: {cell.name}")

        for layer_index in layout.layer_indexes():
            shapes = cell.shapes(layer_index)
            if shapes.size() == 0:
                continue

            original_region = pya.Region(shapes)
            original_count = original_region.size()

            # 应用修复操作
            fixed_region = original_region.merged()  # 合并重叠和相交的多边形
            fixed_region = fixed_region.smoothed(1)  # 轻微平滑

            # 移除过小的多边形
            cleaned_region = pya.Region()
            for polygon in fixed_region.each():
                area = polygon.area() * (layout.dbu ** 2)
                if area >= 1e-8:  # 保留面积大于 1e-8 的多边形
                    cleaned_region.insert(polygon)

            final_count = cleaned_region.size()

            # 如果图形数量有变化，更新层
            if final_count != original_count:
                print(f"  层 {layout.get_info(layer_index)}: {original_count} -> {final_count} 个多边形")
                shapes.clear()
                shapes.insert(cleaned_region)

    # 保存修复后的文件
    layout.write(output_path)
    print(f"修复完成，保存到: {output_path}")