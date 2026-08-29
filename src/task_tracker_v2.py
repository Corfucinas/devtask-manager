"""Enhanced task tracker with event logging."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class TrackerEvent:
    """A tracked event on a task."""
    id: int
    task_id: int
    event_type: str  # created, updated, status_changed, assigned, commented, completed
    actor: str = ""
    timestamp: str = ""
    before: Optional[Dict] = None
    after: Optional[Dict] = None
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class TaskTrackerV2:
    """Tracks task changes with event logging."""
    def __init__(self, max_events: int = 10000):
        self._events: List[TrackerEvent] = []
        self._by_task: Dict[int, List[int]] = {}
        self._next_id = 1
        self._max_events = max_events

    def log_event(self, task_id, event_type, actor="", before=None, after=None, **metadata):
        """Log a task event."""
        event = TrackerEvent(
            id=self._next_id, task_id=task_id, event_type=event_type,
            actor=actor, before=before, after=after, metadata=metadata or {})
        self._events.append(event)
        if task_id not in self._by_task:
            self._by_task[task_id] = []
        self._by_task[task_id].append(self._next_id)
        self._next_id += 1
        if len(self._events) > self._max_events:
            oldest = self._events.pop(0)
            if oldest.task_id in self._by_task:
                self._by_task[oldest.task_id] = [
                    i for i in self._by_task[oldest.task_id] if i > oldest.id]
        return event

    def get_event(self, event_id):
        """Get a specific event."""
        for e in self._events:
            if e.id == event_id:
                return e
        return None

    def task_history(self, task_id):
        """Return all events for a task."""
        ids = self._by_task.get(task_id, [])
        return [e for e in self._events if e.id in ids]

    def recent_events(self, limit=20):
        """Return most recent events."""
        return self._events[-limit:] if limit > 0 else []

    def all_events(self):
        return list(self._events)

    def event_count(self):
        return len(self._events)

    def by_type(self, event_type):
        return [e for e in self._events if e.event_type == event_type]

    def by_actor(self, actor):
        return [e for e in self._events if e.actor == actor]

    def by_task(self, task_id):
        return self.task_history(task_id)

    def tracked_tasks(self):
        return sorted(self._by_task.keys())

    def task_count(self):
        return len(self._by_task)

    def clear(self):
        self._events = []
        self._by_task = {}
        self._next_id = 1

    def search(self, query):
        """Search events by query string."""
        query_lower = query.lower()
        results = []
        for e in self._events:
            if (query_lower in e.event_type.lower() or
                query_lower in e.actor.lower() or
                any(query_lower in str(v).lower() for v in e.metadata.values())):
                results.append(e)
        return results

    def event_types(self):
        """Return all unique event types."""
        return sorted(set(e.event_type for e in self._events))

    def actors(self):
        """Return all unique actors."""
        return sorted(set(e.actor for e in self._events if e.actor))


def tracker_report(tracker):
    """Generate a tracking report."""
    events = tracker.all_events()
    by_type = {}
    for e in events:
        by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
    return {
        "total_events": len(events),
        "tracked_tasks": tracker.task_count(),
        "event_types": tracker.event_types(),
        "actors": tracker.actors(),
        "by_type": dict(sorted(by_type.items(), key=lambda x: -x[1])),
        "most_active_task": max(tracker._by_task.items(), key=lambda x: len(x[1]))[0]
            if tracker._by_task else None,
    }


def default_tracker():
    """Create a tracker with default settings."""
    return TaskTrackerV2(max_events=10000)
