# -*- coding: utf-8 -*-
import math

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
import gdspy


def cell_add(gds, template, delta_x, delta_y, rotation=0, template_cell_name='TOP',
             gds_cell_list=['TOP_main_1', 'TOP_main_2', 'TOP_main_3']):
    for cell_name in gds_cell_list:
        cell = gds.cells[cell_name]
        for layer, polygon in cell.get_polygons(by_spec=True).items():
            polygon_set = gdspy.PolygonSet(polygon, layer[0], layer[1])
            polygon_set.rotate(math.radians(rotation))
            polygon_set.translate(delta_x, delta_y)
            template.cells[template_cell_name].add(polygon_set)
