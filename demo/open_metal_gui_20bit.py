"""打开 MetalGUI 查看 20 比特 CT20Q 芯片真实版图"""
import os, sys, json

# 确保不用 offscreen
os.environ.pop("QT_QPA_PLATFORM", None)

from qiskit_metal import designs, MetalGUI
from qiskit_metal.qlibrary.user_components.my_qcomponent import *
from qiskit_metal.qlibrary.user_components.save_load import *
from qiskit_metal.qlibrary.user_components.reader import *

json_path = r"E:\work\QuantaMind\quantamind\server\CT20QV2_01.json"

print("Creating design...")
design = designs.DesignPlanar()
design.overwrite_enabled = True
design.chips['main']['material'] = 'sapphire'
design.chips.main.size['size_x'] = '12.5mm'
design.chips.main.size['size_y'] = '12.5mm'

print(f"Loading parameters from {json_path}...")
try:
    load_design(design, json_path)
    print(f"Loaded {len(design.components)} components")
except Exception as e:
    print(f"load_design failed: {e}")
    print("Trying manual JSON load...")
    with open(json_path, 'r', encoding='utf-8') as f:
        params = json.load(f)
    print(f"JSON has {len(params)} entries")

print("Opening MetalGUI...")
gui = MetalGUI(design)
gui.rebuild()
gui.autoscale()
gui.main_window.show()

print("\nMetalGUI is open! You can:")
print("  - Zoom/pan to view the chip layout")
print("  - Click components to see parameters")
print("  - Close the window when done")
print("\nPress Ctrl+C in this console to exit.")

try:
    from qiskit_metal.qlibrary.user_components.my_qcomponent import QApplication
    QApplication.instance().exec_()
except:
    input("Press Enter to close...")
