"""Automatic task batching for bulk operations."""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


class TaskBatcher:
    """Groups tasks into fixed-size batches."""
    def __init__(self, batch_size: int = 10):
        self._batch_size = max(1, batch_size)

    @property
    def batch_size(self) -> int:
        return self._batch_size

    def set_batch_size(self, size: int):
        self._batch_size = max(1, size)
        return self

    def batch(self, tasks: List) -> List[List]:
        """Split tasks into fixed-size batches."""
        return [tasks[i:i + self._batch_size]
                for i in range(0, len(tasks), self._batch_size)]

    def batch_by_status(self, tasks: List) -> Dict[str, List[List]]:
        """Batch tasks grouped by status."""
        groups: Dict[str, List] = {}
        for t in tasks:
            groups.setdefault(_get_status(t), []).append(t)
        return {status: self.batch(group) for status, group in groups.items()}

    def batch_by_priority(self, tasks: List) -> Dict[str, List[List]]:
        """Batch tasks grouped by priority."""
        groups: Dict[str, List] = {}
        for t in tasks:
            groups.setdefault(_get_priority(t), []).append(t)
        return {priority: self.batch(group) for priority, group in groups.items()}

    def batch_by(self, tasks: List, key_func: Callable) -> Dict[str, List[List]]:
        """Batch tasks grouped by a custom key function."""
        groups: Dict[str, List] = {}
        for t in tasks:
            groups.setdefault(str(key_func(t)), []).append(t)
        return {key: self.batch(group) for key, group in groups.items()}

    def batch_count(self, tasks: List) -> int:
        """Number of batches a task list would produce."""
        return (len(tasks) + self._batch_size - 1) // self._batch_size

    def flatten(self, batches: List[List]) -> List:
        """Flatten batches back into a single list."""
        return [t for batch in batches for t in batch]


def batch_stats(batcher: TaskBatcher, tasks: List) -> Dict:
    batches = batcher.batch(tasks)
    sizes = [len(b) for b in batches]
    return {"total_tasks": len(tasks), "batch_size": batcher.batch_size,
            "total_batches": len(batches),
            "avg_batch_fill": round(sum(sizes) / max(len(sizes), 1), 1),
            "full_batches": sum(1 for s in sizes if s == batcher.batch_size),
            "partial_batches": sum(1 for s in sizes if s < batcher.batch_size)}
