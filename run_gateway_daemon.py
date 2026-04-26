"""
QuantaMind Gateway 守护进程

功能：
1. 单实例运行，避免重复启动
2. 自动拉起 Gateway
3. 周期性健康检查（端口 + /api/v1/status）
4. 发现 Gateway 崩溃或假死时自动重启
5. 写入独立日志，适合 pythonw / VBS / 计划任务后台运行
"""
import atexit
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
GATEWAY_SCRIPT = str(BASE_DIR / "run_gateway.py")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from quantamind.config import DEFAULT_ROOT as QUANTAMIND_ROOT  # noqa: E402
RUN_DIR = QUANTAMIND_ROOT / "run"
LOG_DIR = QUANTAMIND_ROOT / "logs"
RUN_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

PID_FILE = RUN_DIR / "gateway_daemon.pid"
DAEMON_LOG = LOG_DIR / "gateway-daemon.log"
GATEWAY_LOG = LOG_DIR / "gateway.log"

GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 18789
HEALTH_URL = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}/health"
STATUS_URL = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}/api/v1/status"

CHECK_INTERVAL = 5
STARTUP_GRACE_SEC = 120
UNHEALTHY_LIMIT = 8
RESTART_DELAY = 3
COOLDOWN_WINDOW = 60
MAX_CRASHES_IN_WINDOW = 5
MAX_RESTART = 1000

proc = None
crash_times = []
unhealthy_count = 0
external_gateway_seen = False
_LOCAL_HTTP_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        with DAEMON_LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        print(line)
    except Exception:
        pass


def is_port_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def is_http_healthy(timeout: float = 5.0) -> bool:
    for url in (HEALTH_URL, STATUS_URL):
        try:
            req = urllib.request.Request(url, headers={"Connection": "close"})
            with _LOCAL_HTTP_OPENER.open(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return True
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue
    return False


def _pid_alive(pid: int) -> bool:
    try:
        if pid <= 0:
            return False
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def ensure_singleton() -> None:
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            if _pid_alive(old_pid):
                log(f"检测到已有守护进程运行，pid={old_pid}，本次退出。")
                raise SystemExit(0)
        except Exception:
            pass
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def cleanup_pid_file() -> None:
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
    except Exception:
        pass


def start_gateway() -> subprocess.Popen:
    with GATEWAY_LOG.open("a", encoding="utf-8") as out:
        out.write("\n" + "=" * 80 + "\n")
        out.write(f"Gateway daemon start at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    out_handle = GATEWAY_LOG.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "-X", "utf8", GATEWAY_SCRIPT],
        cwd=str(BASE_DIR),
        stdout=out_handle,
        stderr=subprocess.STDOUT,
    )
    process._quantamind_log_handle = out_handle  # type: ignore[attr-defined]
    log(f"已启动 Gateway，pid={process.pid}")
    return process


def stop_gateway(process: subprocess.Popen, reason: str) -> None:
    log(f"准备停止 Gateway(pid={process.pid})，原因：{reason}")
    try:
        process.terminate()
        process.wait(timeout=10)
    except Exception:
        try:
            process.kill()
            process.wait(timeout=5)
        except Exception:
            pass
    try:
        handle = getattr(process, "_quantamind_log_handle", None)
        if handle:
            handle.close()
    except Exception:
        pass


def main_loop() -> None:
    global proc, unhealthy_count, external_gateway_seen

    for attempt in range(1, MAX_RESTART + 1):
        now = time.time()
        crash_times.append(now)
        recent = [t for t in crash_times if now - t < COOLDOWN_WINDOW]
        if len(recent) > MAX_CRASHES_IN_WINDOW:
            log(f"最近 {COOLDOWN_WINDOW}s 内连续重启 {len(recent)} 次，暂停 30s 后继续。")
            time.sleep(30)
            crash_times.clear()

        if proc is None and is_port_open(GATEWAY_HOST, GATEWAY_PORT) and is_http_healthy():
            if not external_gateway_seen:
                log("检测到已有可用 Gateway 进程，守护进入监视模式。")
                external_gateway_seen = True
            time.sleep(CHECK_INTERVAL)
            continue

        if proc is None or proc.poll() is not None:
            proc = start_gateway()
            external_gateway_seen = False
            unhealthy_count = 0
            started_at = time.time()

        while proc and proc.poll() is None:
            time.sleep(CHECK_INTERVAL)
            port_ok = is_port_open(GATEWAY_HOST, GATEWAY_PORT)
            http_ok = is_http_healthy()

            if time.time() - started_at < STARTUP_GRACE_SEC:
                if port_ok or http_ok:
                    continue
                else:
                    continue

            # 启动宽限期后，必须能稳定返回 HTTP 响应。
            # 仅端口监听但接口完全不回包，说明网关已进入假死状态，需要重启。
            if port_ok and http_ok:
                unhealthy_count = 0
                continue

            unhealthy_count += 1
            log(f"健康检查失败，第 {unhealthy_count}/{UNHEALTHY_LIMIT} 次：port_ok={port_ok}, http_ok={http_ok}")

            if unhealthy_count >= UNHEALTHY_LIMIT:
                stop_gateway(proc, "健康检查连续失败")
                proc = None
                unhealthy_count = 0
                break

        if proc is not None and proc.poll() is not None:
            code = proc.returncode
            log(f"Gateway 已退出，exit_code={code}")
            try:
                handle = getattr(proc, "_quantamind_log_handle", None)
                if handle:
                    handle.close()
            except Exception:
                pass
            proc = None

        log(f"{RESTART_DELAY}s 后尝试重启 Gateway")
        time.sleep(RESTART_DELAY)


def _handle_exit(signum=None, frame=None) -> None:
    global proc
    log("守护进程收到退出信号，准备清理。")
    if proc and proc.poll() is None:
        stop_gateway(proc, "守护进程退出")
    cleanup_pid_file()
    raise SystemExit(0)


if __name__ == "__main__":
    try:
        os.system("chcp 65001 > nul")
    except Exception:
        pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ensure_singleton()
    atexit.register(cleanup_pid_file)
    signal.signal(signal.SIGTERM, _handle_exit)
    signal.signal(signal.SIGINT, _handle_exit)

    log("QuantaMind Gateway 守护进程已启动。")
    log(f"守护日志：{DAEMON_LOG}")
    log(f"网关日志：{GATEWAY_LOG}")
    main_loop()
