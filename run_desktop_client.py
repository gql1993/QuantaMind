#!/usr/bin/env python3
"""
QuantaMind 桌面客户端 —— 双击即用
1. 自动在后台启动 Gateway（若未运行）
2. 等待 Gateway 就绪
3. 打开浏览器访问 Web 客户端（OpenClaw 风格界面）
"""

import json
import subprocess
import sys
import time
import traceback
import urllib.request
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
GATEWAY_PORT = 18789
GATEWAY_BASE = f"http://127.0.0.1:{GATEWAY_PORT}"


def gateway_ok() -> bool:
    try:
        req = urllib.request.Request(f"{GATEWAY_BASE}/health", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_gateway():
    run_gw = PROJECT_ROOT / "run_gateway.py"
    if not run_gw.exists():
        return
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW
    subprocess.Popen(
        [sys.executable, str(run_gw)],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )


def wait_ready(timeout=30) -> bool:
    if gateway_ok():
        return True
    start_gateway()
    for _ in range(timeout):
        time.sleep(1)
        if gateway_ok():
            return True
    return False


def main():
    print("QuantaMind: 正在启动服务端…")
    ok = wait_ready()
    if ok:
        url = GATEWAY_BASE
        print(f"QuantaMind: Gateway 已就绪，打开浏览器 → {url}")
        webbrowser.open(url)
        print("QuantaMind: 客户端已在浏览器中打开。关闭此窗口不影响服务端运行。")
        # 保持进程等待，便于用户知道它在运行
        try:
            input("按 Enter 退出此窗口…")
        except (EOFError, KeyboardInterrupt):
            pass
    else:
        msg = (
            f"QuantaMind: 无法启动 Gateway（端口 {GATEWAY_PORT}）。\n"
            "请检查：\n"
            f"  1. 端口 {GATEWAY_PORT} 是否被占用\n"
            "  2. Python 依赖是否已安装（pip install -r requirements.txt）\n"
            f"  3. 或手动运行：python run_gateway.py\n"
        )
        print(msg)
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("QuantaMind 启动失败", msg)
            root.destroy()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("QuantaMind 启动失败", f"错误：\n{e}\n\n{traceback.format_exc()}")
            root.destroy()
        except Exception:
            traceback.print_exc()
        sys.exit(1)
