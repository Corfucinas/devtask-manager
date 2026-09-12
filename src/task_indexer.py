"""Task indexer for fast attribute lookups."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


class TaskIndexer:
    """Maintains inverted indexes over task attributes."""
    def __init__(self):
        self._by_tag: Dict[str, Set[int]] = {}
        self._by_status: Dict[str, Set[int]] = {}
        self._by_assignee: Dict[str, Set[int]] = {}
        self._by_title_token: Dict[str, Set[int]] = {}
        self._all: Set[int] = set()

    def index(self, task):
        """Add/update a task in the index."""
        tid = getattr(task, "id", None)
        if tid is None:
            return
        self.remove(tid)
        self._all.add(tid)
        for tag in (getattr(task, "tags", None) or []):
            self._by_tag.setdefault(tag, set()).add(tid)
        status = _get_status(task)
        self._by_status.setdefault(status, set()).add(tid)
        assignee = getattr(task, "assignee", None)
        if assignee:
            self._by_assignee.setdefault(assignee, set()).add(tid)
        title = (getattr(task, "title", "") or "").lower()
        for token in title.split():
            self._by_title_token.setdefault(token, set()).add(tid)

    def remove(self, task_id: int):
        """Remove a task from the index."""
        self._all.discard(task_id)
        for s in self._by_tag.values(): s.discard(task_id)
        for s in self._by_status.values(): s.discard(task_id)
        for s in self._by_assignee.values(): s.discard(task_id)
        for s in self._by_title_token.values(): s.discard(task_id)

    def find_by_tag(self, tag: str) -> List[int]:
        return sorted(self._by_tag.get(tag, set()))

    def find_by_status(self, status: str) -> List[int]:
        return sorted(self._by_status.get(status, set()))

    def find_by_assignee(self, assignee: str) -> List[int]:
        return sorted(self._by_assignee.get(assignee, set()))

    def find_by_title_token(self, token: str) -> List[int]:
        return sorted(self._by_title_token.get(token.lower(), set()))

    def find_any(self, tags=None, status=None, assignee=None, token=None) -> List[int]:
        """Find tasks matching ANY of the given criteria."""
        results: Set[int] = set()
        if tags:
            for tag in tags:
                results |= self._by_tag.get(tag, set())
        if status:
            results |= self._by_status.get(status, set())
        if assignee:
            results |= self._by_assignee.get(assignee, set())
        if token:
            results |= self._by_title_token.get(token.lower(), set())
        return sorted(results)

    def find_all(self, tags=None, status=None, assignee=None, token=None) -> List[int]:
        """Find tasks matching ALL given criteria (intersection)."""
        sets: List[Set[int]] = []
        if tags:
            for tag in tags:
                sets.append(self._by_tag.get(tag, set()))
        if status:
            sets.append(self._by_status.get(status, set()))
        if assignee:
            sets.append(self._by_assignee.get(assignee, set()))
        if token:
            sets.append(self._by_title_token.get(token.lower(), set()))
        if not sets:
            return sorted(self._all)
        return sorted(set.intersection(*sets))

    def all_ids(self) -> List[int]:
        return sorted(self._all)

    def size(self) -> int:
        return len(self._all)

    def clear(self):
        self._by_tag.clear(); self._by_status.clear()
        self._by_assignee.clear(); self._by_title_token.clear()
        self._all.clear()


def index_stats(indexer: TaskIndexer) -> Dict:
    return {"total_tasks": indexer.size(),
            "unique_tags": len(indexer._by_tag),
            "unique_statuses": len(indexer._by_status),
            "unique_assignees": len(indexer._by_assignee),
            "unique_title_tokens": len(indexer._by_title_token)}
