"""Task grouper with dynamic grouping strategies."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class GroupingStrategy(Enum):
    """Available grouping strategies."""
    BY_STATUS = "by_status"
    BY_PRIORITY = "by_priority"
    BY_ASSIGNEE = "by_assignee"
    BY_TAG = "by_tag"
    BY_SPRINT = "by_sprint"
    CUSTOM = "custom"


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


@dataclass
class TaskGroup:
    """A group of tasks sharing a common key."""
    key: str
    tasks: List = field(default_factory=list)
    count: int = 0

    def add(self, task):
        self.tasks.append(task)
        self.count = len(self.tasks)


def group_tasks(tasks, strategy=GroupingStrategy.BY_STATUS, key_func=None):
    """Group tasks by a strategy or custom function."""
    if strategy == GroupingStrategy.CUSTOM and key_func:
        pass
    elif strategy == GroupingStrategy.BY_STATUS:
        key_func = lambda t: _get_status(t)
    elif strategy == GroupingStrategy.BY_PRIORITY:
        key_func = lambda t: _get_priority(t)
    elif strategy == GroupingStrategy.BY_ASSIGNEE:
        key_func = lambda t: getattr(t, "assignee", None) or "unassigned"
    elif strategy == GroupingStrategy.BY_TAG:
        return _group_by_tag(tasks)
    elif strategy == GroupingStrategy.BY_SPRINT:
        key_func = lambda t: str(getattr(t, "sprint_id", "no_sprint"))

    groups: Dict[str, TaskGroup] = {}
    for task in tasks:
        key = str(key_func(task))
        if key not in groups:
            groups[key] = TaskGroup(key=key)
        groups[key].add(task)
    return groups


def _group_by_tag(tasks):
    """Group tasks by tags (a task can be in multiple groups)."""
    groups: Dict[str, TaskGroup] = {}
    for task in tasks:
        tags = getattr(task, "tags", []) or []
        if not tags:
            key = "untagged"
            if key not in groups:
                groups[key] = TaskGroup(key=key)
            groups[key].add(task)
        else:
            for tag in tags:
                if tag not in groups:
                    groups[tag] = TaskGroup(key=tag)
                groups[tag].add(task)
    return groups


class Grouper:
    """Advanced task grouper with multiple strategies."""
    def __init__(self, strategy=GroupingStrategy.BY_STATUS):
        self._strategy = strategy
        self._custom_func = None

    @property
    def strategy(self):
        return self._strategy

    def set_strategy(self, strategy):
        self._strategy = strategy
        return self

    def set_custom(self, key_func):
        self._custom_func = key_func
        self._strategy = GroupingStrategy.CUSTOM
        return self

    def group(self, tasks):
        return group_tasks(tasks, self._strategy, self._custom_func)

    def group_names(self, tasks):
        return sorted(self.group(tasks).keys())

    def group_sizes(self, tasks):
        return {k: g.count for k, g in self.group(tasks).items()}


def grouping_report(groups):
    """Generate a grouping summary report."""
    return {
        "total_groups": len(groups),
        "total_tasks": sum(g.count for g in groups.values()),
        "avg_group_size": round(sum(g.count for g in groups.values()) / max(len(groups), 1), 1),
        "largest_group": max((g.count for g in groups.values()), default=0),
        "smallest_group": min((g.count for g in groups.values()), default=0),
        "group_keys": sorted(groups.keys()),
    }


def multi_group(tasks, strategies):
    """Group tasks by multiple strategies, returning nested groups."""
    result = {}
    for strategy in strategies:
        groups = group_tasks(tasks, strategy)
        result[strategy.value] = {k: g.count for k, g in groups.items()}
    return result
