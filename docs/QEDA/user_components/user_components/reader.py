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
import pandas as pd
from qiskit_metal import draw, Dict,designs,MetalGUI


def extract_strings(s):
    """将字符串中以{}分隔的子字符串提取出来.
    Args:
        s (str): 需要提取的字符串.

    Returns:
        List: 提取出来的字符串组成的列表
    """
    results = []
    current = ""
    stack = []
    for char in s:
        if char == '{':
            if current:
                results.append(current)
                current = ""
            stack.append(results)
            results = []
        elif char == '}':
            if current:
                results.append(current)
                current = ""
            temp = results
            results = stack.pop()
            results.extend(temp)
        else:
            current += char

    if current:
        results.append(current)

    return results


def set_nested_dict_value(d, keys, value):
    """设置嵌套字典的键和值.
    Args:
        d (dict): 需要设置的字典.
        keys(str): 设置的键
        value(any):设置的值
    """
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def update_nested_dict(original, new):
    """更新嵌套字典的键和值.
    Args:
        original (dict): 需要更新的字典.
        new(dict): 更新后的字典
    """
    for key, value in new.items():
        if isinstance(value, dict) and key in original and isinstance(original[key], dict):
            update_nested_dict(original[key], value)
        else:
            original[key] = value


def extract_nested_dict(path: str, set_index: str):
    """将excel中的数据转换为dictionary
    Args:
    path(str): excel的路径名称
    set_index (str): 需要将excel中的哪一列当做索引

    Returns:
    dict: 返回转换后的字典型数据
    """
    nested_dict = {}
    df = pd.read_excel(path)
    df.columns = df.columns.str.replace(' ', '')
    df.set_index(set_index, inplace=True)
    for row_index in df.index:
        for col_name in df.columns.to_list():
            key_list = extract_strings(col_name)
            key_list.insert(0, row_index)
            if not pd.isna(df.loc[row_index, col_name]):
                set_nested_dict_value(nested_dict, key_list, df.loc[row_index, col_name])
    return nested_dict


def parameter_import(design, parameter: dict):
    # design_copy = design
    # gui = MetalGUI(design)
    for key, value in parameter.items():
        update_nested_dict(design.components[key].options, value)
        # gui.rebuild()


