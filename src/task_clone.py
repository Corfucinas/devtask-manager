"""Task cloning with deep copy."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import copy


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def clone_task(task, new_id=None):
    """Create a deep copy of a task."""
    cloned = copy.deepcopy(task)
    if new_id is not None:
        cloned.id = new_id
    if hasattr(cloned, "created_at"):
        cloned.created_at = datetime.now(timezone.utc).isoformat()
    if hasattr(cloned, "updated_at"):
        cloned.updated_at = cloned.created_at
    if hasattr(cloned, "completed_at"):
        cloned.completed_at = None
    return cloned


def clone_with_modifications(task, new_id=None, **kwargs):
    """Clone a task and apply modifications."""
    cloned = clone_task(task, new_id)
    for key, value in kwargs.items():
        if hasattr(cloned, key):
            setattr(cloned, key, value)
    if hasattr(cloned, "updated_at"):
        cloned.updated_at = datetime.now(timezone.utc).isoformat()
    return cloned


def clone_batch(tasks, modifications=None, id_offset=0):
    """Clone multiple tasks at once."""
    mods = modifications or {}
    clones = []
    for i, task in enumerate(tasks):
        new_id = getattr(task, "id", i) + id_offset
        clone = clone_with_modifications(task, new_id, **mods)
        clones.append(clone)
    return clones


def clone_subtree(task, all_tasks, new_id_offset=1000):
    """Clone a task and all its subtasks."""
    cloned = clone_task(task, new_id=getattr(task, "id", 0) + new_id_offset)
    subtasks = getattr(task, "subtask_ids", []) or []
    cloned_subtasks = []
    for sub_id in subtasks:
        sub = next((t for t in all_tasks if getattr(t, "id", None) == sub_id), None)
        if sub:
            cloned_sub = clone_task(sub, new_id=sub_id + new_id_offset)
            cloned_subtasks.append(cloned_sub)
    return cloned, cloned_subtasks


def clone_report(originals, clones):
    """Generate a cloning report."""
    return {
        "originals": len(originals),
        "clones": len(clones),
        "cloned_ids": [getattr(c, "id", None) for c in clones],
        "original_ids": [getattr(o, "id", None) for o in originals],
        "fields_preserved": ["title", "description", "tags", "priority"],
        "fields_reset": ["created_at", "updated_at", "completed_at"],
    }


def is_clone(original, clone):
    """Check if clone is a copy of original (same title, different id)."""
    return (getattr(original, "title", "") == getattr(clone, "title", "")
            and getattr(original, "id", None) != getattr(clone, "id", None))


def diff_original_clone(original, clone):
    """Find differences between original and clone."""
    diffs = {}
    attrs = ["title", "description", "tags", "priority", "status", "assignee"]
    for attr in attrs:
        orig_val = getattr(original, attr, None)
        clone_val = getattr(clone, attr, None)
        if hasattr(orig_val, "value"):
            orig_val = orig_val.value
        if hasattr(clone_val, "value"):
            clone_val = clone_val.value
        if orig_val != clone_val:
            diffs[attr] = {"original": orig_val, "clone": clone_val}
    return diffs
