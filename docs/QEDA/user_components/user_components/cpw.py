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

import numpy as np
from shapely.geometry import LineString, Polygon, CAP_STYLE, JOIN_STYLE
from qiskit_metal.draw import Vector


def bad_fillet_idxs(coords: list,
                    fradius: float,
                    precision: int = 9,
                    isclosed: bool = False) -> list:
    """
    Get list of vertex indices in a linestring (isclosed = False) or polygon (isclosed = True) that cannot be filleted based on
    proximity to neighbors. By default, this list excludes the first and last vertices if the shape is a linestring.

    Args:
        coords (list): Ordered list of tuples of vertex coordinates.
        fradius (float): User-specified fillet radius from QGeometry table.
        precision (int, optional): Digits of precision used for round(). Defaults to 9.
        isclosed (bool, optional): Boolean denoting whether the shape is a linestring or polygon. Defaults to False.

    Returns:
        list: List of indices of vertices too close to their neighbors to be filleted.
    """
    length = len(coords)
    get_dist = Vector.get_distance
    if isclosed:
        return [
            i for i in range(length)
            if min(get_dist(coords[i - 1], coords[i], precision),
                   get_dist(coords[i], coords[(i + 1) %
                                              length], precision)) < 2 * fradius
        ]
    if length < 3:
        return []
    if length == 3:
        return [] if min(get_dist(coords[0], coords[1], precision),
                         get_dist(coords[1], coords[2],
                                  precision)) >= fradius else [1]
    if (get_dist(coords[0], coords[1], precision) < fradius) or (get_dist(
            coords[1], coords[2], precision) < 2 * fradius):
        badlist = [1]
    else:
        badlist = []
    for i in range(2, length - 2):
        if min(get_dist(coords[i - 1], coords[i], precision),
               get_dist(coords[i], coords[i + 1], precision)) < 2 * fradius:
            badlist.append(i)
    if (get_dist(coords[length - 3], coords[length - 2], precision)
        < 2 * fradius) or (get_dist(coords[length - 2], coords[length - 1],
                                    precision) < fradius):
        badlist.append(length - 2)
    return badlist


# --- 辅助函数 2: 改写 _calc_fillet (去除 self) ---
def _calc_fillet_standalone(vertex_start, vertex_corner, vertex_end, radius, points=16):
    """纯数学计算：计算三个点之间的圆角弧线坐标"""
    # 顶点去重
    if np.array_equal(vertex_start, vertex_corner) or np.array_equal(vertex_end, vertex_corner):
        return False

    # 计算向量
    sc_vec = vertex_start - vertex_corner
    ec_vec = vertex_end - vertex_corner
    sc_norm = np.linalg.norm(sc_vec)
    ec_norm = np.linalg.norm(ec_vec)
    sc_uvec = sc_vec / sc_norm
    ec_uvec = ec_vec / ec_norm

    # 计算夹角
    dot_prod = np.dot(sc_uvec, ec_uvec)
    # 防止浮点数误差导致 arccos 越界
    dot_prod = np.clip(dot_prod, -1.0, 1.0)
    end_angle = np.arccos(dot_prod)

    # 共线检查
    if (end_angle == 0) or (end_angle == np.pi):
        return False

    # 检查半径是否过大
    if radius / np.tan(end_angle / 2) > min(sc_norm, ec_norm):
        # print("Warning: Radius too large for corner.")
        return False

    # 计算圆心方向向量
    net_uvec = (sc_uvec + ec_uvec) / np.linalg.norm(sc_uvec + ec_uvec)

    # 计算圆心坐标
    circle_center = vertex_corner + net_uvec * radius / np.sin(end_angle / 2)

    # 计算起始角度和结束角度
    delta_x = vertex_corner[0] - circle_center[0]
    delta_y = vertex_corner[1] - circle_center[1]

    if delta_x:
        theta_mid = np.arctan(delta_y / delta_x) + np.pi * int(delta_x < 0)
    else:
        theta_mid = np.pi * ((1 - 2 * int(delta_y < 0)) + int(delta_y < 0))

    theta_start = theta_mid - (np.pi - end_angle) / 2
    theta_end = theta_mid + (np.pi - end_angle) / 2

    p1 = circle_center + radius * np.array([np.cos(theta_start), np.sin(theta_start)])
    p2 = circle_center + radius * np.array([np.cos(theta_end), np.sin(theta_end)])

    # 解决 arctan 模糊性
    if np.linalg.norm(vertex_start - p2) < np.linalg.norm(vertex_start - p1):
        theta_start, theta_end = theta_end, theta_start

    # 生成圆弧点集
    # 注意：这里我们生成点集，不包括起点（起点由上一段线连接）
    angles = np.linspace(theta_start, theta_end, points)
    # 如果 points 很小，至少保证有头尾
    if len(angles) < 2:
        return False

    path_points = []
    # 从第二个点开始取，因为第一个点理论上会接上之前的路径
    for theta in angles[1:]:
        pt = circle_center + radius * np.array([np.cos(theta), np.sin(theta)])
        path_points.append(pt)

    return np.array(path_points)


