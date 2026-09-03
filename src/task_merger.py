"""Task merger for combining task lists."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class MergeResult:
    """Result of merging task lists."""
    total_input: int = 0
    total_output: int = 0
    duplicates_removed: int = 0
    sources_merged: int = 0
    merged_at: str = ""

    def __post_init__(self):
        if not self.merged_at:
            self.merged_at = datetime.now(timezone.utc).isoformat()


class TaskMerger:
    """Merges and deduplicates task lists."""
    def __init__(self, dedup_key="id"):
        self._dedup_key = dedup_key
        self._merged: List = []
        self._results: List[MergeResult] = []

    @property
    def dedup_key(self):
        return self._dedup_key

    def set_dedup_key(self, key: str):
        self._dedup_key = key
        return self

    def merge(self, *task_lists) -> List:
        """Merge multiple task lists with deduplication."""
        seen = set()
        merged = []
        source_count = 0
        total_input = 0
        for task_list in task_lists:
            source_count += 1
            total_input += len(task_list)
            for task in task_list:
                key = getattr(task, self._dedup_key, id(task))
                if key not in seen:
                    seen.add(key)
                    merged.append(task)
        self._merged = merged
        result = MergeResult(total_input=total_input, sources_merged=source_count)
        self._results.append(result)
        return merged

    def append(self, tasks) -> List:
        """Append tasks to merged set (dedup against existing)."""
        seen = {getattr(t, self._dedup_key, id(t)) for t in self._merged}
        added = 0
        for task in tasks:
            key = getattr(task, self._dedup_key, id(task))
            if key not in seen:
                seen.add(key)
                self._merged.append(task)
                added += 1
        return self._merged

    def merged_tasks(self) -> List:
        return list(self._merged)

    def merged_count(self) -> int:
        return len(self._merged)

    def clear(self):
        self._merged = []
        self._results = []

    def find_duplicates(self, tasks) -> List:
        """Find duplicate entries in a task list."""
        seen = set()
        duplicates = []
        for task in tasks:
            key = getattr(task, self._dedup_key, id(task))
            if key in seen:
                duplicates.append(task)
            else:
                seen.add(key)
        return duplicates

    def deduplicate(self, tasks) -> List:
        """Return deduplicated list."""
        seen = set()
        result = []
        for task in tasks:
            key = getattr(task, self._dedup_key, id(task))
            if key not in seen:
                seen.add(key)
                result.append(task)
        return result

    def count_by_source(self, tasks, source_attr="_source") -> Dict[str, int]:
        """Count tasks by source."""
        counts = {}
        for task in tasks:
            source = getattr(task, source_attr, "unknown")
            counts[source] = counts.get(source, 0) + 1
        return counts

    def all_results(self):
        return list(self._results)


def merge_report(merger: TaskMerger) -> Dict:
    """Generate a merge summary report."""
    results = merger.all_results()
    return {
        "merged_count": merger.merged_count(),
        "dedup_key": merger.dedup_key,
        "merge_operations": len(results),
        "total_input": sum(r.total_input for r in results),
        "total_removed": sum(r.total_input for r in results) - merger.merged_count(),
        "sources_merged": sum(r.sources_merged for r in results),
    }


def default_merger() -> TaskMerger:
    return TaskMerger(dedup_key="id")
