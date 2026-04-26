"""
Q-EDA tool registry for QuantaMind integration.

Registers Q-EDA's local tools (design, simulation, export, DRC) with QuantaMind
Gateway so that AI agents can invoke them via Function Calling.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from quantamind.client.qeda_bridge.protocol import ToolRegistration

logger = logging.getLogger(__name__)

ToolHandler = Callable[..., Any | Awaitable[Any]]


class _ToolEntry:
    def __init__(
        self,
        registration: ToolRegistration,
        handler: ToolHandler,
    ) -> None:
        self.registration = registration
        self.handler = handler


class QEDAToolRegistry:
    """
    Registry of Q-EDA tools that QuantaMind agents can call.

    Tools are registered with metadata (name, description, parameters)
    and a handler function. When QuantaMind sends a tool_call message,
    the client looks up and invokes the corresponding handler.
    """

    def __init__(self) -> None:
        self._tools: dict[str, _ToolEntry] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        category: str = "qeda",
        parameters: dict[str, Any] | None = None,
        requires_approval: bool = False,
    ) -> None:
        reg = ToolRegistration(
            name=name,
            description=description,
            category=category,
            parameters=parameters or {},
            requires_approval=requires_approval,
        )
        self._tools[name] = _ToolEntry(registration=reg, handler=handler)
        logger.debug("Registered tool: %s [%s]", name, category)

    def get_handler(self, tool_name: str) -> ToolHandler | None:
        entry = self._tools.get(tool_name)
        return entry.handler if entry else None

    async def execute(self, tool_name: str, **params: Any) -> Any:
        """Execute a registered tool by name."""
        entry = self._tools.get(tool_name)
        if entry is None:
            raise KeyError(f"Tool '{tool_name}' not registered")

        handler = entry.handler
        if asyncio.iscoroutinefunction(handler):
            return await handler(**params)
        return handler(**params)

    def get_registrations(self) -> list[ToolRegistration]:
        return [e.registration for e in self._tools.values()]

    def get_registration(self, tool_name: str) -> ToolRegistration | None:
        entry = self._tools.get(tool_name)
        return entry.registration if entry else None

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    @property
    def count(self) -> int:
        return len(self._tools)


def create_default_registry() -> QEDAToolRegistry:
    """
    Create the default Q-EDA tool registry with placeholder handlers.

    Real handlers will be wired up by the application bootstrap
    once all services are initialized.
    """
    registry = QEDAToolRegistry()

    design_tools = [
        ("qeda_add_transmon", "Add a transmon qubit to the design canvas"),
        ("qeda_add_xmon", "Add an Xmon qubit to the design canvas"),
        ("qeda_add_resonator", "Add a CPW readout resonator"),
        ("qeda_add_coupler", "Add a coupler between two qubits"),
        ("qeda_add_flux_line", "Add a flux control line to a qubit"),
        ("qeda_add_drive_line", "Add a microwave drive line"),
        ("qeda_add_readout_line", "Add a readout line"),
        ("qeda_add_airbridge", "Add an airbridge crossover"),
        ("qeda_add_launchpad", "Add a launch pad for wirebonding"),
        ("qeda_update_component", "Update component parameters"),
        ("qeda_remove_component", "Remove a component from the design"),
        ("qeda_set_topology", "Set the chip topology (grid, linear, etc.)"),
        ("qeda_allocate_frequencies", "Allocate qubit frequencies avoiding collisions"),
    ]

    for name, desc in design_tools:
        registry.register(name, desc, handler=_placeholder_handler, category="design")

    sim_tools = [
        ("qeda_run_lom", "Run LOM (Lumped Oscillator Model) analysis"),
        ("qeda_run_hfss_eigenmode", "Run HFSS eigenmode simulation"),
        ("qeda_run_q3d_capacitance", "Run Q3D capacitance extraction"),
        ("qeda_run_surrogate_predict", "Run AI surrogate model prediction"),
        ("qeda_run_pyepr_analysis", "Run pyEPR quantum parameter extraction"),
        ("qeda_run_blackbox_quantization", "Run black-box quantization analysis"),
    ]

    for name, desc in sim_tools:
        registry.register(name, desc, handler=_placeholder_handler, category="simulation")

    opt_tools = [
        ("qeda_optimize_layout_rl", "Optimize layout using reinforcement learning"),
        ("qeda_optimize_routing_rl", "Optimize routing using RL/A*"),
        ("qeda_optimize_bayesian", "Run Bayesian multi-parameter optimization"),
        ("qeda_optimize_waveform_grape", "Optimize control waveform using GRAPE"),
    ]

    for name, desc in opt_tools:
        registry.register(name, desc, handler=_placeholder_handler, category="optimization")

    export_tools = [
        ("qeda_run_drc", "Run design rule check"),
        ("qeda_export_gds", "Export design to GDSII format"),
        ("qeda_export_oasis", "Export design to OASIS format"),
        ("qeda_export_report", "Generate design report"),
    ]

    for name, desc in export_tools:
        registry.register(name, desc, handler=_placeholder_handler, category="export")

    logger.info("Default tool registry created with %s tools", registry.count)
    return registry


async def _placeholder_handler(**kwargs: Any) -> dict[str, Any]:
    """Placeholder handler for unimplemented tools."""
    return {
        "status": "not_implemented",
        "message": "This tool is registered but not yet implemented",
        "params_received": kwargs,
    }