# --- 辅助函数 3: 改写 fillet_path (去除 self 和 DataFrame 依赖) ---
def _process_fillet_path(line_geometry, fillet_radius, resolution, precision):
    """处理 LineString，将拐角替换为圆弧点集"""
    path = list(line_geometry.coords)
    if len(path) <= 2:
        return line_geometry

    path = np.array(path)
    newpath = np.array([path[0]])  # 初始化新路径，包含起点

    # 获取不可圆角的点索引 (使用我们的 mock 函数)
    no_fillet = bad_fillet_idxs(path, fillet_radius, precision)

    # 遍历每三个点组成的一个角
    for i, (start, corner, end) in enumerate(zip(path, path[1:], path[2:])):
        # i 是当前 corner 在 path[1:] 中的索引，对应原始 path 中的 index = i+1
        current_corner_idx = i + 1

        should_skip = current_corner_idx in no_fillet

        fillet_points = False
        if not should_skip:
            fillet_points = _calc_fillet_standalone(
                np.array(start),
                np.array(corner),
                np.array(end),
                fillet_radius,
                resolution
            )

        if fillet_points is not False:
            # 如果成功计算出圆角，加入圆角点集
            newpath = np.concatenate((newpath, fillet_points))
        else:
            # 否则保留原始拐角
            newpath = np.concatenate((newpath, np.array([corner])))

    # 加入终点
    newpath = np.concatenate((newpath, np.array([path[-1]])))

    return LineString(newpath)


# --- 主函数: 生成 CPW ---
def generate_cpw_from_line(line_string, width, gap, fillet_radius, resolution=32, precision=9):
    """
    输入 LineString，生成带圆角的 CPW Trace 和 Gap 多边形。

    Args:
        line_string (LineString): 原始路径
        width (float): 导线宽度
        gap (float): 间隙宽度
        fillet_radius (float): 圆角半径
        resolution (int): 圆角的精细度（点数）
        precision (int): 精度位数

    Returns:
        (Polygon, Polygon): 返回 (Trace_Polygon, Gap_Polygon)
    """

    # 1. 第一步：生成带圆角的线性路径 (LineString)
    # 如果没有圆角需求，直接使用原始路径
    if fillet_radius <= 0:
        filleted_line = line_string
    else:
        filleted_line = _process_fillet_path(line_string, fillet_radius, resolution, precision)

    # 2. 第二步：生成中心导线 (Trace) 多边形
    # 使用 render_path 中的逻辑：buffer(width/2)
    trace_poly = filleted_line.buffer(
        distance=width / 2.0,
        cap_style=CAP_STYLE.flat,
        join_style=JOIN_STYLE.mitre,
        resolution=resolution
    )

    # 3. 第三步：生成间隙 (Gap) 多边形
    # Gap 通常用于做减法层 (Subtract)。总宽度 = width + 2*gap
    total_width = width + 2 * gap
    gap_poly = filleted_line.buffer(
        distance=total_width / 2.0,
        cap_style=CAP_STYLE.flat,
        join_style=JOIN_STYLE.mitre,
        resolution=resolution
    )

    return trace_poly, gap_poly