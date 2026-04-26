"""
独立启动 MetalGUI 查看芯片设计
不在 Gateway 进程中运行，而是作为独立进程弹出
"""
import subprocess
import sys
import os

def open_gui_with_design(json_path: str = None, gds_path: str = None) -> dict:
    """在独立进程中启动 MetalGUI"""
    script = r'''
import os, sys, json
os.environ.pop("QT_QPA_PLATFORM", None)

from qiskit_metal import designs, MetalGUI
from qiskit_metal.qlibrary.user_components.my_qcomponent import *
from qiskit_metal.qlibrary.user_components.save_load import *
from qiskit_metal.qlibrary.user_components.reader import *

json_path = sys.argv[1] if len(sys.argv) > 1 else None

design = designs.DesignPlanar()
gui = MetalGUI(design)
design.overwrite_enabled = True

if json_path and os.path.exists(json_path):
    print(f"Loading design from {json_path}")
    load_design(design, json_path)
    gui.rebuild()
    gui.autoscale()
    print("Design loaded. MetalGUI is open.")
else:
    design.chips.main.size.size_x = '12.5mm'
    design.chips.main.size.size_y = '12.5mm'
    print("Empty 12.5mm design created. MetalGUI is open.")

gui.main_window.show()
input("Press Enter to close MetalGUI...")
'''
    # Determine which JSON to load
    if json_path is None:
        json_path = str(os.path.join(os.path.dirname(__file__), "CT20QV2_01.json"))

    try:
        proc = subprocess.Popen(
            [sys.executable, "-c", script, json_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
        )
        return {
            "status": "launched",
            "pid": proc.pid,
            "json_loaded": json_path,
            "note": "MetalGUI window should appear shortly. Close the console window when done.",
        }
    except Exception as e:
        return {"error": str(e)}
