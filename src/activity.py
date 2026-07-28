"""Activity feed and timeline tracking."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Activity:
    """A single activity event in the project timeline."""
    id: int
    activity_type: str
    actor: str
    target_type: str = "task"
    target_id: Optional[int] = None
    timestamp: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class ActivityFeed:
    """Collects and queries project activity events."""

    def __init__(self, max_size: int = 1000):
        self._activities: List[Activity] = []
        self._next_id = 1
        self._max_size = max_size

    def log(self, activity_type: str, actor: str,
            target_type: str = "task", target_id: int = None,
            metadata: dict = None) -> Activity:
        activity = Activity(
            id=self._next_id,
            activity_type=activity_type,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata or {},
        )
        self._activities.append(activity)
        self._next_id += 1
        if len(self._activities) > self._max_size:
            self._activities.pop(0)
        return activity

    def recent(self, limit: int = 20) -> List[Activity]:
        return self._activities[-limit:] if limit > 0 else []

    def all_activities(self) -> List[Activity]:
        return list(self._activities)

    def feed_since(self, timestamp: str) -> List[Activity]:
        from datetime import datetime as dt
        cutoff = dt.fromisoformat(timestamp.replace("Z", "+00:00"))
        results = []
        for a in self._activities:
            ts = dt.fromisoformat(a.timestamp.replace("Z", "+00:00"))
            if ts > cutoff:
                results.append(a)
        return results

    def feed_by_type(self, activity_type: str) -> List[Activity]:
        return [a for a in self._activities if a.activity_type == activity_type]

    def feed_by_actor(self, actor: str) -> List[Activity]:
        return [a for a in self._activities if a.actor == actor]

    def feed_by_target(self, target_id: int) -> List[Activity]:
        return [a for a in self._activities if a.target_id == target_id]

    def count(self) -> int:
        return len(self._activities)

    def clear(self) -> None:
        self._activities = []
        self._next_id = 1

    def activity_types(self) -> Dict[str, int]:
        counts = {}
        for a in self._activities:
            counts[a.activity_type] = counts.get(a.activity_type, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def actor_activity(self) -> Dict[str, int]:
        counts = {}
        for a in self._activities:
            counts[a.actor] = counts.get(a.actor, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def search(self, query: str) -> List[Activity]:
        query_lower = query.lower()
        results = []
        for a in self._activities:
            if query_lower in a.activity_type.lower():
                results.append(a)
            elif any(query_lower in str(v).lower() for v in a.metadata.values()):
                results.append(a)
        return results

    def timeline(self, group_by: str = "day") -> Dict[str, List[Activity]]:
        groups = {}
        for a in self._activities:
            ts = datetime.fromisoformat(a.timestamp.replace("Z", "+00:00"))
            if group_by == "hour":
                key = ts.strftime("%Y-%m-%d %H:00")
            else:
                key = ts.strftime("%Y-%m-%d")
            if key not in groups:
                groups[key] = []
            groups[key].append(a)
        return dict(sorted(groups.items()))
