"""Smart task grouping by similarity."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set


@dataclass
class GroupConfig:
    """Configuration for smart grouping."""
    min_similarity: float = 0.3
    max_group_size: int = 10
    min_group_size: int = 2
    group_by_tags: bool = True
    group_by_priority: bool = True
    group_by_assignee: bool = True


@dataclass
class TaskGroup:
    """A group of similar tasks."""
    id: int
    name: str
    task_ids: List[int] = field(default_factory=list)
    shared_tags: List[str] = field(default_factory=list)
    shared_priority: Optional[str] = None
    shared_assignee: Optional[str] = None
    similarity_score: float = 0.0


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _title_similarity(a, b):
    tokens_a = set((getattr(a, "title", "") or "").lower().split())
    tokens_b = set((getattr(b, "title", "") or "").lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _tag_similarity(a, b):
    tags_a = set(getattr(a, "tags", []) or [])
    tags_b = set(getattr(b, "tags", []) or [])
    if not tags_a or not tags_b:
        return 0.0
    return len(tags_a & tags_b) / len(tags_a | tags_b)


def task_similarity(a, b, config=None):
    """Calculate similarity score between two tasks."""
    if config is None:
        config = GroupConfig()
    score = 0.0
    score += _title_similarity(a, b) * 0.4
    score += _tag_similarity(a, b) * 0.3
    if config.group_by_priority and _get_priority(a) == _get_priority(b):
        score += 0.15
    if config.group_by_assignee and getattr(a, "assignee", None) == getattr(b, "assignee", None) and getattr(a, "assignee", None):
        score += 0.15
    return round(min(1.0, score), 3)


class SmartGrouper:
    """Clusters tasks into groups by similarity."""
    def __init__(self, config=None):
        self._config = config or GroupConfig()
        self._groups: List[TaskGroup] = []
        self._next_id = 1

    def group_tasks(self, tasks):
        """Group tasks into similarity clusters."""
        self._groups = []
        assigned = set()
        for i, task_a in enumerate(tasks):
            id_a = getattr(task_a, "id", i)
            if id_a in assigned:
                continue
            group = TaskGroup(id=self._next_id, name=f"Group {self._next_id}",
                              task_ids=[id_a])
            self._next_id += 1
            assigned.add(id_a)

            shared_tags = set(getattr(task_a, "tags", []) or [])
            priorities = [_get_priority(task_a)]
            assignees = [getattr(task_a, "assignee", None)]

            for task_b in tasks[i+1:]:
                id_b = getattr(task_b, "id", 0)
                if id_b in assigned:
                    continue
                if len(group.task_ids) >= self._config.max_group_size:
                    break
                sim = task_similarity(task_a, task_b, self._config)
                if sim >= self._config.min_similarity:
                    group.task_ids.append(id_b)
                    assigned.add(id_b)
                    group.similarity_score = max(group.similarity_score, sim)
                    shared_tags &= set(getattr(task_b, "tags", []) or [])
                    priorities.append(_get_priority(task_b))
                    assignees.append(getattr(task_b, "assignee", None))

            group.shared_tags = sorted(shared_tags) if shared_tags else []
            if len(set(priorities)) == 1:
                group.shared_priority = priorities[0]
            if len(set(a for a in assignees if a)) == 1 and assignees[0]:
                group.shared_assignee = assignees[0]
            self._groups.append(group)
        return self._groups

    def all_groups(self):
        return list(self._groups)

    def group_count(self):
        return len(self._groups)

    def ungrouped_count(self):
        return sum(1 for g in self._groups if len(g.task_ids) < self._config.min_group_size)


def grouping_report(grouper):
    """Generate a grouping summary report."""
    groups = grouper.all_groups()
    return {
        "total_groups": len(groups),
        "total_tasks": sum(len(g.task_ids) for g in groups),
        "avg_group_size": round(sum(len(g.task_ids) for g in groups) / max(len(groups), 1), 1),
        "largest_group": max((len(g.task_ids) for g in groups), default=0),
        "groups_by_size": {
            "small": sum(1 for g in groups if len(g.task_ids) < 3),
            "medium": sum(1 for g in groups if 3 <= len(g.task_ids) < 7),
            "large": sum(1 for g in groups if len(g.task_ids) >= 7),
        },
    }
