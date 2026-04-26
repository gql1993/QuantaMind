# QuantaMind 桌面客户端 — 仅需运行本程序即可（将自动启动 Gateway，无需单独运行 run_gateway.py）

import json
import queue
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

from quantamind import config

# Gateway 地址（客户端连接用 localhost）
GATEWAY_BASE = f"http://127.0.0.1:{config.GATEWAY_PORT}"

# 项目根目录（run_gateway.py 所在目录）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _gateway_ok() -> bool:
    """检测 Gateway 是否已就绪"""
    try:
        req = urllib.request.Request(f"{GATEWAY_BASE}/health", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _start_gateway_background() -> bool:
    """在后台启动 Gateway 进程（无窗口），返回是否已启动"""
    run_gateway = _PROJECT_ROOT / "run_gateway.py"
    if not run_gateway.exists():
        return False
    try:
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.CREATE_NO_WINDOW  # 0x08000000，不弹出黑窗口
        subprocess.Popen(
            [sys.executable, str(run_gateway)],
            cwd=str(_PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        return True
    except Exception:
        return False


def _wait_gateway_ready(timeout_sec: int = 30) -> bool:
    """若 Gateway 未运行则自动启动并等待就绪。仅需运行桌面客户端即可，无需单独启动 Gateway。"""
    if _gateway_ok():
        return True
    _start_gateway_background()
    for i in range(timeout_sec):
        time.sleep(1)
        if _gateway_ok():
            return True
    return False


def _http_post_json(url: str, data: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_status() -> Optional[dict]:
    """拉取运转看板汇总数据 GET /api/v1/status"""
    try:
        req = urllib.request.Request(f"{GATEWAY_BASE}/api/v1/status", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def create_session() -> Optional[str]:
    try:
        out = _http_post_json(f"{GATEWAY_BASE}/api/v1/sessions", {})
        return out.get("session_id")
    except Exception:
        return None


def chat_stream(session_id: Optional[str], message: str, chunk_queue: queue.Queue) -> None:
    """在后台线程中请求流式对话，把每个 content chunk 放入 chunk_queue。"""
    try:
        data = {"message": message, "stream": True}
        if session_id:
            data["session_id"] = session_id
        req = urllib.request.Request(
            f"{GATEWAY_BASE}/api/v1/chat",
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            buf = b""
            for chunk in iter(lambda: resp.read(1), b""):
                buf += chunk
                if b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if line.startswith(b"data: "):
                        try:
                            obj = json.loads(line[6:].decode("utf-8"))
                            if obj.get("type") == "content" and obj.get("data"):
                                chunk_queue.put(("content", obj["data"]))
                            if obj.get("type") == "done":
                                chunk_queue.put(("done", None))
                                return
                        except (json.JSONDecodeError, KeyError):
                            pass
        chunk_queue.put(("done", None))
    except Exception as e:
        chunk_queue.put(("error", str(e)))


def run_desktop_app() -> None:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, font as tkfont

    root = tk.Tk()
    root.title("QuantaMind 客户端")
    root.minsize(600, 500)
    root.geometry("900x620")

    # 状态与会话
    session_id: Optional[str] = None
    chunk_queue: queue.Queue = queue.Queue()
    sending = [False]  # 用 list 以便闭包内修改

    # 字体
    try:
        font_family = "Microsoft YaHei UI" if "Microsoft YaHei UI" in list(tkfont.families()) else "TkDefaultFont"
    except Exception:
        font_family = "TkDefaultFont"
    font_normal = (font_family, 10)
    font_bold = (font_family, 10, "bold")
    font_small = (font_family, 9)

    # 顶部：标题 + 连接状态
    top = ttk.Frame(root, padding=8)
    top.pack(fill=tk.X)
    ttk.Label(top, text="QuantaMind · 量子科研 AI 中台", font=font_bold).pack(side=tk.LEFT)
    status_var = tk.StringVar(value="未连接")
    ttk.Label(top, textvariable=status_var).pack(side=tk.RIGHT, padx=8)

    # 主区域：标签页（对话 | 运转看板）
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

    # ---------- 标签页 1：对话 ----------
    chat_tab = ttk.Frame(notebook, padding=4)
    notebook.add(chat_tab, text="  对话  ")
    chat_frame = ttk.Frame(chat_tab, padding=4)
    chat_frame.pack(fill=tk.BOTH, expand=True)
    chat = scrolledtext.ScrolledText(
        chat_frame,
        wrap=tk.WORD,
        font=font_normal,
        state=tk.DISABLED,
        padx=8,
        pady=8,
    )
    chat.pack(fill=tk.BOTH, expand=True)

    def append_chat(role: str, text: str) -> None:
        chat.config(state=tk.NORMAL)
        if role == "user":
            chat.insert(tk.END, "You\n", "role_user")
            chat.insert(tk.END, text.strip() + "\n\n", "msg_user")
        else:
            chat.insert(tk.END, "QuantaMind\n", "role_bot")
            chat.insert(tk.END, text + "\n\n", "msg_bot")
        chat.config(state=tk.DISABLED)
        chat.see(tk.END)

    chat.tag_configure("role_user", font=font_bold, foreground="#1a73e8")
    chat.tag_configure("msg_user", foreground="#202124")
    chat.tag_configure("role_bot", font=font_bold, foreground="#0d47a1")
    chat.tag_configure("msg_bot", foreground="#3c4043")

    # 输入区（放在对话标签页内）
    input_frame = ttk.Frame(chat_tab, padding=8)
    input_frame.pack(fill=tk.X)
    input_var = tk.StringVar()
    input_box = ttk.Entry(input_frame, textvariable=input_var, font=font_normal)
    input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
    send_btn = ttk.Button(input_frame, text="发送")

    def flush_stream_to_chat() -> None:
        while True:
            try:
                typ, data = chunk_queue.get_nowait()
            except queue.Empty:
                break
            if typ == "content" and data:
                chat.config(state=tk.NORMAL)
                chat.insert(tk.END, data, "msg_bot")
                chat.config(state=tk.DISABLED)
                chat.see(tk.END)
            elif typ == "done":
                chat.config(state=tk.NORMAL)
                chat.insert(tk.END, "\n", "msg_bot")
                chat.config(state=tk.DISABLED)
                chat.see(tk.END)
                sending[0] = False
                send_btn.config(state=tk.NORMAL)
                input_box.config(state=tk.NORMAL)
            elif typ == "error":
                append_chat("assistant", f"[错误] {data}")
                sending[0] = False
                send_btn.config(state=tk.NORMAL)
                input_box.config(state=tk.NORMAL)
        root.after(100, flush_stream_to_chat)

    def do_send() -> None:
        msg = input_var.get().strip()
        if not msg or sending[0]:
            return
        nonlocal session_id
        if not session_id:
            session_id = create_session()
            if not session_id:
                messagebox.showerror(
                    "连接失败",
                    "无法连接服务端。本程序会自动尝试启动 Gateway；若仍失败，请检查端口是否被占用后重试，或手动运行：\npython run_gateway.py\n\n地址：%s" % GATEWAY_BASE,
                )
                return
            status_var.set(f"已连接 · {session_id[:8]}...")
        append_chat("user", msg)
        input_var.set("")
        sending[0] = True
        send_btn.config(state=tk.DISABLED)
        input_box.config(state=tk.DISABLED)
        chat.config(state=tk.NORMAL)
        chat.insert(tk.END, "QuantaMind\n", "role_bot")
        chat.config(state=tk.DISABLED)
        def run_stream():
            chat_stream(session_id, msg, chunk_queue)
        t = threading.Thread(target=run_stream, daemon=True)
        t.start()
        root.after(100, flush_stream_to_chat)

    send_btn.config(command=do_send)
    send_btn.pack(side=tk.RIGHT)
    input_box.bind("<Return>", lambda e: do_send())

    # ---------- 标签页 2：运转看板 ----------
    dashboard_tab = ttk.Frame(notebook, padding=12)
    notebook.add(dashboard_tab, text="  运转看板  ")
    # 看板内容容器（滚动区域用 Frame + Canvas 简化，此处用多行 Label 更新）
    dash_inner = ttk.Frame(dashboard_tab)
    dash_inner.pack(fill=tk.BOTH, expand=True)
    # 各区块用 Label 显示，定时刷新
    dash_vars = {
        "gateway": tk.StringVar(value="Gateway：—"),
        "sessions": tk.StringVar(value="会话数：—"),
        "tasks": tk.StringVar(value="任务：—"),
        "heartbeat": tk.StringVar(value="Heartbeat：—"),
        "skills_tools": tk.StringVar(value="技能 / 工具：—"),
        "platforms": tk.StringVar(value="六大平台：—"),
        "updated": tk.StringVar(value="上次刷新：—"),
    }

    def _dash_section(parent_: tk.Misc, title: str, var: tk.StringVar) -> None:
        f = ttk.LabelFrame(parent_, text=title, padding=6)
        f.pack(fill=tk.X, pady=4)
        ttk.Label(f, textvariable=var, font=font_small, wraplength=800).pack(anchor=tk.W)

    _dash_section(dash_inner, "网关", dash_vars["gateway"])
    _dash_section(dash_inner, "会话", dash_vars["sessions"])
    _dash_section(dash_inner, "任务", dash_vars["tasks"])
    _dash_section(dash_inner, "心跳与自主任务", dash_vars["heartbeat"])
    _dash_section(dash_inner, "技能与工具", dash_vars["skills_tools"])
    _dash_section(dash_inner, "六大平台运转状态", dash_vars["platforms"])
    ttk.Label(dash_inner, textvariable=dash_vars["updated"], font=font_small).pack(anchor=tk.E, pady=4)

    def apply_status(data: Optional[dict]) -> None:
        """在主线程根据 status 数据更新看板变量"""
        import datetime
        if not data:
            dash_vars["gateway"].set("Gateway：未连接")
            dash_vars["sessions"].set("会话数：—")
            dash_vars["tasks"].set("任务：—")
            dash_vars["heartbeat"].set("Heartbeat：—")
            dash_vars["skills_tools"].set("技能 / 工具：—")
            dash_vars["platforms"].set("六大平台：—")
            dash_vars["updated"].set("上次刷新：失败")
            return
        g = data.get("gateway", {})
        dash_vars["gateway"].set(f"Gateway：{g.get('status', '—')} · {g.get('service', '')}")
        dash_vars["sessions"].set(f"会话数：{data.get('sessions_count', 0)}")
        t = data.get("tasks", {})
        dash_vars["tasks"].set(
            f"总任务 {t.get('total', 0)}  |  待办 {t.get('pending', 0)}  |  进行中 {t.get('running', 0)}  |  已完成 {t.get('completed', 0)}  |  待审批 {t.get('pending_approval', 0)}"
        )
        h = data.get("heartbeat", {})
        dash_vars["heartbeat"].set(
            f"层级 {h.get('level', '—')}  间隔 {h.get('interval_minutes', '—')} 分钟  |  上次运行 {h.get('last_run') or '—'}  下次 {h.get('next_run') or '—'}"
        )
        dash_vars["skills_tools"].set(f"技能 {data.get('skills_count', 0)} 个  |  工具 {data.get('tools_count', 0)} 个")
        pl = data.get("platforms", {})
        lines = []
        for k, v in (pl if isinstance(pl, dict) else {}).items():
            name = v.get("name", k)
            st = v.get("status", "—")
            msg = v.get("message", "")
            lines.append(f"  · {name}：{st}  {msg}")
        dash_vars["platforms"].set("\n".join(lines) if lines else "—")
        dash_vars["updated"].set(f"上次刷新：{datetime.datetime.now().strftime('%H:%M:%S')}  每 5 秒自动刷新")

    def refresh_dashboard() -> None:
        """后台拉取状态并在主线程更新界面"""
        def do_fetch():
            data = fetch_status()
            root.after(0, lambda: apply_status(data))
        threading.Thread(target=do_fetch, daemon=True).start()

    def schedule_dashboard_refresh() -> None:
        refresh_dashboard()
        root.after(5000, schedule_dashboard_refresh)

    def on_dashboard_selected(_event=None) -> None:
        try:
            if notebook.index(notebook.select()) == 1:
                refresh_dashboard()
        except Exception:
            pass
    notebook.bind("<<NotebookTabChanged>>", on_dashboard_selected)
    root.after(800, refresh_dashboard)
    root.after(5000, schedule_dashboard_refresh)

    # 启动时自动启动 Gateway（若未运行）并连接，仅需运行本客户端即可
    def try_connect():
        status_var.set("正在连接或自动启动服务端…")
        append_chat("assistant", "正在连接或自动启动服务端（仅需运行本程序，无需单独启动 Gateway）…")

        def connect_in_background():
            ok = _wait_gateway_ready()
            def on_main():
                nonlocal session_id
                if ok:
                    session_id = create_session()
                    if session_id:
                        status_var.set(f"已连接 · {session_id[:8]}...")
                        append_chat("assistant", "已就绪。输入消息与 AI 科学家对话。")
                    else:
                        status_var.set("未连接")
                        append_chat("assistant", "服务端已启动但会话创建失败，请重试。")
                else:
                    status_var.set("未连接")
                    append_chat(
                        "assistant",
                        "已尝试自动启动服务端但未成功。请检查端口 %s 是否被占用，或手动在终端执行：\npython run_gateway.py\n然后重新打开本客户端。"
                        % config.GATEWAY_PORT,
                    )
            root.after(0, on_main)
        threading.Thread(target=connect_in_background, daemon=True).start()

    root.after(200, try_connect)
    root.after(200, flush_stream_to_chat)

    root.mainloop()
