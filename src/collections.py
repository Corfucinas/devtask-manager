"""Task collection grouping and batch views."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Collection:
    """A named collection of tasks with optional filter."""
    id: int
    name: str
    description: str = ""
    filter_fn: Optional[Callable] = None
    sort_fn: Optional[Callable] = None
    task_ids: List[int] = field(default_factory=list)
    color: str = "#999999"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def includes(self, task_id):
        return task_id in self.task_ids

    def count(self):
        return len(self.task_ids)


class CollectionManager:
    """Manages task collections."""
    def __init__(self):
        self._collections = {}
        self._next_id = 1

    def create(self, name, description="", filter_fn=None, sort_fn=None, color="#999999"):
        c = Collection(id=self._next_id, name=name, description=description,
                       filter_fn=filter_fn, sort_fn=sort_fn, color=color)
        self._collections[self._next_id] = c
        self._next_id += 1
        return c

    def get(self, collection_id):
        return self._collections.get(collection_id)

    def find_by_name(self, name):
        for c in self._collections.values():
            if c.name.lower() == name.lower():
                return c
        return None

    def remove(self, collection_id):
        if collection_id in self._collections:
            del self._collections[collection_id]
            return True
        return False

    def all_collections(self):
        return sorted(self._collections.values(), key=lambda c: c.name)

    def count(self):
        return len(self._collections)


def add_to_collection(collection, task_id):
    if task_id in collection.task_ids:
        return False
    collection.task_ids.append(task_id)
    return True


def remove_from_collection(collection, task_id):
    if task_id in collection.task_ids:
        collection.task_ids.remove(task_id)
        return True
    return False


def tasks_in_collection(collection, all_tasks):
    id_set = set(collection.task_ids)
    result = [t for t in all_tasks if getattr(t, "id", None) in id_set]
    if collection.sort_fn:
        result.sort(key=collection.sort_fn)
    return result


def auto_populate(collection, all_tasks):
    if not collection.filter_fn:
        return 0
    collection.task_ids = []
    for task in all_tasks:
        try:
            if collection.filter_fn(task):
                collection.task_ids.append(getattr(task, "id", 0))
        except Exception:
            continue
    return collection.count()


def collection_summary(manager, all_tasks):
    results = []
    for c in manager.all_collections():
        task_objs = tasks_in_collection(c, all_tasks)
        done = sum(1 for t in task_objs
                   if (t.status.value if hasattr(t.status, "value") else t.status) == "done")
        results.append({"id": c.id, "name": c.name, "count": c.count(),
                        "done": done,
                        "completion_rate": round(done / max(c.count(), 1) * 100, 1)})
    return results


def merge_collections(a, b):
    for task_id in b.task_ids:
        if task_id not in a.task_ids:
            a.task_ids.append(task_id)
    return a


def intersect_collections(a, b):
    return list(set(a.task_ids) & set(b.task_ids))


def diff_collections(a, b):
    return list(set(a.task_ids) - set(b.task_ids))


def default_collections():
    manager = CollectionManager()
    def is_high(task, context=None):
        p = task.priority.value if hasattr(task.priority, "value") else task.priority
        return p in ("high", "critical")
    def is_overdue(task, context=None):
        due = getattr(task, "due_date", None)
        if not due:
            return False
        status = task.status.value if hasattr(task.status, "value") else task.status
        if status == "done":
            return False
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
            return dt < datetime.now(timezone.utc)
        except (ValueError, TypeError):
            return False
    manager.create("High Priority", "All high/critical tasks", filter_fn=is_high, color="#e99695")
    manager.create("Overdue", "All overdue tasks", filter_fn=is_overdue, color="#d73a4a")
    manager.create("My Tasks", "Tasks assigned to me", color="#a2eeef")
    return manager
