"""Label hierarchy with parent-child relationships."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabelNode:
    """A node in the label hierarchy."""
    name: str
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    color: str = "#999999"
    description: str = ""

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def depth(self) -> int:
        """Calculate depth (will be accurate only if set by hierarchy)."""
        return getattr(self, "_depth", 0) if hasattr(self, "_depth") else 0


class LabelHierarchy:
    """Manages a hierarchical label tree."""
    def __init__(self):
        self._nodes: Dict[str, LabelNode] = {}
        self._depths: Dict[str, int] = {}

    def add(self, name: str, parent: str = None, color: str = "#999999",
            description: str = "") -> LabelNode:
        """Add a label to the hierarchy."""
        if name in self._nodes:
            return self._nodes[name]
        node = LabelNode(name=name, parent=parent, color=color, description=description)
        self._nodes[name] = node
        if parent and parent in self._nodes:
            self._nodes[parent].children.append(name)
        self._recalculate_depths()
        return node

    def remove(self, name: str) -> bool:
        """Remove a label and all its children."""
        if name not in self._nodes:
            return False
        children = list(self._nodes[name].children)
        for child in children:
            self.remove(child)
        parent = self._nodes[name].parent
        if parent and parent in self._nodes:
            if name in self._nodes[parent].children:
                self._nodes[parent].children.remove(name)
        del self._nodes[name]
        self._recalculate_depths()
        return True

    def get(self, name: str) -> Optional[LabelNode]:
        return self._nodes.get(name)

    def all_labels(self) -> List[str]:
        return sorted(self._nodes.keys())

    def count(self) -> int:
        return len(self._nodes)

    def roots(self) -> List[LabelNode]:
        """Return all root labels (no parent)."""
        return [n for n in self._nodes.values() if n.is_root]

    def leaves(self) -> List[LabelNode]:
        """Return all leaf labels (no children)."""
        return [n for n in self._nodes.values() if n.is_leaf]

    def children_of(self, name: str) -> List[str]:
        """Return direct children of a label."""
        node = self._nodes.get(name)
        return list(node.children) if node else []

    def descendants_of(self, name: str) -> List[str]:
        """Return all descendants of a label."""
        result = []
        node = self._nodes.get(name)
        if not node:
            return result
        for child in node.children:
            result.append(child)
            result.extend(self.descendants_of(child))
        return result

    def get_path(self, name: str) -> List[str]:
        """Get the full path from root to this label."""
        path = []
        current = name
        while current and current in self._nodes:
            path.append(current)
            current = self._nodes[current].parent
        return list(reversed(path))

    def depth_of(self, name: str) -> int:
        """Get the depth of a label (0 = root)."""
        return self._depths.get(name, 0)

    def _recalculate_depths(self):
        """Recalculate depths for all nodes."""
        self._depths = {}
        for name in self._nodes:
            self._depths[name] = len(self.get_path(name)) - 1

    def subtree(self, name: str) -> Dict:
        """Return a subtree as a nested dict."""
        node = self._nodes.get(name)
        if not node:
            return {}
        return {
            "name": node.name,
            "color": node.color,
            "children": [self.subtree(c) for c in node.children],
        }

    def flatten(self) -> List[Dict]:
        """Return all labels with their paths and depths."""
        return [
            {"name": name, "path": "/".join(self.get_path(name)),
             "depth": self.depth_of(name), "parent": self._nodes[name].parent}
            for name in sorted(self._nodes.keys())
        ]


def default_hierarchy() -> LabelHierarchy:
    """Create a hierarchy with common default labels."""
    h = LabelHierarchy()
    h.add("type", color="#999", description="Task types")
    h.add("bug", parent="type", color="#d73a4a", description="Bug fix")
    h.add("feature", parent="type", color="#a2eeef", description="New feature")
    h.add("refactor", parent="type", color="#d876e3")
    h.add("docs", parent="type", color="#0075ca")
    h.add("priority", color="#e99695", description="Priority levels")
    h.add("urgent", parent="priority", color="#e99695")
    h.add("normal", parent="priority", color="#0075ca")
    h.add("low", parent="priority", color="#999999")
    return h
