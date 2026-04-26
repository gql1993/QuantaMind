"""
Topology models for quantum chip graph representation.

The chip topology is modeled as a graph: nodes represent quantum elements
(qubits, resonators) and edges represent coupling relationships.
This structure drives frequency allocation, layout, routing, and
the GNN-based surrogate model predictions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _new_id() -> str:
    return uuid4().hex[:8]


class TopologyType(str, Enum):
    LINEAR = "linear"
    GRID = "grid"
    HEAVY_HEX = "heavy_hex"
    SURFACE_CODE = "surface_code"
    CUSTOM = "custom"


class NodeType(str, Enum):
    QUBIT = "qubit"
    RESONATOR = "resonator"
    COUPLER = "coupler"
    ANCILLA = "ancilla"


class EdgeType(str, Enum):
    CAPACITIVE = "capacitive"
    INDUCTIVE = "inductive"
    RESONATOR_MEDIATED = "resonator_mediated"
    DIRECT = "direct"


class Node(BaseModel):
    """A node in the chip topology graph."""
    node_id: str = Field(default_factory=_new_id)
    name: str = ""
    node_type: NodeType = NodeType.QUBIT
    component_instance_id: str = ""
    position_x: float = 0.0
    position_y: float = 0.0
    frequency_hz: Optional[float] = None
    anharmonicity_hz: Optional[float] = None
    t1_us: Optional[float] = None
    t2_us: Optional[float] = None
    properties: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    """An edge (coupling) in the chip topology graph."""
    edge_id: str = Field(default_factory=_new_id)
    source_id: str
    target_id: str
    edge_type: EdgeType = EdgeType.CAPACITIVE
    coupling_strength_hz: Optional[float] = None
    distance_um: Optional[float] = None
    component_instance_id: str = ""
    properties: dict[str, Any] = Field(default_factory=dict)


class FrequencyConstraint(BaseModel):
    """Constraint for frequency allocation."""
    min_frequency_hz: float = 4.5e9
    max_frequency_hz: float = 5.5e9
    min_neighbor_detuning_hz: float = 200e6
    avoid_frequencies_hz: list[float] = Field(default_factory=list)


class Topology(BaseModel):
    """
    Complete chip topology: nodes + edges forming the connectivity graph.

    Used for:
      - Frequency allocation (avoiding collisions)
      - Layout and routing guidance
      - GNN-based global property prediction
      - Surface code / error correction code mapping
    """
    topology_id: str = Field(default_factory=_new_id)
    name: str = ""
    topology_type: TopologyType = TopologyType.CUSTOM
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    grid_rows: Optional[int] = None
    grid_cols: Optional[int] = None
    frequency_constraints: FrequencyConstraint = Field(default_factory=FrequencyConstraint)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_node(self, node_id: str) -> Node | None:
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        return None

    def get_node_by_name(self, name: str) -> Node | None:
        for n in self.nodes:
            if n.name == name:
                return n
        return None

    def neighbors(self, node_id: str) -> list[Node]:
        neighbor_ids: set[str] = set()
        for e in self.edges:
            if e.source_id == node_id:
                neighbor_ids.add(e.target_id)
            elif e.target_id == node_id:
                neighbor_ids.add(e.source_id)
        return [n for n in self.nodes if n.node_id in neighbor_ids]

    def edges_of(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.source_id == node_id or e.target_id == node_id]

    @property
    def num_qubits(self) -> int:
        return sum(1 for n in self.nodes if n.node_type == NodeType.QUBIT)

    def to_adjacency_dict(self) -> dict[str, list[str]]:
        adj: dict[str, list[str]] = {n.node_id: [] for n in self.nodes}
        for e in self.edges:
            adj.setdefault(e.source_id, []).append(e.target_id)
            adj.setdefault(e.target_id, []).append(e.source_id)
        return adj

    @classmethod
    def create_grid(
        cls,
        rows: int,
        cols: int,
        spacing_um: float = 1000.0,
        name: str = "",
    ) -> Topology:
        """Factory: create a rectangular grid topology."""
        nodes: list[Node] = []
        edges: list[Edge] = []
        id_map: dict[tuple[int, int], str] = {}

        for r in range(rows):
            for c in range(cols):
                node = Node(
                    name=f"Q{r * cols + c}",
                    node_type=NodeType.QUBIT,
                    position_x=c * spacing_um * 1e-6,
                    position_y=r * spacing_um * 1e-6,
                )
                nodes.append(node)
                id_map[(r, c)] = node.node_id

        for r in range(rows):
            for c in range(cols):
                if c + 1 < cols:
                    edges.append(Edge(
                        source_id=id_map[(r, c)],
                        target_id=id_map[(r, c + 1)],
                    ))
                if r + 1 < rows:
                    edges.append(Edge(
                        source_id=id_map[(r, c)],
                        target_id=id_map[(r + 1, c)],
                    ))

        return cls(
            name=name or f"{rows}x{cols} Grid",
            topology_type=TopologyType.GRID,
            nodes=nodes,
            edges=edges,
            grid_rows=rows,
            grid_cols=cols,
        )

    @classmethod
    def create_linear(cls, num_qubits: int, spacing_um: float = 1000.0, name: str = "") -> Topology:
        """Factory: create a linear chain topology."""
        nodes = [
            Node(
                name=f"Q{i}",
                node_type=NodeType.QUBIT,
                position_x=i * spacing_um * 1e-6,
            )
            for i in range(num_qubits)
        ]
        edges = [
            Edge(source_id=nodes[i].node_id, target_id=nodes[i + 1].node_id)
            for i in range(num_qubits - 1)
        ]
        return cls(
            name=name or f"{num_qubits}-qubit linear chain",
            topology_type=TopologyType.LINEAR,
            nodes=nodes,
            edges=edges,
        )
