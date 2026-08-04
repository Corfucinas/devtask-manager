"""Task diff and change comparison."""
from dataclasses import dataclass
from typing import Any, List


@dataclass
class TaskDiff:
    """A single field change between two task versions."""
    field: str
    old_value: Any
    new_value: Any
    change_type: str = "modified"

    @property
    def is_added(self):
        return self.change_type == "added"

    @property
    def is_removed(self):
        return self.change_type == "removed"

    @property
    def is_modified(self):
        return self.change_type == "modified"

    @property
    def changed(self):
        return self.old_value != self.new_value


def _task_to_dict(task):
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


def diff_tasks(old, new):
    old_dict = _task_to_dict(old)
    new_dict = _task_to_dict(new)
    diffs = []
    all_fields = set(old_dict.keys()) | set(new_dict.keys())
    for field_name in sorted(all_fields):
        old_val = old_dict.get(field_name)
        new_val = new_dict.get(field_name)
        if field_name not in old_dict:
            diffs.append(TaskDiff(field=field_name, old_value=None,
                                  new_value=new_val, change_type="added"))
        elif field_name not in new_dict:
            diffs.append(TaskDiff(field=field_name, old_value=old_val,
                                  new_value=None, change_type="removed"))
        elif old_val != new_val:
            diffs.append(TaskDiff(field=field_name, old_value=old_val,
                                  new_value=new_val, change_type="modified"))
    return diffs


def apply_diff(task, diffs):
    for diff in diffs:
        if diff.field == "title":
            task.title = diff.new_value
        elif diff.field == "description":
            task.description = diff.new_value
        elif diff.field == "priority":
            if hasattr(task.priority, "value"):
                from src.models import Priority
                task.priority = Priority(diff.new_value)
            else:
                task.priority = diff.new_value
        elif diff.field == "status":
            if hasattr(task.status, "value"):
                from src.models import Status
                task.status = Status(diff.new_value)
            else:
                task.status = diff.new_value
        elif diff.field == "tags":
            task.tags = diff.new_value or []
        elif diff.field == "assignee":
            task.assignee = diff.new_value
        elif diff.field == "due_date":
            task.due_date = diff.new_value


def format_diff(diffs):
    lines = []
    for diff in diffs:
        if diff.is_added:
            lines.append(f"+ {diff.field}: {diff.new_value}")
        elif diff.is_removed:
            lines.append(f"- {diff.field}: {diff.old_value}")
        else:
            lines.append(f"~ {diff.field}: {diff.old_value} -> {diff.new_value}")
    return "\n".join(lines)


def diff_summary(diffs):
    return {
        "total_changes": len(diffs),
        "added": sum(1 for d in diffs if d.is_added),
        "removed": sum(1 for d in diffs if d.is_removed),
        "modified": sum(1 for d in diffs if d.is_modified),
        "fields_changed": [d.field for d in diffs],
    }


def has_changes(diffs):
    return any(d.changed for d in diffs)


def revert_diff(diffs):
    return [
        TaskDiff(field=d.field, old_value=d.new_value, new_value=d.old_value,
                 change_type="removed" if d.is_added else ("added" if d.is_removed else "modified"))
        for d in diffs
    ]


def merge_diffs(diffs_a, diffs_b):
    by_field = {d.field: d for d in diffs_a}
    for d in diffs_b:
        by_field[d.field] = d
    return sorted(by_field.values(), key=lambda d: d.field)
