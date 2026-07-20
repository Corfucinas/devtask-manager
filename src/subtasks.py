"""Subtask hierarchy and parent-child relationships."""


def add_subtask(parent_task, child_id):
    """Attach a child task ID to a parent task."""
    if not hasattr(parent_task, "subtasks") or parent_task.subtasks is None:
        parent_task.subtasks = []
    if child_id not in parent_task.subtasks:
        parent_task.subtasks.append(child_id)


def get_subtasks(parent_task, all_tasks):
    """Return direct child tasks of a parent."""
    if not hasattr(parent_task, "subtasks") or not parent_task.subtasks:
        return []
    by_id = {t.id: t for t in all_tasks}
    return [by_id[cid] for cid in parent_task.subtasks if cid in by_id]


def get_descendants(parent_task, all_tasks, visited=None):
    """Recursively fetch all descendants of a task."""
    if visited is None:
        visited = set()
    parent_id = parent_task.id
    if parent_id in visited:
        return []
    visited.add(parent_id)

    children = get_subtasks(parent_task, all_tasks)
    result = list(children)
    for child in children:
        result.extend(get_descendants(child, all_tasks, visited))
    return result


def is_blocked_by(task, all_tasks):
    """Check if a task is blocked by incomplete parent tasks."""
    for t in all_tasks:
        if hasattr(t, "subtasks") and t.subtasks and task.id in t.subtasks:
            parent_status = t.status.value if hasattr(t.status, "value") else t.status
            if parent_status != "done":
                return True
    return False


def flatten_hierarchy(tasks):
    """Return task IDs that have children, with their direct child counts."""
    hierarchy = {}
    for t in tasks:
        if hasattr(t, "subtasks") and t.subtasks:
            hierarchy[t.id] = len(t.subtasks)
    return hierarchy
