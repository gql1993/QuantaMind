#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quantamind_v2.client.desktop import DesktopWorkspaceShell


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase13 desktop workspace snapshot for V2.")
    parser.add_argument("--gateway-base", default="http://127.0.0.1:18790")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--output", default="docs/reports/phase13_desktop_workspace_latest.json")
    args = parser.parse_args()

    shell = DesktopWorkspaceShell(args.gateway_base, timeout=args.timeout)
    snapshot = shell.collect_snapshot()
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"[phase13-desktop] health_ok={snapshot.health_ok} running_runs={snapshot.running_runs} "
        f"pending_approvals={snapshot.pending_approvals} output={output}"
    )
    return 0 if snapshot.health_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
