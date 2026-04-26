#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys


def run(cmd: list[str], *, title: str) -> int:
    print(f"[phase6-regression] {title}: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    print(f"[phase6-regression] {title} exit={result.returncode}")
    return int(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 6 regression bundle.")
    parser.add_argument("--v1-base", default="http://127.0.0.1:18789")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest tests/v2")
    parser.add_argument("--skip-baseline", action="store_true", help="Skip baseline API probe")
    args = parser.parse_args()

    failed = 0
    if not args.skip_tests:
        failed += run([sys.executable, "-m", "pytest", "tests/v2", "-q"], title="pytest")
    if not args.skip_baseline:
        failed += run(
            [
                sys.executable,
                "scripts/v1_v2_baseline_regression.py",
                "--v1-base",
                args.v1_base,
                "--v2-base",
                args.v2_base,
            ],
            title="baseline",
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
