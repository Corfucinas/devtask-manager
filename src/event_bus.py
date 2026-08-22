"""Event bus for pub/sub task events."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Event:
    """A single event fired on the bus."""
    event_type: str
    payload: Any = None
    timestamp: str = ""
    source: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class Subscription:
    """A subscription to an event type."""
    id: int
    event_type: str
    handler: Callable
    priority: int = 0
    active: bool = True
    call_count: int = 0


class EventBus:
    """Pub/sub event bus for task events."""
    def __init__(self):
        self._subscriptions: Dict[int, Subscription] = {}
        self._by_type: Dict[str, List[int]] = {}
        self._history: List[Event] = []
        self._next_id = 1
        self._max_history = 100

    def subscribe(self, event_type, handler, priority=0):
        """Subscribe a handler to an event type."""
        sub = Subscription(id=self._next_id, event_type=event_type,
                          handler=handler, priority=priority)
        self._subscriptions[self._next_id] = sub
        if event_type not in self._by_type:
            self._by_type[event_type] = []
        self._by_type[event_type].append(self._next_id)
        self._next_id += 1
        return sub

    def unsubscribe(self, sub_id):
        """Remove a subscription."""
        if sub_id not in self._subscriptions:
            return False
        sub = self._subscriptions[sub_id]
        if sub.event_type in self._by_type:
            self._by_type[sub.event_type].remove(sub_id)
        del self._subscriptions[sub_id]
        return True

    def publish(self, event_type, payload=None, source=""):
        """Publish an event to all subscribers."""
        event = Event(event_type=event_type, payload=payload, source=source)
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        sub_ids = sorted(self._by_type.get(event_type, []),
                         key=lambda sid: -self._subscriptions[sid].priority)
        results = []
        for sid in sub_ids:
            sub = self._subscriptions.get(sid)
            if not sub or not sub.active:
                continue
            try:
                result = sub.handler(event)
                sub.call_count += 1
                results.append({"sub_id": sid, "event_type": event_type,
                                "result": result, "error": None})
            except Exception as e:
                results.append({"sub_id": sid, "event_type": event_type,
                                "result": None, "error": str(e)})
        return results

    def get(self, sub_id):
        return self._subscriptions.get(sub_id)

    def subscriptions_for(self, event_type):
        """Return all subscriptions for an event type."""
        ids = self._by_type.get(event_type, [])
        return [self._subscriptions[sid] for sid in ids if sid in self._subscriptions]

    def all_subscriptions(self):
        return list(self._subscriptions.values())

    def event_types(self):
        return sorted(self._by_type.keys())

    def subscription_count(self):
        return len(self._subscriptions)

    def history(self):
        return list(self._history)

    def clear_history(self):
        self._history = []

    def deactivate(self, sub_id):
        if sub_id in self._subscriptions:
            self._subscriptions[sub_id].active = False
            return True
        return False

    def activate(self, sub_id):
        if sub_id in self._subscriptions:
            self._subscriptions[sub_id].active = True
            return True
        return False


def event_summary(bus):
    """Generate an event bus summary."""
    return {
        "total_subscriptions": bus.subscription_count(),
        "event_types": len(bus.event_types()),
        "history_size": len(bus.history()),
        "by_type": {et: len(bus.subscriptions_for(et)) for et in bus.event_types()},
    }
