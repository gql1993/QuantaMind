#!/usr/bin/env python
"""
Standalone worker script for industrial layout generation.
Called via subprocess.Popen by industrial_layout_runner.py.

Usage:
    python _layout_worker.py <param_json> <output_gds> <checkpoint_gds> <result_json> [log_path]
"""

import os
import sys
import time
import json
import logging
import traceback

os.environ["QT_QPA_PLATFORM"] = "offscreen"

_log_path = sys.argv[5] if len(sys.argv) > 5 else None
_handlers = []
if _log_path:
    _handlers.append(logging.FileHandler(_log_path, mode="w", encoding="utf-8"))
_handlers.append(logging.StreamHandler(sys.stderr))

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
    handlers=_handlers,
)
log = logging.getLogger("layout_worker")

LAYOUT_MODULE_PATH = os.path.join(os.path.dirname(__file__), "layout_CT20QV2_01.py")


# ---- NoopGUI (Plan B) ----

class _NoopGUI:
    def __init__(self, design):
        self.design = design

    def rebuild(self, autoscale=False):
        self.design.rebuild()

    def __getattr__(self, name):
        return lambda *a, **kw: None


# ---- GDS export helper ----

def _export_gds(design, output_path):
    """Export DesignPlanar to GDS with cheese/no-cheese disabled to avoid
    bounding-box and gdstk type errors."""
    from qiskit_metal.renderers.renderer_gds.gds_renderer import QGDSRenderer
    from qiskit_metal import Dict

    design.rebuild()
    renderer = QGDSRenderer(design)

    renderer.options.no_cheese.view_in_file = Dict(main={})
    renderer.options.cheese.view_in_file = Dict(main={})

    ok = renderer.export_to_gds(output_path)
    if ok != 1:
        raise RuntimeError("QGDSRenderer.export_to_gds returned 0")
    return os.path.getsize(output_path)


# ---- Main ----

def main():
    if len(sys.argv) < 5:
        print("Usage: _layout_worker.py <param_json> <output_gds> <checkpoint_gds> <result_json>",
              file=sys.stderr)
        sys.exit(1)

    parameter_file = sys.argv[1]
    output_path = sys.argv[2]
    checkpoint_path = sys.argv[3]
    result_path = sys.argv[4]

    MAX_FAILURES = 2    # stop routing after this many failures

    skipped_routes = []
    _first_route_call = [True]
    _OrigRP = [None]
    _route_count = [0]
    _fail_count = [0]
    _skip_all = [False]

    # ---- SafeRoutePathfinder (Plan A) with checkpoints ----

    def _save_checkpoint(design, label=""):
        try:
            _export_gds(design, checkpoint_path)
            sz = os.path.getsize(checkpoint_path)
            log.info("Checkpoint saved%s: %s (%s bytes)", label, checkpoint_path, f"{sz:,}")
        except Exception as e:
            log.warning("Checkpoint export failed: %s", e)

    def _safe_rpf(design, name, *args, **kwargs):
        _route_count[0] += 1

        if _first_route_call[0]:
            _first_route_call[0] = False
            log.info(">>> Saving pre-routing checkpoint GDS <<<")
            _save_checkpoint(design, " (pre-routing)")

        if _skip_all[0]:
            skipped_routes.append({"name": name, "error": "skipped (routing halted)"})
            return None

        log.info("RoutePathfinder #%d: '%s' ...", _route_count[0], name)
        t0 = time.time()
        try:
            result = _OrigRP[0](design, name, *args, **kwargs)
            dt = time.time() - t0
            log.info("  '%s' completed in %.1f s", name, dt)
            return result
        except Exception as exc:
            dt = time.time() - t0
            _fail_count[0] += 1
            log.warning("  '%s' failed after %.1f s — skipped (%d/%d): %s",
                        name, dt, _fail_count[0], MAX_FAILURES, exc)
            skipped_routes.append({"name": name, "error": str(exc)})
            if name in design.components:
                try:
                    design.delete_component(name)
                except Exception:
                    pass
            if _fail_count[0] >= MAX_FAILURES:
                log.warning(">>> %d failures reached — halting all remaining routes. "
                            "Saving post-readout checkpoint. <<<", _fail_count[0])
                _skip_all[0] = True
                _save_checkpoint(design, " (post-readout)")
            return None

    # ---- Import & patch layout module ----
    t0 = time.time()
    try:
        import importlib.util
        mod_name = "quantamind.server.layout_CT20QV2_01"
        spec = importlib.util.spec_from_file_location(mod_name, LAYOUT_MODULE_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)

        _OrigRP[0] = mod.RoutePathfinder
        mod.MetalGUI = _NoopGUI
        mod.RoutePathfinder = _safe_rpf
        log.info("Patched MetalGUI -> NoopGUI, RoutePathfinder -> safe wrapper")
    except Exception as exc:
        _write_result(result_path, {"error": f"Import failed: {exc}",
                                    "traceback": traceback.format_exc()})
        sys.exit(2)

    # ---- Run layout ----
    try:
        log.info("Calling twenty_qubits_tunable_coupler_layout() ...")
        design, gui = mod.twenty_qubits_tunable_coupler_layout(
            parameter_file_path=parameter_file
        )
        layout_time = time.time() - t0
        log.info("Layout completed in %.1f s", layout_time)
    except Exception as exc:
        layout_time = time.time() - t0
        log.error("Layout failed: %s", exc, exc_info=True)
        _write_result(result_path, {
            "error": f"Layout failed: {exc}",
            "skipped_routes": skipped_routes,
            "elapsed_seconds": round(layout_time, 1),
            "checkpoint_available": os.path.exists(checkpoint_path),
        })
        sys.exit(3)

    # ---- Component stats ----
    comp_names = list(design.components.keys())
    stats = {
        "total": len(comp_names),
        "qubits": sum(1 for c in comp_names if c.startswith("xmon_round")),
        "couplers": sum(1 for c in comp_names if c.startswith("tunable_coupler")),
        "meanders": sum(1 for c in comp_names if c.startswith("meander")),
        "readout_lines": sum(1 for c in comp_names if c.startswith("readout_line")),
        "launchpads": sum(1 for c in comp_names if c.startswith("launch_line")),
    }
    log.info("Components: %s", stats)

    # ---- Export final GDS ----
    try:
        log.info("Exporting final GDS to %s ...", output_path)
        file_size = _export_gds(design, output_path)
        log.info("Final GDS: %s (%s bytes)", output_path, f"{file_size:,}")
    except Exception as exc:
        log.error("Final GDS export failed: %s", exc, exc_info=True)
        _write_result(result_path, {
            "error": f"GDS export failed: {exc}",
            "stats": stats,
            "skipped_routes": skipped_routes,
            "elapsed_seconds": round(time.time() - t0, 1),
            "checkpoint_available": os.path.exists(checkpoint_path),
        })
        sys.exit(4)

    _write_result(result_path, {
        "success": True,
        "gds_file": output_path,
        "file_size_bytes": file_size,
        "stats": stats,
        "skipped_routes": skipped_routes,
        "elapsed_seconds": round(time.time() - t0, 1),
    })
    log.info("=== DONE (%.1f s) ===", time.time() - t0)


def _write_result(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    main()
