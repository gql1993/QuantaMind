"""
工业级版图生成器 — 方案 A+B 组合（带子进程隔离）

B: Monkey-patch MetalGUI 为 NoopGUI（跳过 Qt 窗口）
A: SafeRoutePathfinder 包裹所有寻路 + 中间 GDS 检查点
   RoutePathfinder 第一次被调用前自动导出中间 GDS（meanders 已完成）
   整个布局在子进程中运行（subprocess.Popen），segfault 不影响主进程

用法:
    from quantamind.server.industrial_layout_runner import generate_industrial_gds
    result = generate_industrial_gds()
"""

import os
import sys
import time
import json
import logging
import subprocess
from pathlib import Path

_log = logging.getLogger("quantamind.industrial_layout")

_WORKER_SCRIPT = Path(__file__).parent / "_layout_worker.py"
PARAMS_JSON = Path(__file__).parent / "CT20QV2_01.json"
OUTPUT_DIR = Path(os.path.expanduser("~/.quantamind/outputs/chip_designs")).resolve()

_CHECKPOINT_SUFFIX = "_checkpoint.gds"
_RESULT_FILENAME = "_layout_result.json"


def generate_industrial_gds(
    output_filename: str = "CT20QV2_industrial.gds",
    parameter_file: str = None,
    meander_length_list: list = None,
    jj_dict: dict = None,
    timeout: int = 900,
) -> dict:
    """
    Run the team's twenty_qubits_tunable_coupler_layout() in an isolated
    subprocess with NoopGUI + SafeRoutePathfinder, then export GDS.

    If the subprocess segfaults during routing, falls back to the intermediate
    checkpoint GDS (meanders + qubits + couplers, before readout/routing lines).

    Args:
        output_filename: GDS file name (saved under ~/.quantamind/outputs/chip_designs/)
        parameter_file:  Path to component parameter JSON. Defaults to CT20QV2_01.json.
        meander_length_list: Unused placeholder (reserved for future).
        jj_dict: Unused placeholder (reserved for future).
        timeout: Max seconds to wait for the subprocess (default 900 = 15 min).

    Returns:
        dict with success/error info, file path, component stats, etc.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(OUTPUT_DIR / output_filename)
    checkpoint_path = str(OUTPUT_DIR / output_filename.replace(".gds", _CHECKPOINT_SUFFIX))
    result_path = str(OUTPUT_DIR / _RESULT_FILENAME)

    if parameter_file is None:
        parameter_file = str(PARAMS_JSON)
    if not Path(parameter_file).exists():
        return {"error": f"Parameter JSON not found: {parameter_file}"}

    for p in [result_path]:
        if os.path.exists(p):
            os.remove(p)

    _log.info("=== Industrial Layout Generation START (subprocess) ===")
    _log.info("Worker: %s", _WORKER_SCRIPT)
    _log.info("Output: %s | Timeout: %ds", output_path, timeout)
    t0 = time.time()

    log_path = str(OUTPUT_DIR / "_layout_worker.log")

    cmd = [
        sys.executable,
        str(_WORKER_SCRIPT),
        parameter_file,
        output_path,
        checkpoint_path,
        result_path,
        log_path,
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        )
        exit_code = _wait_for_process(proc, timeout)
    except Exception as exc:
        _log.error("Failed to launch subprocess: %s", exc)
        return {"error": f"Subprocess launch failed: {exc}"}

    elapsed = time.time() - t0

    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            for line in lines[-40:]:
                _log.info("[worker] %s", line.rstrip())
        except Exception:
            pass

    _log.info("Subprocess exited: code=%s, elapsed=%.1f s", exit_code, elapsed)

    # ---------- Read result from worker ----------
    worker_result = None
    if os.path.exists(result_path):
        try:
            with open(result_path, "r", encoding="utf-8") as f:
                worker_result = json.load(f)
        except Exception:
            pass
        finally:
            try:
                os.remove(result_path)
            except OSError:
                pass

    # ---------- Happy path: worker succeeded ----------
    if worker_result and worker_result.get("success"):
        stats = worker_result["stats"]
        return {
            "success": True,
            "gds_file": worker_result["gds_file"],
            "file_size_bytes": worker_result["file_size_bytes"],
            "backend": "qiskit_metal_industrial",
            "chip_name": "CT20QV2_01",
            "chip_size_mm": [13, 13],
            "total_components": stats["total"],
            "qubits": stats["qubits"],
            "couplers": stats["couplers"],
            "meanders": stats["meanders"],
            "readout_lines": stats["readout_lines"],
            "launchpads": stats["launchpads"],
            "skipped_routes": worker_result.get("skipped_routes", []),
            "skipped_count": len(worker_result.get("skipped_routes", [])),
            "elapsed_seconds": round(elapsed, 1),
            "note": (
                f"Industrial-grade GDS generated LIVE from team layout code "
                f"({stats['total']} components, {len(worker_result.get('skipped_routes', []))} "
                f"routes skipped). NoopGUI + SafeRoutePathfinder."
            ),
        }

    # ---------- Fallback: use checkpoint GDS ----------
    has_checkpoint = os.path.exists(checkpoint_path)
    if has_checkpoint:
        import shutil
        shutil.copy2(checkpoint_path, output_path)
        file_size = os.path.getsize(output_path)
        crash_reason = _describe_exit(exit_code, worker_result, timeout)

        _log.warning("Using checkpoint GDS (subprocess %s). Size: %s bytes",
                     crash_reason, f"{file_size:,}")

        return {
            "success": True,
            "gds_file": output_path,
            "file_size_bytes": file_size,
            "backend": "qiskit_metal_industrial_checkpoint",
            "chip_name": "CT20QV2_01",
            "chip_size_mm": [13, 13],
            "skipped_routes": (worker_result or {}).get("skipped_routes", []),
            "elapsed_seconds": round(elapsed, 1),
            "note": (
                f"Intermediate checkpoint GDS (meanders + qubits + couplers, "
                f"exported before routing phase). Subprocess {crash_reason}. "
                f"Core chip structure intact; routing lines not included."
            ),
            "fallback_reason": crash_reason,
        }

    # ---------- Total failure ----------
    error_msg = _describe_exit(exit_code, worker_result, timeout)

    return {
        "error": error_msg,
        "exit_code": exit_code,
        "elapsed_seconds": round(elapsed, 1),
        "skipped_routes": (worker_result or {}).get("skipped_routes", []),
        "worker_error": (worker_result or {}).get("error"),
    }


def _wait_for_process(proc, timeout):
    """Wait for subprocess with timeout, using poll loop instead of
    communicate() to avoid hanging on Windows when child segfaults."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        code = proc.poll()
        if code is not None:
            return code
        time.sleep(2)
    _log.warning("Subprocess timed out after %ds — killing", timeout)
    proc.kill()
    try:
        proc.wait(timeout=15)
    except Exception:
        pass
    return None


def _describe_exit(exit_code, worker_result, timeout):
    if worker_result and "error" in worker_result:
        return worker_result["error"]
    if exit_code is None:
        return f"timed out after {timeout}s"
    if exit_code == -1073741819:
        return "crashed (memory access violation / segfault in C code)"
    if exit_code != 0:
        return f"exited with code {exit_code}"
    return "unknown error"
