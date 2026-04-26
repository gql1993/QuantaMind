#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict[str, Any]:
    p = ROOT / path
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 10 export audit bundle.")
    parser.add_argument("--bundle-id", default=datetime.now().strftime("%Y%m%d"))
    parser.add_argument("--manifest-template", default="docs/templates/Phase10_审计导出清单模板.json")
    parser.add_argument("--output-root", default="docs/reports/phase10_audit_bundle")
    args = parser.parse_args()

    tmpl = load_json(args.manifest_template)
    patterns = tmpl.get("include_patterns") if isinstance(tmpl.get("include_patterns"), list) else []
    output_dir = ROOT / args.output_root / args.bundle_id
    output_dir.mkdir(parents=True, exist_ok=True)

    exported = []
    for pattern in patterns:
        for src in ROOT.glob(pattern):
            if not src.is_file():
                continue
            rel = src.relative_to(ROOT)
            dst = output_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            exported.append(str(rel).replace("\\", "/"))

    manifest = {
        "bundle_id": args.bundle_id,
        "timestamp": datetime.now().isoformat(),
        "export_root": str(output_dir.relative_to(ROOT)).replace("\\", "/"),
        "count": len(exported),
        "files": exported,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[phase10-audit-export] bundle={args.bundle_id} count={len(exported)} root={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
