"""
Component library service.

Manages the parameterized component library: built-in components,
user-defined components, and sync with QuantaMind's Memory knowledge graph.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from quantamind.server.qeda_models.component import (
    CPW_RESONATOR,
    ComponentCategory,
    ComponentDefinition,
    TUNABLE_COUPLER,
    XMON_TRANSMON,
)


class ComponentService:
    """
    Service for the component library.

    Components are indexed by ID and searchable by category, name, and tags.
    """

    def __init__(self) -> None:
        self._components: dict[str, ComponentDefinition] = {}

    def load_builtin_components(self) -> None:
        """Register the built-in component definitions."""
        for comp in [XMON_TRANSMON, CPW_RESONATOR, TUNABLE_COUPLER]:
            self.register(comp)
        logger.info("Loaded {} built-in components", len(self._components))

    def register(self, component: ComponentDefinition) -> None:
        self._components[component.component_id] = component

    def get(self, component_id: str) -> ComponentDefinition | None:
        return self._components.get(component_id)

    def get_by_name(self, name: str) -> ComponentDefinition | None:
        for comp in self._components.values():
            if comp.name == name:
                return comp
        return None

    def search(
        self,
        category: Optional[ComponentCategory] = None,
        keyword: str = "",
        tags: Optional[list[str]] = None,
    ) -> list[ComponentDefinition]:
        results = list(self._components.values())

        if category:
            results = [c for c in results if c.category == category]

        if keyword:
            kw = keyword.lower()
            results = [
                c for c in results
                if kw in c.name.lower() or kw in c.description.lower()
            ]

        if tags:
            tag_set = set(t.lower() for t in tags)
            results = [
                c for c in results
                if tag_set & set(t.lower() for t in c.tags)
            ]

        return results

    def list_all(self) -> list[ComponentDefinition]:
        return list(self._components.values())

    def list_categories(self) -> list[str]:
        return sorted(set(c.category.value for c in self._components.values()))

    @property
    def count(self) -> int:
        return len(self._components)
