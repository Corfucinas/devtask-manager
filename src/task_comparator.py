"""Task comparator for diff analysis."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


@dataclass
class FieldDiff:
    """A difference between two task fields."""
    field: str
    value_a: Any
    value_b: Any
    is_different: bool = True

    @property
    def change_type(self) -> str:
        if not self.is_different:
            return "unchanged"
        if self.value_a is None:
            return "added"
        if self.value_b is None:
            return "removed"
        return "modified"


COMPARE_FIELDS = [
    "id", "title", "description", "priority", "status",
    "tags", "assignee", "due_date",
]


def compare_tasks(a, b) -> List[FieldDiff]:
    """Compare two tasks field by field."""
    diffs = []
    for field_name in COMPARE_FIELDS:
        val_a = getattr(a, field_name, None)
        val_b = getattr(b, field_name, None)
        if hasattr(val_a, "value"):
            val_a = val_a.value
        if hasattr(val_b, "value"):
            val_b = val_b.value
        if isinstance(val_a, list):
            val_a = sorted(val_a or [])
        if isinstance(val_b, list):
            val_b = sorted(val_b or [])
        is_diff = val_a != val_b
        diffs.append(FieldDiff(field=field_name, value_a=val_a, value_b=val_b, is_different=is_diff))
    return diffs


def similarity_score(a, b) -> float:
    """Calculate similarity between two tasks (0-1)."""
    diffs = compare_tasks(a, b)
    same = sum(1 for d in diffs if not d.is_different)
    return round(same / len(diffs), 3)


def changed_fields(a, b) -> List[str]:
    """Return names of fields that differ."""
    return [d.field for d in compare_tasks(a, b) if d.is_different]


def unchanged_fields(a, b) -> List[str]:
    """Return names of fields that are the same."""
    return [d.field for d in compare_tasks(a, b) if not d.is_different]


def merge_tasks(a, b, strategy="b_wins") -> Dict:
    """Merge two tasks into a single dict."""
    result = {}
    for field_name in COMPARE_FIELDS:
        val_a = getattr(a, field_name, None)
        val_b = getattr(b, field_name, None)
        if hasattr(val_a, "value"):
            val_a = val_a.value
        if hasattr(val_b, "value"):
            val_b = val_b.value
        if val_a == val_b:
            result[field_name] = val_a
        elif strategy == "b_wins":
            result[field_name] = val_b
        elif strategy == "a_wins":
            result[field_name] = val_a
        elif strategy == "prefer_non_none":
            result[field_name] = val_b if val_b is not None else val_a
        elif strategy == "merge_lists" and isinstance(val_a, list) and isinstance(val_b, list):
            result[field_name] = sorted(set(val_a + val_b))
        else:
            result[field_name] = val_b
    result["_merge_strategy"] = strategy
    result["_merged_at"] = datetime.now(timezone.utc).isoformat()
    return result


def comparison_report(tasks) -> Dict:
    """Generate a comparison report across all task pairs."""
    if len(tasks) < 2:
        return {"total_tasks": len(tasks), "comparisons": 0}
    comparisons = []
    for i in range(len(tasks)):
        for j in range(i + 1, len(tasks)):
            sim = similarity_score(tasks[i], tasks[j])
            changed = changed_fields(tasks[i], tasks[j])
            comparisons.append({
                "task_a": getattr(tasks[i], "id", i),
                "task_b": getattr(tasks[j], "id", j),
                "similarity": sim,
                "changed_fields": changed,
                "changed_count": len(changed),
            })
    avg_sim = round(sum(c["similarity"] for c in comparisons) / len(comparisons), 3)
    return {
        "total_tasks": len(tasks),
        "comparisons": len(comparisons),
        "average_similarity": avg_sim,
        "most_similar": max(comparisons, key=lambda c: c["similarity"]),
        "least_similar": min(comparisons, key=lambda c: c["similarity"]),
    }


def diff_summary(a, b) -> Dict:
    """Generate a compact diff summary."""
    diffs = compare_tasks(a, b)
    return {
        "total_fields": len(diffs),
        "changed": sum(1 for d in diffs if d.is_different),
        "unchanged": sum(1 for d in diffs if not d.is_different),
        "similarity": similarity_score(a, b),
        "changes": {d.field: d.change_type for d in diffs if d.is_different},
    }
