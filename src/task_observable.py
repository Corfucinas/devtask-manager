"""Observable properties for reactive updates."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ChangeEvent:
    """Emitted when an observable value changes."""
    key: str
    old_value: Any
    new_value: Any
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class Observable:
    """A container of observable values with change listeners."""
    def __init__(self, initial: Dict = None):
        self._values: Dict[str, Any] = dict(initial or {})
        self._listeners: Dict[str, List[Callable]] = {}
        self._any_listeners: List[Callable] = []
        self._history: List[ChangeEvent] = []
        self._batching = False
        self._pending: List[ChangeEvent] = []

    def get(self, key: str, default=None) -> Any:
        return self._values.get(key, default)

    def set(self, key: str, value: Any):
        old = self._values.get(key)
        if old == value:
            return
        self._values[key] = value
        event = ChangeEvent(key=key, old_value=old, new_value=value)
        if self._batching:
            self._pending.append(event)
        else:
            self._notify(event)

    def _notify(self, event: ChangeEvent):
        self._history.append(event)
        for listener in self._listeners.get(event.key, []):
            try:
                listener(event)
            except Exception:
                pass
        for listener in self._any_listeners:
            try:
                listener(event)
            except Exception:
                pass

    def on(self, key: str, listener: Callable):
        self._listeners.setdefault(key, []).append(listener)

    def on_any(self, listener: Callable):
        self._any_listeners.append(listener)

    def batch(self):
        self._batching = True

    def commit(self):
        self._batching = False
        pending, self._pending = self._pending, []
        for event in pending:
            self._notify(event)

    def keys(self) -> List[str]:
        return sorted(self._values.keys())

    def to_dict(self) -> Dict:
        return dict(self._values)

    def history(self, key: str = None) -> List[ChangeEvent]:
        if key:
            return [e for e in self._history if e.key == key]
        return list(self._history)

    def change_count(self, key: str = None) -> int:
        return len(self.history(key))

    def clear_history(self):
        self._history.clear()


def observable_report(obs: Observable) -> Dict:
    return {"keys": obs.keys(), "total_changes": obs.change_count(),
            "values": obs.to_dict()}
