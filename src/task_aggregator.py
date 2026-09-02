"""Task aggregator for cross-source merging."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class TaskSource:
    """A source of tasks."""
    id: int
    name: str
    endpoint: str = ""
    enabled: bool = True
    last_sync: Optional[str] = None
    task_count: int = 0
    sync_errors: int = 0
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class TaskAggregator:
    """Aggregates tasks from multiple sources."""
    def __init__(self):
        self._sources: Dict[int, TaskSource] = {}
        self._next_id = 1
        self._aggregated: List = []

    def add_source(self, name, endpoint=""):
        source = TaskSource(id=self._next_id, name=name, endpoint=endpoint)
        self._sources[self._next_id] = source
        self._next_id += 1
        return source

    def remove_source(self, source_id):
        if source_id in self._sources:
            del self._sources[source_id]
            return True
        return False

    def get_source(self, source_id):
        return self._sources.get(source_id)

    def all_sources(self):
        return list(self._sources.values())

    def enabled_sources(self):
        return [s for s in self._sources.values() if s.enabled]

    def source_count(self):
        return len(self._sources)

    def register_source_data(self, source_id, tasks):
        """Register tasks from a source."""
        source = self._sources.get(source_id)
        if source:
            source.task_count = len(tasks)
            source.last_sync = datetime.now(timezone.utc).isoformat()
            for task in tasks:
                if not hasattr(task, "_source"):
                    task._source = source.name
                self._aggregated.append(task)
            return len(tasks)
        return 0

    def aggregate(self):
        """Return all aggregated tasks."""
        return list(self._aggregated)

    def clear_aggregated(self):
        self._aggregated = []

    def aggregated_count(self):
        return len(self._aggregated)

    def deduplicate(self):
        """Remove duplicate tasks by ID."""
        seen = set()
        unique = []
        for task in self._aggregated:
            tid = getattr(task, "id", None)
            if tid is not None and tid not in seen:
                seen.add(tid)
                unique.append(task)
        removed = len(self._aggregated) - len(unique)
        self._aggregated = unique
        return removed

    def merge(self, *aggregators):
        """Merge other aggregators into this one."""
        total_merged = 0
        for agg in aggregators:
            for task in agg.aggregate():
                self._aggregated.append(task)
                total_merged += 1
        return total_merged


def aggregation_report(aggregator):
    """Generate an aggregation summary report."""
    return {
        "total_sources": aggregator.source_count(),
        "enabled_sources": len(aggregator.enabled_sources()),
        "total_tasks": aggregator.aggregated_count(),
        "by_source": {s.name: {"task_count": s.task_count, "enabled": s.enabled,
                               "last_sync": s.last_sync, "errors": s.sync_errors}
                      for s in aggregator.all_sources()},
    }


def default_aggregator():
    """Create an aggregator with default sources."""
    a = TaskAggregator()
    a.add_source("Internal", "internal://tasks")
    a.add_source("External API", "https://api.example.com/tasks")
    return a
