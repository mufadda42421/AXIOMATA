"""A minimal synchronous event bus used to decouple UI panels from logic.

Events are delivered synchronously in the publishing thread. For expensive work,
callers should publish completion events from the worker thread via Qt signals
(see ``services``), but simple state-change notifications stay here.
"""
from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any, Callable

Handler = Callable[..., Any]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._lock = threading.RLock()

    def subscribe(self, event: str, handler: Handler) -> Callable[[], None]:
        with self._lock:
            self._handlers[event].append(handler)

        def _unsubscribe() -> None:
            with self._lock:
                if handler in self._handlers[event]:
                    self._handlers[event].remove(handler)

        return _unsubscribe

    def publish(self, event: str, *args: Any, **kwargs: Any) -> None:
        with self._lock:
            handlers = list(self._handlers.get(event, ()))
        for handler in handlers:
            handler(*args, **kwargs)

    def clear(self) -> None:
        with self._lock:
            self._handlers.clear()


# Frequently used event names centralised to avoid typos.
class Events:
    PROJECT_CREATED = "project.created"
    PROJECT_OPENED = "project.opened"
    PROJECT_CLOSED = "project.closed"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    PROJECT_LIST_CHANGED = "project.list_changed"
    EXPERIMENT_CREATED = "experiment.created"
    SETTINGS_CHANGED = "settings.changed"
    PROFESSION_CHANGED = "profession.changed"
    LOG_MESSAGE = "log.message"
    NAVIGATION_REQUESTED = "navigation.requested"