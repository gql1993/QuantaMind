"""
One-off migration: copy QEDA layer files from EDA-Q-main into QuantaMind with import rewiring.
Run from repo root: python scripts/migrate_qeda_layer.py
"""

from __future__ import annotations

import pathlib
import shutil

EDA = pathlib.Path(r"E:\work\EDA-Q-main\qeda")
AQ = pathlib.Path(r"E:\work\QuantaMind\quantamind")

# (source under EDA, destination under quantamind/)
COPIES: list[tuple[str, str]] = [
    ("core/geometry/engine.py", "server/geometry/engine.py"),
    ("core/geometry/gdstk_engine.py", "server/geometry/gdstk_engine.py"),
    ("core/geometry/layer_profiles.py", "server/geometry/layer_profiles.py"),
    ("core/geometry/geometry_cache.py", "server/geometry/geometry_cache.py"),
    ("core/geometry/component_templates.py", "server/geometry/component_templates.py"),
    ("core/geometry/generators.py", "server/geometry/generators.py"),
    ("core/geometry/component_cell_library.py", "server/geometry/component_cell_library.py"),
    ("core/geometry/export_gds.py", "server/geometry/export_gds.py"),
    ("core/geometry/routing_geometry.py", "server/geometry/routing_geometry.py"),
    ("models/simulation.py", "server/qeda_models/simulation.py"),
    ("core/events.py", "server/events.py"),
    ("core/simulation/manager.py", "server/qeda_simulation/manager.py"),
    ("core/simulation/adapters.py", "server/qeda_simulation/adapters.py"),
    ("application/services/simulation_service.py", "server/services/simulation_service.py"),
    ("application/services/external_design_importer.py", "server/services/external_design_importer.py"),
    ("application/services/layout_script_parser.py", "server/services/layout_script_parser.py"),
    ("application/services/design_service.py", "server/services/design_service.py"),
    ("application/services/component_service.py", "server/services/component_service.py"),
    ("core/drc/checker.py", "server/drc/checker.py"),
    ("aetherq/client.py", "client/qeda_bridge/client.py"),
    ("application/api/design.py", "server/sidecar/api/design.py"),
    ("application/api/simulation.py", "server/sidecar/api/simulation.py"),
    ("application/api/export.py", "server/sidecar/api/export.py"),
    ("application/api/system.py", "server/sidecar/api/system.py"),
    ("application/api/aetherq.py", "server/sidecar/api/quantamind.py"),
    ("application/api/components.py", "server/sidecar/api/components.py"),
    ("application/sidecar.py", "server/sidecar/app.py"),
]


def transform(text: str) -> str:
    repl = [
        ("from qeda.models.", "from quantamind.server.qeda_models."),
        ("from qeda.models import", "from quantamind.server.qeda_models import"),
        ("from qeda.utils.units", "from quantamind.server.layout_units"),
        ("from qeda.core.geometry.", "from quantamind.server.geometry."),
        ("from qeda.core.events", "from quantamind.server.events"),
        ("from qeda.core.simulation.manager", "from quantamind.server.qeda_simulation.manager"),
        ("from qeda.core.simulation.adapters", "from quantamind.server.qeda_simulation.adapters"),
        ("from qeda.core.drc.", "from quantamind.server.drc."),
        ("from qeda.application.services.", "from quantamind.server.services."),
        ("from qeda.application.api.", "from quantamind.server.sidecar.api."),
        ("from qeda.aetherq.", "from quantamind.client.qeda_bridge."),
        ("from qeda.config import get_config", "from quantamind.server.qeda_bootstrap import get_qeda_config as get_config"),
        ('"qeda.core.geometry.generators.', '"quantamind.server.geometry.generators.'),
        ("from qeda.core.geometry.export_gds import", "from quantamind.server.geometry.export_gds import"),
        ("from qeda.core.geometry.gdstk_engine import", "from quantamind.server.geometry.gdstk_engine import"),
    ]
    for a, b in repl:
        text = text.replace(a, b)
    return text


def main() -> None:
    for rel_src, rel_dst in COPIES:
        src = EDA / rel_src
        if not src.exists():
            # client lives under qeda/aetherq (upstream folder name)
            if rel_src.startswith("aetherq/"):
                src = EDA / rel_src
            if not src.exists():
                raise FileNotFoundError(src)
        dst = AQ / rel_dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        raw = src.read_text(encoding="utf-8")
        dst.write_text(transform(raw), encoding="utf-8")
        print(f"OK {rel_dst}")
    print("Done.")


if __name__ == "__main__":
    main()
