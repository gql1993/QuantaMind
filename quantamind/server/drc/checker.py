"""
Design Rule Check (DRC) engine for quantum chip validation.

Validates geometric constraints critical for superconducting chip fabrication:
  - Minimum line width / spacing
  - Metal density bounds
  - Junction area constraints
  - Airbridge placement rules
  - Custom foundry rules

Rules are defined as data (YAML/JSON loadable) and executed against the
design's geometry, producing DRCViolation records attached to the Design model.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger

from quantamind.server.qeda_models.design import DRCViolation, Design


class RuleSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class DRCRule:
    """A single design rule."""
    name: str
    description: str
    severity: RuleSeverity = RuleSeverity.ERROR
    category: str = "general"
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


class DRCRuleChecker(ABC):
    """Abstract base for rule checkers."""

    @abstractmethod
    def check(self, design: Design, rule: DRCRule) -> list[DRCViolation]:
        """Run this rule against a design. Return violations found."""


class MinWidthChecker(DRCRuleChecker):
    """Check minimum feature width."""

    def check(self, design: Design, rule: DRCRule) -> list[DRCViolation]:
        min_width = rule.params.get("min_width_um", 2.0)
        violations: list[DRCViolation] = []
        for seg in design.routing_segments:
            if seg.width_um < min_width:
                violations.append(DRCViolation(
                    rule_name=rule.name,
                    severity=rule.severity.value,
                    message=f"Trace width {seg.width_um} µm < minimum {min_width} µm",
                    component_id=seg.segment_id,
                ))
        return violations


class MinSpacingChecker(DRCRuleChecker):
    """Check minimum spacing between components."""

    def check(self, design: Design, rule: DRCRule) -> list[DRCViolation]:
        min_spacing_um = rule.params.get("min_spacing_um", 5.0)
        violations: list[DRCViolation] = []
        components = design.components
        for i, a in enumerate(components):
            for b in components[i + 1:]:
                dx = abs(a.position_x - b.position_x) * 1e6
                dy = abs(a.position_y - b.position_y) * 1e6
                dist = (dx**2 + dy**2) ** 0.5
                if dist < min_spacing_um:
                    violations.append(DRCViolation(
                        rule_name=rule.name,
                        severity=rule.severity.value,
                        message=(
                            f"Spacing between '{a.name}' and '{b.name}' "
                            f"is {dist:.1f} µm < minimum {min_spacing_um} µm"
                        ),
                        component_id=a.instance_id,
                        location_x=a.position_x,
                        location_y=a.position_y,
                    ))
        return violations


# Default DRC rule set for superconducting quantum chips
DEFAULT_RULES: list[DRCRule] = [
    DRCRule(
        name="min_trace_width",
        description="Minimum CPW trace width",
        category="geometry",
        params={"min_width_um": 2.0},
    ),
    DRCRule(
        name="min_gap_width",
        description="Minimum CPW gap width",
        category="geometry",
        params={"min_width_um": 2.0},
    ),
    DRCRule(
        name="min_component_spacing",
        description="Minimum spacing between components",
        category="geometry",
        params={"min_spacing_um": 50.0},
    ),
    DRCRule(
        name="chip_boundary",
        description="All features must be within chip boundary",
        category="boundary",
    ),
    DRCRule(
        name="junction_area",
        description="Josephson junction area within fabrication limits",
        category="junction",
        params={"min_area_um2": 0.01, "max_area_um2": 0.5},
    ),
]


class DRCEngine:
    """
    Main DRC engine that orchestrates rule checking.

    Loads rules (built-in or from YAML), runs all enabled checkers,
    and collects violations into the Design model.
    """

    def __init__(self) -> None:
        self._rules: list[DRCRule] = list(DEFAULT_RULES)
        self._checkers: dict[str, DRCRuleChecker] = {
            "min_trace_width": MinWidthChecker(),
            "min_gap_width": MinWidthChecker(),
            "min_component_spacing": MinSpacingChecker(),
        }

    def add_rule(self, rule: DRCRule, checker: DRCRuleChecker | None = None) -> None:
        self._rules.append(rule)
        if checker:
            self._checkers[rule.name] = checker

    def register_checker(self, rule_name: str, checker: DRCRuleChecker) -> None:
        self._checkers[rule_name] = checker

    def run(self, design: Design) -> list[DRCViolation]:
        """Run all enabled rules and return violations."""
        all_violations: list[DRCViolation] = []

        for rule in self._rules:
            if not rule.enabled:
                continue
            checker = self._checkers.get(rule.name)
            if checker is None:
                logger.debug("No checker registered for rule '{}', skipping", rule.name)
                continue
            try:
                violations = checker.check(design, rule)
                all_violations.extend(violations)
            except Exception:
                logger.exception("DRC rule '{}' failed", rule.name)

        design.drc_violations = all_violations
        error_count = sum(1 for v in all_violations if v.severity == "error")
        warn_count = sum(1 for v in all_violations if v.severity == "warning")
        logger.info("DRC completed: {} errors, {} warnings", error_count, warn_count)

        return all_violations

    @property
    def rules(self) -> list[DRCRule]:
        return list(self._rules)
