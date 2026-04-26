"""
Design service: business logic for creating, managing, and persisting designs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from quantamind.server.events import DesignCreatedEvent, DesignModifiedEvent, get_event_bus
from quantamind.server.qeda_models.component import ComponentInstance
from quantamind.server.qeda_models.design import Design, DesignMetadata, DesignState, RoutingSegment
from quantamind.server.qeda_models.topology import Topology, TopologyType


class DesignService:
    """
    Service layer for design operations.

    Manages the lifecycle of Design objects and coordinates
    between the UI, Core Engine, and persistence layers.
    """

    def __init__(self) -> None:
        self._designs: dict[str, Design] = {}
        self._active_design_id: Optional[str] = None

    @property
    def active_design(self) -> Design | None:
        if self._active_design_id:
            return self._designs.get(self._active_design_id)
        return None

    def create_design(
        self,
        name: str,
        topology_type: TopologyType = TopologyType.CUSTOM,
        num_qubits: int = 0,
        grid_rows: int = 0,
        grid_cols: int = 0,
        **kwargs: Any,
    ) -> Design:
        """Create a new design with optional topology pre-generation."""
        topology: Topology
        if topology_type == TopologyType.GRID and grid_rows > 0 and grid_cols > 0:
            topology = Topology.create_grid(grid_rows, grid_cols, name=f"{name}_topo")
        elif topology_type == TopologyType.LINEAR and num_qubits > 0:
            topology = Topology.create_linear(num_qubits, name=f"{name}_topo")
        else:
            topology = Topology(name=f"{name}_topo", topology_type=topology_type)

        metadata = DesignMetadata(
            description=kwargs.get("description", ""),
            chip_size_x_mm=kwargs.get("chip_size_x_mm", 10.0),
            chip_size_y_mm=kwargs.get("chip_size_y_mm", 10.0),
        )

        design = Design(
            name=name,
            metadata=metadata,
            topology=topology,
        )

        self._designs[design.design_id] = design
        self._active_design_id = design.design_id

        get_event_bus().publish(DesignCreatedEvent(
            design_name=name,
            source="design_service",
        ))

        logger.info("Created design '{}' (id={})", name, design.design_id)
        return design

    def open_design(self, path: Path | str) -> Design:
        """Load a design from a JSON file."""
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        design = Design.model_validate(data)
        self._designs[design.design_id] = design
        self._active_design_id = design.design_id
        logger.info("Opened design '{}' from {}", design.name, path)
        return design

    def save_design(self, design_id: str | None = None, path: Path | str | None = None) -> Path:
        """Save a design to a JSON file."""
        did = design_id or self._active_design_id
        if did is None:
            raise ValueError("No design to save")
        design = self._designs.get(did)
        if design is None:
            raise KeyError(f"Design '{did}' not found")

        if path is None:
            path = Path(f"projects/{design.name}/{design.name}.qeda.json")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(design.model_dump_json(indent=2))

        logger.info("Saved design '{}' to {}", design.name, path)
        return path

    def add_component(
        self,
        design_id: str | None = None,
        **component_kwargs: Any,
    ) -> ComponentInstance:
        """Add a component instance to a design."""
        design = self._get_design(design_id)
        comp = ComponentInstance(**component_kwargs)
        design.add_component(comp)

        get_event_bus().publish(DesignModifiedEvent(
            design_name=design.name,
            modification_type="add_component",
            details={"component_id": comp.instance_id, "name": comp.name},
            source="design_service",
        ))

        return comp

    def remove_component(self, instance_id: str, design_id: str | None = None) -> bool:
        design = self._get_design(design_id)
        result = design.remove_component(instance_id)
        if result:
            get_event_bus().publish(DesignModifiedEvent(
                design_name=design.name,
                modification_type="remove_component",
                details={"component_id": instance_id},
                source="design_service",
            ))
        return result

    def add_route(
        self,
        source_id: str,
        source_port: str,
        target_id: str,
        target_port: str,
        design_id: str | None = None,
        **kwargs: Any,
    ) -> RoutingSegment:
        design = self._get_design(design_id)
        seg = RoutingSegment(
            source_instance_id=source_id,
            source_port=source_port,
            target_instance_id=target_id,
            target_port=target_port,
            **kwargs,
        )
        design.add_routing(seg)
        return seg

    def set_active(self, design_id: str) -> None:
        if design_id not in self._designs:
            raise KeyError(f"Design '{design_id}' not found")
        self._active_design_id = design_id

    def get_design(self, design_id: str) -> Design | None:
        return self._designs.get(design_id)

    def list_designs(self) -> list[Design]:
        return list(self._designs.values())

    def close_design(self, design_id: str) -> bool:
        if design_id in self._designs:
            del self._designs[design_id]
            if self._active_design_id == design_id:
                self._active_design_id = next(iter(self._designs), None)
            return True
        return False

    def _get_design(self, design_id: str | None) -> Design:
        did = design_id or self._active_design_id
        if did is None:
            raise ValueError("No active design")
        design = self._designs.get(did)
        if design is None:
            raise KeyError(f"Design '{did}' not found")
        return design
