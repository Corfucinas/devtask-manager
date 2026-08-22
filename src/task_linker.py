"""Task linker for cross-references."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set


LINK_TYPES = {
    "blocks": {"reverse": "blocked_by", "label": "Blocks"},
    "blocked_by": {"reverse": "blocks", "label": "Blocked By"},
    "duplicates": {"reverse": "duplicates", "label": "Duplicates"},
    "relates_to": {"reverse": "relates_to", "label": "Relates To"},
    "causes": {"reverse": "caused_by", "label": "Causes"},
    "caused_by": {"reverse": "causes", "label": "Caused By"},
    "fixes": {"reverse": "fixed_by", "label": "Fixes"},
    "fixed_by": {"reverse": "fixes", "label": "Fixed By"},
}


@dataclass
class TaskLink:
    """A link between two tasks."""
    id: int
    source_id: int
    target_id: int
    link_type: str = "relates_to"
    created_at: str = ""
    created_by: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def reverse_type(self):
        """Return the reverse link type."""
        info = LINK_TYPES.get(self.link_type, {})
        return info.get("reverse", "relates_to")


class TaskLinker:
    """Manages cross-references between tasks."""
    def __init__(self):
        self._links: Dict[int, TaskLink] = {}
        self._by_source: Dict[int, List[int]] = {}
        self._by_target: Dict[int, List[int]] = {}
        self._next_id = 1

    def link(self, source_id, target_id, link_type="relates_to", created_by=""):
        """Create a link between two tasks."""
        existing = self.find_exact(source_id, target_id, link_type)
        if existing:
            return existing
        link = TaskLink(id=self._next_id, source_id=source_id,
                        target_id=target_id, link_type=link_type,
                        created_by=created_by)
        self._links[self._next_id] = link
        if source_id not in self._by_source:
            self._by_source[source_id] = []
        self._by_source[source_id].append(self._next_id)
        if target_id not in self._by_target:
            self._by_target[target_id] = []
        self._by_target[target_id].append(self._next_id)
        self._next_id += 1
        return link

    def unlink(self, link_id):
        """Remove a link."""
        if link_id not in self._links:
            return False
        link = self._links[link_id]
        if link_id in self._by_source.get(link.source_id, []):
            self._by_source[link.source_id].remove(link_id)
        if link_id in self._by_target.get(link.target_id, []):
            self._by_target[link.target_id].remove(link_id)
        del self._links[link_id]
        return True

    def get(self, link_id):
        return self._links.get(link_id)

    def find_exact(self, source_id, target_id, link_type=None):
        """Find an exact link match."""
        for link in self._links.values():
            if link.source_id == source_id and link.target_id == target_id:
                if link_type is None or link.link_type == link_type:
                    return link
        return None

    def links_from(self, task_id):
        """Return all links from a task."""
        ids = self._by_source.get(task_id, [])
        return [self._links[i] for i in ids if i in self._links]

    def links_to(self, task_id):
        """Return all links to a task."""
        ids = self._by_target.get(task_id, [])
        return [self._links[i] for i in ids if i in self._links]

    def find_linked(self, task_id):
        """Return all task IDs linked to/from a task."""
        linked = set()
        for link in self.links_from(task_id):
            linked.add(link.target_id)
        for link in self.links_to(task_id):
            linked.add(link.source_id)
        return sorted(linked)

    def all_links(self):
        return list(self._links.values())

    def count(self):
        return len(self._links)

    def link_count_for(self, task_id):
        return len(self.links_from(task_id)) + len(self.links_to(task_id))

    def by_type(self, link_type):
        """Return all links of a specific type."""
        return [l for l in self._links.values() if l.link_type == link_type]

    def find_chain(self, task_id, visited=None):
        """Find the transitive closure of all linked tasks."""
        if visited is None:
            visited = set()
        if task_id in visited:
            return set()
        visited.add(task_id)
        for linked_id in self.find_linked(task_id):
            self.find_chain(linked_id, visited)
        return visited

    def clear(self):
        self._links = {}
        self._by_source = {}
        self._by_target = {}
        self._next_id = 1


def link_summary(linker):
    """Generate a link summary report."""
    return {
        "total_links": linker.count(),
        "by_type": {lt: len(linker.by_type(lt)) for lt in LINK_TYPES},
        "tasks_with_links": len(set(
            [l.source_id for l in linker.all_links()] +
            [l.target_id for l in linker.all_links()]
        )),
    }
