#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def probe_json(url: str, timeout: float) -> Dict[str, Any]:
    req = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(raw) if raw else {}
            return {"ok": True, "code": int(resp.getcode()), "payload": payload}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:  # noqa: BLE001
            payload = {"raw": raw}
        return {"ok": False, "code": int(exc.code), "payload": payload}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "code": None, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 rollback drill (dry-run).")
    parser.add_argument("--v1-base", default="http://127.0.0.1:18789")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--output", default="docs/reports/phase7_rollback_drill_latest.json")
    args = parser.parse_args()

    v1 = probe_json(args.v1_base.rstrip("/") + "/api/v1/status", timeout=args.timeout)
    v2 = probe_json(args.v2_base.rstrip("/") + "/health", timeout=args.timeout)

    # Dry-run policy:
    # - rollback-precheck succeeds when V1 is healthy/available
    # - V2 may be healthy or degraded/down; this script only validates fallback path readiness
    rollback_ready = bool(v1.get("ok"))
    report = {
        "timestamp": utc_now_iso(),
        "v1_probe": v1,
        "v2_probe": v2,
        "rollback_ready": rollback_ready,
        "playbook": [
            "1) freeze V2 traffic switch flag",
            "2) route client base URL to V1 gateway",
            "3) run V1 smoke checks (/api/v1/status, /api/v1/library/stats, /api/v1/pipelines)",
            "4) notify users and keep V2 diagnostics for postmortem",
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[phase7-rollback] ready={rollback_ready} report={output}")
    return 0 if rollback_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
