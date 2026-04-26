from abc import ABC, abstractmethod
from qiskit_metal import designs, MetalGUI
import os
from qiskit_metal.qlibrary.user_components.reader import parameter_import
from qiskit_metal.qlibrary.user_components.save_load import convert_keys_to_int, load_json
from qiskit_metal.qlibrary.user_components.writer import *


class QuantumChip(ABC):
    def __init__(self, design=None, gui=None,  jj_path='', parameter_file_path: str = None,):
        """
        初始化芯片基类。
        :param design: Qiskit Metal Design 对象。如果为 None，会自动创建。
        :param gui: MetalGUI 对象，或者 bool 值。
                    - 传入对象: 直接使用。
                    - 传入 True: 自动开启 GUI。
                    - 传入 None/False: 不开启 GUI。
        :param parameter_file_path: 参数文件路径 (JSON等)。
        """
        # --- 1. 处理 Design 环境 ---
        if design is None:
            print("[QuantumChip] No design provided. Creating new DesignPlanar...")
            self.design = designs.DesignPlanar()
            self._created_internal_design = True  # 标记一下是我们自己创建的
        else:
            self.design = design
            self._created_internal_design = False

        # --- 2. 处理 GUI 环境 ---
        if isinstance(gui, MetalGUI):
            # 情况 A: 用户传进来了现成的 GUI 对象
            self.gui = gui
        elif gui is None:
            # 情况 B: 用户想开启 GUI，但没传对象，我们帮他 new 一个
            print("[QuantumChip] Starting new MetalGUI...")
            self.gui = MetalGUI(self.design)
        else:
            # 情况 C: 不需要 GUI (比如在服务器跑脚本时)
            self.gui = None

        # --- 3. 处理参数导入 (原 parameter_import) ---
        self.parameter_file_path = parameter_file_path
        if self.parameter_file_path:
            self._load_parameters()
        self.jj_path = jj_path

    def _load_parameters(self):
        """对应原 parameter_import 函数"""
        if not os.path.exists(self.parameter_file_path):
            print(f"[Warning] Parameter file not found: {self.parameter_file_path}")
            return

        print(f"[QuantumChip] Loading parameters from {self.parameter_file_path}...")
        # 假设参数文件是 JSON 格式
        try:
            with open(self.parameter_file_path, 'r') as f:
                parameter_import(self.design, convert_keys_to_int(load_json(self.parameter_file_path)))
            # 将参数更新到 design 变量中 (根据你的具体逻辑调整)
            # self.design.variables.update(params)
        except Exception as e:
            print(f"[Error] Failed to load parameters: {e}")

    def export_gds(self, output_path: str, output_name: str, negative_mask=[1,2,3],cheese_view=[]):
        """对应原 layout_generation 的导出部分"""
        full_path = os.path.join(output_path, f"{output_name}.gds")
        print(f"[QuantumChip] Exporting GDS to {full_path}...")

        # 调用 Metal 的导出接口
        a_gds = self.design.renderers.gds
        a_gds.options['path_filename'] = full_path
        a_gds.options['no_cheese']['buffer'] = '0um'  # 示例配置
        a_gds = writer_planar(self.design, self.jj_path, negative_mask=[1, 2, 3], cheese_view=cheese_view)
        a_gds.export_to_gds(output_name + ".gds")

    def simulate_q3d(self, setup_name="Setup", max_passes=15):
        """对应原 q3d_simulation"""
        print(f"[QuantumChip] Starting Q3D Simulation: {setup_name}...")
        # Q3D 仿真逻辑...
        pass

    @abstractmethod
    def build(self, **kwargs):
        """子类必须实现这个方法"""
        pass