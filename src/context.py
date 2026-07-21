"""Task context and cross-references between tasks."""
from enum import Enum
from typing import List, Optional


class LinkType(Enum):
    """Types of links between tasks."""
    BLOCKS = "blocks"
    DUPLICATES = "duplicates"
    RELATES_TO = "relates-to"
    CAUSES = "causes"
    FIXES = "fixes"


def add_link(task, target_id: int, link_type: LinkType) -> None:
    """Create a typed link from task to target_id."""
    if not hasattr(task, "links") or task.links is None:
        task.links = []
    link = {"target": target_id, "type": link_type.value}
    if link not in task.links:
        task.links.append(link)


def get_links(task, link_type: Optional[LinkType] = None) -> List[dict]:
    """Retrieve links from a task, optionally filtered by type."""
    if not hasattr(task, "links") or not task.links:
        return []
    if link_type is None:
        return list(task.links)
    return [l for l in task.links if l["type"] == link_type.value]


def linked_tasks(task, all_tasks, link_type: Optional[LinkType] = None) -> list:
    """Resolve linked task objects from a task's links."""
    links = get_links(task, link_type)
    by_id = {t.id: t for t in all_tasks}
    return [by_id[l["target"]] for l in links if l["target"] in by_id]


def remove_link(task, target_id: int, link_type: LinkType) -> bool:
    """Remove a specific link. Returns True if removed."""
    if not hasattr(task, "links") or not task.links:
        return False
    before = len(task.links)
    task.links = [
        l for l in task.links
        if not (l["target"] == target_id and l["type"] == link_type.value)
    ]
    return len(task.links) < before


def bidirectional_link(task_a, task_b, link_type: LinkType) -> None:
    """Create a link in both directions between two tasks."""
    add_link(task_a, task_b.id, link_type)
    add_link(task_b, task_a.id, link_type)


def link_count(task) -> int:
    """Count total links on a task."""
    if not hasattr(task, "links") or not task.links:
        return 0
    return len(task.links)


def find_orphans(tasks) -> list:
    """Return tasks with no links at all."""
    return [t for t in tasks if link_count(t) == 0]
