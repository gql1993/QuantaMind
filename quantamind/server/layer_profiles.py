"""
Process layer profiles for GDS/OASIS export.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessLayerProfile:
    name: str
    ground_plane: int
    metal: int
    junction: int
    bandage: int
    etch: int
    airbridge: int
    readout: int
    marker: int = 7
    fake_junction: int = 8
    text: int = 9
    chip_edge: int = 10

    def map_logical(self, logical_layer: int) -> int:
        return {
            0: self.ground_plane,
            1: self.metal,
            2: self.junction,
            3: self.bandage,
            4: self.airbridge,
            5: self.readout,
            6: self.etch,
            7: self.marker,
            8: self.fake_junction,
            9: self.text,
            10: self.chip_edge,
        }.get(logical_layer, self.metal)

    def role_layer(self, role: str) -> int:
        role_key = role.strip().lower()
        return {
            "ground": self.ground_plane,
            "ground_plane": self.ground_plane,
            "metal": self.metal,
            "trace": self.metal,
            "junction": self.junction,
            "bandage": self.bandage,
            "etch": self.etch,
            "subtract": self.etch,
            "airbridge": self.airbridge,
            "readout": self.readout,
            "marker": self.marker,
            "fake_junction": self.fake_junction,
            "text": self.text,
            "chip_edge": self.chip_edge,
        }.get(role_key, self.metal)


DEFAULT_PROFILE = ProcessLayerProfile(
    name="default",
    ground_plane=0,
    metal=1,
    junction=2,
    bandage=3,
    airbridge=4,
    readout=5,
    etch=6,
    marker=7,
    fake_junction=8,
    text=9,
    chip_edge=10,
)


FT105_PROFILE = ProcessLayerProfile(
    name="ft105",
    ground_plane=24,
    metal=13,
    junction=14,
    bandage=12,
    airbridge=27,
    readout=11,
    etch=21,
    marker=26,
    fake_junction=20,
    text=10,
    chip_edge=26,
)


def get_process_layer_profile(name: str = "default") -> ProcessLayerProfile:
    key = (name or "default").strip().lower()
    if key in {"ft105", "real105", "ft105q"}:
        return FT105_PROFILE
    return DEFAULT_PROFILE
