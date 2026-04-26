"""
Physical unit conversion utilities for quantum chip design.

All internal calculations use SI base units (meters, Hz, seconds).
Display and user input can use convenient units (um, GHz, ns).
"""

from __future__ import annotations

from enum import Enum
from typing import Union

Numeric = Union[int, float]


class LengthUnit(str, Enum):
    NM = "nm"
    UM = "um"
    MM = "mm"
    M = "m"


class FrequencyUnit(str, Enum):
    HZ = "Hz"
    KHZ = "kHz"
    MHZ = "MHz"
    GHZ = "GHz"


class TimeUnit(str, Enum):
    S = "s"
    MS = "ms"
    US = "us"
    NS = "ns"


_LENGTH_TO_M: dict[LengthUnit, float] = {
    LengthUnit.NM: 1e-9,
    LengthUnit.UM: 1e-6,
    LengthUnit.MM: 1e-3,
    LengthUnit.M: 1.0,
}

_FREQ_TO_HZ: dict[FrequencyUnit, float] = {
    FrequencyUnit.HZ: 1.0,
    FrequencyUnit.KHZ: 1e3,
    FrequencyUnit.MHZ: 1e6,
    FrequencyUnit.GHZ: 1e9,
}

_TIME_TO_S: dict[TimeUnit, float] = {
    TimeUnit.S: 1.0,
    TimeUnit.MS: 1e-3,
    TimeUnit.US: 1e-6,
    TimeUnit.NS: 1e-9,
}


def to_meters(value: Numeric, unit: LengthUnit | str) -> float:
    unit = LengthUnit(unit) if isinstance(unit, str) else unit
    return float(value) * _LENGTH_TO_M[unit]


def from_meters(value: Numeric, unit: LengthUnit | str) -> float:
    unit = LengthUnit(unit) if isinstance(unit, str) else unit
    return float(value) / _LENGTH_TO_M[unit]


def to_hz(value: Numeric, unit: FrequencyUnit | str) -> float:
    unit = FrequencyUnit(unit) if isinstance(unit, str) else unit
    return float(value) * _FREQ_TO_HZ[unit]


def from_hz(value: Numeric, unit: FrequencyUnit | str) -> float:
    unit = FrequencyUnit(unit) if isinstance(unit, str) else unit
    return float(value) / _FREQ_TO_HZ[unit]


def to_seconds(value: Numeric, unit: TimeUnit | str) -> float:
    unit = TimeUnit(unit) if isinstance(unit, str) else unit
    return float(value) * _TIME_TO_S[unit]


def from_seconds(value: Numeric, unit: TimeUnit | str) -> float:
    unit = TimeUnit(unit) if isinstance(unit, str) else unit
    return float(value) / _TIME_TO_S[unit]


def parse_length(text: str) -> float:
    """Parse a string like '10mm' or '500 um' into meters."""
    text = text.strip().lower()
    for unit in sorted(_LENGTH_TO_M, key=lambda u: len(u.value), reverse=True):
        if text.endswith(unit.value):
            num = text[: -len(unit.value)].strip()
            return to_meters(float(num), unit)
    return float(text)


def parse_frequency(text: str) -> float:
    """Parse a string like '5.5GHz' or '200 MHz' into Hz."""
    text = text.strip()
    for unit in sorted(_FREQ_TO_HZ, key=lambda u: len(u.value), reverse=True):
        if text.lower().endswith(unit.value.lower()):
            num = text[: -len(unit.value)].strip()
            return to_hz(float(num), unit)
    return float(text)
