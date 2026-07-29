"""Batch operations on multiple tasks."""
from typing import Any, Dict, List, Optional


def batch_update(tasks: list, task_ids: List[int], **fields) -> dict:
    """Update multiple tasks with the same field values."""
    id_set = set(task_ids)
    updated = 0
    for task in tasks:
        if task.id in id_set:
            for key, value in fields.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            updated += 1
    return {"requested": len(task_ids), "updated": updated}


def batch_delete(tasks: list, task_ids: List[int]) -> dict:
    """Delete multiple tasks by ID."""
    id_set = set(task_ids)
    before = len(tasks)
    tasks[:] = [t for t in tasks if t.id not in id_set]
    after = len(tasks)
    return {"requested": len(task_ids), "deleted": before - after, "remaining": after}


def batch_assign(tasks: list, task_ids: List[int], assignee: str) -> dict:
    """Assign multiple tasks to a single person."""
    id_set = set(task_ids)
    assigned = sum(1 for t in tasks if t.id in id_set and (setattr(t, "assignee", assignee) or True))
    return {"requested": len(task_ids), "assigned": assigned}


def batch_change_status(tasks: list, task_ids: List[int], status: str) -> dict:
    """Change the status of multiple tasks."""
    id_set = set(task_ids)
    changed = 0
    for task in tasks:
        if task.id in id_set:
            if hasattr(task.status, "value"):
                from src.models import Status
                task.status = Status(status)
            else:
                task.status = status
            changed += 1
    return {"requested": len(task_ids), "changed": changed}


def batch_add_tag(tasks: list, task_ids: List[int], tag: str) -> dict:
    """Add a tag to multiple tasks."""
    id_set = set(task_ids)
    tagged = 0
    for task in tasks:
        if task.id in id_set:
            if not hasattr(task, "tags") or task.tags is None:
                task.tags = []
            if tag not in task.tags:
                task.tags.append(tag)
            tagged += 1
    return {"requested": len(task_ids), "tagged": tagged}


def batch_remove_tag(tasks: list, task_ids: List[int], tag: str) -> dict:
    """Remove a tag from multiple tasks."""
    id_set = set(task_ids)
    untagged = 0
    for task in tasks:
        if task.id in id_set:
            if hasattr(task, "tags") and task.tags:
                before = len(task.tags)
                task.tags = [t for t in task.tags if t != tag]
                if len(task.tags) < before:
                    untagged += 1
    return {"requested": len(task_ids), "untagged": untagged}


def batch_set_priority(tasks: list, task_ids: List[int], priority: str) -> dict:
    """Set priority on multiple tasks."""
    id_set = set(task_ids)
    changed = 0
    for task in tasks:
        if task.id in id_set:
            if hasattr(task.priority, "value"):
                from src.models import Priority
                task.priority = Priority(priority)
            else:
                task.priority = priority
            changed += 1
    return {"requested": len(task_ids), "changed": changed}


def batch_archive(tasks: list, task_ids: List[int]) -> dict:
    """Archive multiple tasks by marking them as done and adding archive tag."""
    id_set = set(task_ids)
    archived = 0
    for task in tasks:
        if task.id in id_set:
            if hasattr(task.status, "value"):
                from src.models import Status
                task.status = Status("done")
            else:
                task.status = "done"
            if not hasattr(task, "tags") or task.tags is None:
                task.tags = []
            if "archived" not in task.tags:
                task.tags.append("archived")
            archived += 1
    return {"requested": len(task_ids), "archived": archived}


def batch_summary(tasks: list, task_ids: List[int]) -> dict:
    """Generate a summary of the selected tasks."""
    id_set = set(task_ids)
    selected = [t for t in tasks if t.id in id_set]
    return {
        "selected": len(selected),
        "not_found": len(task_ids) - len(selected),
        "by_status": _count_by(selected, "status"),
        "by_priority": _count_by(selected, "priority"),
    }


def _count_by(tasks: list, field: str) -> dict:
    counts = {}
    for t in tasks:
        attr = getattr(t, field, None)
        value = attr.value if hasattr(attr, "value") else attr
        if value:
            counts[value] = counts.get(value, 0) + 1
    return counts
