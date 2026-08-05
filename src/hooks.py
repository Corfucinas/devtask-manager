"""Lifecycle hooks and event interceptors."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Hook:
    """A lifecycle hook registered for a specific event."""
    id: int
    event: str
    callback: Callable
    priority: int = 0
    enabled: bool = True
    fired_count: int = 0
    last_fired: Optional[str] = None

    def fire(self, task, context=None):
        if not self.enabled:
            return None
        try:
            result = self.callback(task, context or {})
            self.fired_count += 1
            self.last_fired = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as e:
            return {"error": str(e)}


class HookManager:
    """Manages lifecycle hooks for task events."""

    def __init__(self):
        self._hooks: Dict[int, Hook] = {}
        self._next_id = 1

    def register(self, event, callback, priority=0):
        hook = Hook(id=self._next_id, event=event, callback=callback, priority=priority)
        self._hooks[self._next_id] = hook
        self._next_id += 1
        return hook

    def unregister(self, hook_id):
        if hook_id in self._hooks:
            del self._hooks[hook_id]
            return True
        return False

    def get(self, hook_id):
        return self._hooks.get(hook_id)

    def hooks_for_event(self, event):
        matching = [h for h in self._hooks.values() if h.event == event and h.enabled]
        return sorted(matching, key=lambda h: -h.priority)

    def all_hooks(self):
        return list(self._hooks.values())

    def count(self):
        return len(self._hooks)

    def enable(self, hook_id):
        if hook_id in self._hooks:
            self._hooks[hook_id].enabled = True
            return True
        return False

    def disable(self, hook_id):
        if hook_id in self._hooks:
            self._hooks[hook_id].enabled = False
            return True
        return False

    def fire_hooks(self, event, task, context=None):
        results = []
        for hook in self.hooks_for_event(event):
            result = hook.fire(task, context)
            results.append({"hook_id": hook.id, "event": hook.event,
                            "result": result, "fired": result is not None})
        return results

    def events(self):
        return sorted(set(h.event for h in self._hooks.values()))

    def clear(self):
        self._hooks = {}
        self._next_id = 1

    def hook_count_for(self, event):
        return sum(1 for h in self._hooks.values() if h.event == event)


def default_hooks():
    manager = HookManager()
    def log_creation(task, context):
        return {"action": "logged", "task_id": getattr(task, "id", None)}
    def notify_assignee(task, context):
        return {"action": "notified", "assignee": getattr(task, "assignee", None)}
    def update_timestamp(task, context):
        if hasattr(task, "updated_at"):
            task.updated_at = datetime.now(timezone.utc).isoformat()
        return {"action": "timestamp_updated"}
    manager.register("task.created", log_creation, priority=10)
    manager.register("task.assigned", notify_assignee, priority=5)
    manager.register("task.updated", update_timestamp, priority=1)
    return manager


def hook_summary(manager):
    events = manager.events()
    return {"total_hooks": manager.count(), "event_count": len(events),
            "events": {e: manager.hook_count_for(e) for e in events}}
