"""
Type-safe event bus for Q-EDA.

Provides decoupled communication between layers (UI ↔ Application ↔ Core ↔ QuantaMind).
Supports synchronous and asynchronous handlers, priority ordering, and event filtering.

Design principles:
  - Events are immutable dataclass instances
  - Handlers are weakly referenced to avoid memory leaks from UI components
  - Thread-safe for cross-thread signaling (UI thread ↔ sidecar thread)
"""

from __future__ import annotations

import asyncio
import threading
import weakref
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Callable, Generic, TypeVar
from uuid import uuid4

T = TypeVar("T", bound="Event")


class EventPriority(IntEnum):
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200


@dataclass(frozen=True)
class Event:
    """Base event class. All Q-EDA events inherit from this."""

    event_id: str = field(default_factory=lambda: uuid4().hex[:12])
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = ""


# --- Design Events ---

@dataclass(frozen=True)
class DesignCreatedEvent(Event):
    design_name: str = ""
    project_id: str = ""


@dataclass(frozen=True)
class DesignModifiedEvent(Event):
    design_name: str = ""
    modification_type: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComponentAddedEvent(Event):
    component_id: str = ""
    component_type: str = ""
    position: tuple[float, float] = (0.0, 0.0)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComponentModifiedEvent(Event):
    component_id: str = ""
    changes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComponentRemovedEvent(Event):
    component_id: str = ""


# --- Canvas Events ---

@dataclass(frozen=True)
class CanvasSelectionChanged(Event):
    selected_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanvasViewChanged(Event):
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0


# --- Simulation Events ---

@dataclass(frozen=True)
class SimulationSubmitted(Event):
    job_id: str = ""
    sim_type: str = ""


@dataclass(frozen=True)
class SimulationProgress(Event):
    job_id: str = ""
    progress: float = 0.0
    message: str = ""


@dataclass(frozen=True)
class SimulationCompleted(Event):
    job_id: str = ""
    success: bool = True
    result_path: str = ""


# --- QuantaMind Events ---

@dataclass(frozen=True)
class QuantaMindConnected(Event):
    session_id: str = ""


@dataclass(frozen=True)
class QuantaMindDisconnected(Event):
    reason: str = ""


@dataclass(frozen=True)
class QuantaMindToolCallEvent(Event):
    agent: str = ""
    tool: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""


@dataclass(frozen=True)
class QuantaMindMessageEvent(Event):
    content: str = ""
    agent: str = ""
    message_type: str = "content"


# --- Code Sync Events ---

@dataclass(frozen=True)
class CodeChangedEvent(Event):
    """Code editor content changed."""
    code: str = ""
    change_source: str = ""  # "user", "agent", "canvas"


@dataclass(frozen=True)
class CanvasDrivenCodeUpdate(Event):
    """Canvas interaction triggered a code update."""
    target: str = ""
    action: str = ""
    params: dict[str, Any] = field(default_factory=dict)


# --- Subscription ---

@dataclass
class _Subscription:
    callback: Any  # weakref or strong ref
    priority: EventPriority
    is_weak: bool
    is_async: bool

    def alive(self) -> bool:
        if self.is_weak:
            return self.callback() is not None
        return True

    def get_callback(self) -> Callable | None:
        if self.is_weak:
            return self.callback()
        return self.callback


class EventBus:
    """
    Central event bus supporting both sync and async handlers.

    Thread-safe for publishing events from background threads
    (e.g., sidecar, simulation workers).
    """

    def __init__(self) -> None:
        self._subscribers: dict[type[Event], list[_Subscription]] = {}
        self._lock = threading.RLock()
        self._global_handlers: list[_Subscription] = []

    def subscribe(
        self,
        event_type: type[T],
        handler: Callable[[T], Any],
        priority: EventPriority = EventPriority.NORMAL,
        weak: bool = False,
    ) -> Callable[[], None]:
        """
        Subscribe to an event type. Returns an unsubscribe function.

        Args:
            event_type: The event class to listen for.
            handler: Callback invoked when the event fires.
            priority: Higher priority handlers run first.
            weak: If True, store a weak reference (useful for UI components).
        """
        is_async = asyncio.iscoroutinefunction(handler)

        if weak:
            ref = weakref.WeakMethod(handler) if hasattr(handler, "__self__") else weakref.ref(handler)
            sub = _Subscription(callback=ref, priority=priority, is_weak=True, is_async=is_async)
        else:
            sub = _Subscription(callback=handler, priority=priority, is_weak=False, is_async=is_async)

        with self._lock:
            subs = self._subscribers.setdefault(event_type, [])
            subs.append(sub)
            subs.sort(key=lambda s: s.priority, reverse=True)

        def unsubscribe() -> None:
            with self._lock:
                if event_type in self._subscribers:
                    try:
                        self._subscribers[event_type].remove(sub)
                    except ValueError:
                        pass

        return unsubscribe

    def subscribe_all(
        self,
        handler: Callable[[Event], Any],
        priority: EventPriority = EventPriority.NORMAL,
    ) -> Callable[[], None]:
        """Subscribe to ALL events (useful for logging, debugging)."""
        is_async = asyncio.iscoroutinefunction(handler)
        sub = _Subscription(callback=handler, priority=priority, is_weak=False, is_async=is_async)

        with self._lock:
            self._global_handlers.append(sub)
            self._global_handlers.sort(key=lambda s: s.priority, reverse=True)

        def unsubscribe() -> None:
            with self._lock:
                try:
                    self._global_handlers.remove(sub)
                except ValueError:
                    pass

        return unsubscribe

    def publish(self, event: Event) -> None:
        """
        Publish an event synchronously. Async handlers are scheduled on the running loop.
        """
        with self._lock:
            typed_subs = list(self._subscribers.get(type(event), []))
            global_subs = list(self._global_handlers)

        all_subs = sorted(typed_subs + global_subs, key=lambda s: s.priority, reverse=True)

        for sub in all_subs:
            if not sub.alive():
                continue
            cb = sub.get_callback()
            if cb is None:
                continue
            try:
                if sub.is_async:
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(cb(event))
                    except RuntimeError:
                        asyncio.run(cb(event))
                else:
                    cb(event)
            except Exception:
                import traceback
                traceback.print_exc()

        self._gc_dead_refs()

    async def publish_async(self, event: Event) -> None:
        """Publish an event, awaiting all async handlers."""
        with self._lock:
            typed_subs = list(self._subscribers.get(type(event), []))
            global_subs = list(self._global_handlers)

        all_subs = sorted(typed_subs + global_subs, key=lambda s: s.priority, reverse=True)

        for sub in all_subs:
            if not sub.alive():
                continue
            cb = sub.get_callback()
            if cb is None:
                continue
            try:
                if sub.is_async:
                    await cb(event)
                else:
                    cb(event)
            except Exception:
                import traceback
                traceback.print_exc()

        self._gc_dead_refs()

    def _gc_dead_refs(self) -> None:
        """Remove dead weak-reference subscriptions."""
        with self._lock:
            for event_type in list(self._subscribers):
                self._subscribers[event_type] = [
                    s for s in self._subscribers[event_type] if s.alive()
                ]
            self._global_handlers = [s for s in self._global_handlers if s.alive()]

    def clear(self) -> None:
        """Remove all subscriptions."""
        with self._lock:
            self._subscribers.clear()
            self._global_handlers.clear()


# Singleton event bus
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus singleton."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
