"""Smoke tests for migrated QEDA modules (EDA-Q-main → QuantaMind)."""

from __future__ import annotations

import numpy as np
import pytest

from quantamind.client.qeda_bridge import QEDAToolRegistry, ToolRegistration, create_default_registry
from quantamind.server.events import EventBus, SimulationProgress, get_event_bus
from quantamind.server.geometry_engine import GeometryResult, Polygon
from quantamind.server.layer_profiles import DEFAULT_PROFILE, get_process_layer_profile
from quantamind.server.layout_units import LengthUnit, to_meters
from quantamind.server.models_simulation import SimulationJob, SimulationType
from quantamind.server.qeda_models import Design, Topology
from quantamind.server.qeda_models.common import Point2D
from quantamind.server.qeda_models.component import ComponentInstance


def test_layout_units() -> None:
    assert to_meters(1, LengthUnit.MM) == pytest.approx(1e-3)


def test_layer_profiles() -> None:
    assert get_process_layer_profile("ft105").name == "ft105"
    assert DEFAULT_PROFILE.map_logical(0) == DEFAULT_PROFILE.ground_plane


def test_geometry_engine_dataclasses() -> None:
    poly = Polygon(vertices=np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]], dtype=np.float64))
    res = GeometryResult(polygons=[poly])
    assert res.bounds is not None


def test_models_simulation() -> None:
    job = SimulationJob(design_id="d1", sim_type=SimulationType.LOM)
    assert job.job_id
    assert job.sim_type == SimulationType.LOM


def test_event_bus_roundtrip() -> None:
    bus = EventBus()
    seen: list[float] = []

    def on_prog(ev: SimulationProgress) -> None:
        seen.append(ev.progress)

    bus.subscribe(SimulationProgress, on_prog)
    bus.publish(SimulationProgress(job_id="j1", progress=0.5, message="ok"))
    assert seen == [0.5]


def test_get_event_bus_singleton() -> None:
    b1 = get_event_bus()
    b2 = get_event_bus()
    assert b1 is b2


def test_qeda_models_design() -> None:
    d = Design(name="demo")
    d.topology = Topology.create_linear(3)
    assert d.topology.num_qubits == 3
    inst = ComponentInstance(definition_id="def1", name="Q0")
    d.add_component(inst)
    assert d.num_components == 1


def test_point2d() -> None:
    a = Point2D(x=1, y=2)
    b = Point2D(x=3, y=4)
    assert (a + b).x == 4


def test_tool_registration_model() -> None:
    r = ToolRegistration(name="t", description="d", category="c")
    assert r.name == "t"


def test_qeda_tool_registry_default() -> None:
    reg = create_default_registry()
    assert reg.count > 0
    assert "qeda_export_gds" in reg.tool_names


@pytest.mark.asyncio
async def test_registry_execute_placeholder() -> None:
    reg = QEDAToolRegistry()

    async def _async_ok(**_: object) -> dict[str, str]:
        return {"ok": "1"}

    reg.register("x", "y", _async_ok)
    out = await reg.execute("x")
    assert out["ok"] == "1"


def test_hands_registers_qeda_bridge() -> None:
    from quantamind.server import hands

    names = {t["name"] for t in hands.list_tools()}
    assert "qeda_bridge_capabilities" in names
    assert "qeda_export_gds" in names


@pytest.mark.asyncio
async def test_hands_qeda_bridge_run_tool() -> None:
    from quantamind.server import hands as h

    out = await h.run_tool("qeda_bridge_capabilities")
    assert out["source"] == "qeda_bridge"
    assert out["count"] >= 1
    out2 = await h.run_tool("qeda_export_gds")
    assert out2.get("status") == "not_implemented"
