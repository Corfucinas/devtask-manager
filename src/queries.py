"""Saved query management for reusable task filters."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class SavedQuery:
    """A reusable task query with filters and sort."""
    id: int
    name: str
    description: str = ""
    filters: Dict[str, Any] = field(default_factory=dict)
    sort_by: str = "created_at"
    sort_desc: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class QueryLibrary:
    """Manages a collection of saved queries."""

    def __init__(self):
        self._queries: Dict[int, SavedQuery] = {}
        self._next_id = 1

    def save(self, name: str, filters: dict = None, sort_by: str = "created_at",
             sort_desc: bool = False, description: str = "") -> SavedQuery:
        query = SavedQuery(
            id=self._next_id, name=name, description=description,
            filters=filters or {}, sort_by=sort_by, sort_desc=sort_desc,
        )
        self._queries[self._next_id] = query
        self._next_id += 1
        return query

    def get(self, query_id: int) -> Optional[SavedQuery]:
        return self._queries.get(query_id)

    def find_by_name(self, name: str) -> Optional[SavedQuery]:
        for q in self._queries.values():
            if q.name.lower() == name.lower():
                return q
        return None

    def remove(self, query_id: int) -> bool:
        if query_id in self._queries:
            del self._queries[query_id]
            return True
        return False

    def all_queries(self) -> List[SavedQuery]:
        return sorted(self._queries.values(), key=lambda q: q.name)

    def count(self) -> int:
        return len(self._queries)

    def update(self, query_id: int, **kwargs) -> bool:
        query = self._queries.get(query_id)
        if not query:
            return False
        for key, value in kwargs.items():
            if hasattr(query, key):
                setattr(query, key, value)
        return True


def execute_query(query: SavedQuery, tasks: list) -> list:
    """Apply a saved query's filters and sort to a task list."""
    results = list(tasks)
    filters = query.filters

    if "status" in filters:
        status = filters["status"]
        results = [t for t in results
                   if (t.status.value if hasattr(t.status, "value") else t.status) == status]

    if "priority" in filters:
        priority = filters["priority"]
        results = [t for t in results
                   if (t.priority.value if hasattr(t.priority, "value") else t.priority) == priority]

    if "tags" in filters:
        tags = set(filters["tags"])
        mode = filters.get("tag_mode", "any")
        if mode == "all":
            results = [t for t in results if tags.issubset(set(getattr(t, "tags", []) or []))]
        else:
            results = [t for t in results if tags & set(getattr(t, "tags", []) or [])]

    if "assignee" in filters:
        assignee = filters["assignee"]
        results = [t for t in results if getattr(t, "assignee", None) == assignee]

    if "text" in filters:
        text = filters["text"].lower()
        results = [t for t in results
                   if text in getattr(t, "title", "").lower()
                   or text in getattr(t, "description", "").lower()]

    sort_key = query.sort_by
    results.sort(key=lambda t: getattr(t, sort_key, ""), reverse=query.sort_desc)
    return results


def default_queries() -> QueryLibrary:
    lib = QueryLibrary()
    defaults = [
        ("My Open Tasks", {"status": "todo", "assignee": None}, "created_at", False,
         "All open tasks assigned to me"),
        ("High Priority", {"priority": "high"}, "created_at", False, "All high-priority tasks"),
        ("Critical Backlog", {"priority": "critical", "status": "todo"}, "created_at", True,
         "Critical tasks not yet started"),
        ("Recently Updated", {}, "updated_at", True, "Tasks sorted by most recent update"),
        ("Completed This Sprint", {"status": "done"}, "created_at", False, "All completed tasks"),
        ("Bugs", {"tags": ["bug"], "tag_mode": "any"}, "created_at", False, "All tasks tagged as bugs"),
    ]
    for name, filters, sort_by, sort_desc, desc in defaults:
        lib.save(name, filters, sort_by, sort_desc, desc)
    return lib
