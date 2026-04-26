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
import json
import numpy as np


# class NumpyEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, np.ndarray):
#             return obj.tolist()
#         elif isinstance(obj, (list, dict)):
#             return json.loads(json.dumps(obj, cls=NumpyEncoder))
#         return super().default(obj)
def convert_keys_to_int(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            # 尝试将键转换为整数
            new_key = int(key) if key.isdigit() else key
            # 递归处理子字典
            new_dict[new_key] = convert_keys_to_int(value)
        return new_dict
    elif isinstance(obj, list):
        # 如果是列表，递归处理每个元素
        return [convert_keys_to_int(item) for item in obj]
    else:
        # 其他类型保持不变
        return obj


def save_json(design, path, component_id_list=None):
    """将量子版图参数保存为JSON格式.
    Args:
        design: 需要保存的设计；
        path(str): 保存的路径；
        component_id_list(list): 需要保存的组件id,如果是None则保存所有组件。
    """
    components_dict = {}
    for component_id, component in design.components.items():
        if component_id_list is not None:
            if component_id in component_id_list:
                # Get the component's parameters
                params = component.options
                components_dict[component_id] = params
        else:
            params = component.options
            components_dict[component_id] = params
    with open(path, 'w') as json_file:
        json.dump(components_dict, json_file, indent=4)
    return components_dict


def save_json_parameter(parameter, path):
    with open(path, 'w') as json_file:
        json.dump(parameter, json_file, indent=4)


def load_json(path):
    # Load the dictionary back from the file
    with open(path, 'r') as json_file:
        loaded_components_dict = json.load(json_file)
    return loaded_components_dict
#
# #copy parameter of components to others
# def parameter_copy(design,original_list,target_list):





