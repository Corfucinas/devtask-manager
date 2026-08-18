"""Conflict resolution for concurrent task edits."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Conflict:
    """A field-level conflict between two concurrent edits."""
    field: str
    base_value: Any
    our_value: Any
    their_value: Any
    resolved: bool = False
    resolution: Optional[Any] = None
    resolution_strategy: str = ""

    def resolve(self, strategy="ours"):
        """Resolve this conflict using the specified strategy."""
        if strategy == "ours":
            self.resolution = self.our_value
        elif strategy == "theirs":
            self.resolution = self.their_value
        elif strategy == "base":
            self.resolution = self.base_value
        elif strategy == "merge" and isinstance(self.our_value, list) and isinstance(self.their_value, list):
            self.resolution = list(set(self.our_value + self.their_value))
        elif strategy == "latest":
            self.resolution = self.their_value  # simplified
        else:
            self.resolution = self.our_value
        self.resolution_strategy = strategy
        self.resolved = True
        return self.resolution


def detect_conflicts(base, ours, theirs):
    """Detect conflicts between three versions of a task (three-way merge)."""
    conflicts = []
    base_dict = _to_dict(base)
    our_dict = _to_dict(ours)
    their_dict = _to_dict(theirs)

    all_fields = set(base_dict.keys()) | set(our_dict.keys()) | set(their_dict.keys())

    for field_name in sorted(all_fields):
        base_val = base_dict.get(field_name)
        our_val = our_dict.get(field_name)
        their_val = their_dict.get(field_name)

        if our_val != their_val and our_val != base_val and their_val != base_val:
            conflicts.append(Conflict(
                field=field_name,
                base_value=base_val,
                our_value=our_val,
                their_value=their_val,
            ))
        elif our_val != base_val and their_val == base_val:
            pass  # only we changed, no conflict
        elif their_val != base_val and our_val == base_val:
            pass  # only they changed, no conflict

    return conflicts


def _to_dict(task):
    """Convert a task to a comparable dict."""
    if isinstance(task, dict):
        return task
    result = {}
    for attr in ("id", "title", "description", "priority", "status",
                 "tags", "assignee", "due_date"):
        val = getattr(task, attr, None)
        if hasattr(val, "value"):
            val = val.value
        if isinstance(val, list):
            val = sorted(val)
        result[attr] = val
    return result


class ConflictResolver:
    """Manages multiple conflicts and resolution strategies."""
    def __init__(self, default_strategy="ours"):
        self._conflicts: List[Conflict] = []
        self._default_strategy = default_strategy

    def add_conflict(self, conflict):
        self._conflicts.append(conflict)

    def resolve_all(self, strategy=None):
        """Resolve all conflicts using the given or default strategy."""
        strat = strategy or self._default_strategy
        results = {}
        for conflict in self._conflicts:
            if not conflict.resolved:
                results[conflict.field] = conflict.resolve(strat)
        return results

    def resolve_field(self, field_name, strategy=None):
        """Resolve a specific field conflict."""
        strat = strategy or self._default_strategy
        for conflict in self._conflicts:
            if conflict.field == field_name and not conflict.resolved:
                return conflict.resolve(strat)
        return None

    def unresolved(self):
        return [c for c in self._conflicts if not c.resolved]

    def resolved(self):
        return [c for c in self._conflicts if c.resolved]

    def count(self):
        return len(self._conflicts)

    def unresolved_count(self):
        return len(self.unresolved())

    def is_fully_resolved(self):
        return all(c.resolved for c in self._conflicts)

    def all_conflicts(self):
        return list(self._conflicts)

    def clear(self):
        self._conflicts = []


def resolve_conflict(conflict, strategy="ours"):
    """Resolve a single conflict."""
    return conflict.resolve(strategy)


def auto_resolve(base, ours, theirs, strategy="ours"):
    """Detect and auto-resolve all conflicts between three versions."""
    conflicts = detect_conflicts(base, ours, theirs)
    resolver = ConflictResolver(default_strategy=strategy)
    for conflict in conflicts:
        resolver.add_conflict(conflict)
    resolutions = resolver.resolve_all()
    return {
        "conflict_count": len(conflicts),
        "resolved": len(resolutions),
        "resolutions": resolutions,
        "unresolved": resolver.unresolved_count(),
    }


def conflict_summary(conflicts):
    """Generate a summary of conflicts."""
    return {
        "total": len(conflicts),
        "resolved": sum(1 for c in conflicts if c.resolved),
        "unresolved": sum(1 for c in conflicts if not c.resolved),
        "fields": [c.field for c in conflicts],
    }
