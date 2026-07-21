"""Colored label management for tasks."""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Label:
    """An immutable label with name, color, and category."""
    name: str
    color: str
    category: str = "general"


class LabelRegistry:
    """Registry for managing available labels."""

    def __init__(self):
        self._labels: Dict[str, Label] = {}

    def register(self, label: Label) -> None:
        """Add a label to the registry."""
        self._labels[label.name] = label

    def get(self, name: str) -> Optional[Label]:
        """Retrieve a label by name."""
        return self._labels.get(name)

    def list_labels(self) -> List[Label]:
        """Return all registered labels sorted by name."""
        return sorted(self._labels.values(), key=lambda l: l.name)

    def by_category(self, category: str) -> List[Label]:
        """Return all labels in a specific category."""
        return [l for l in self._labels.values() if l.category == category]

    def remove(self, name: str) -> bool:
        """Remove a label from the registry."""
        if name in self._labels:
            del self._labels[name]
            return True
        return False


def apply_label(task, label: Label) -> None:
    """Attach a label to a task."""
    if not hasattr(task, "labels") or task.labels is None:
        task.labels = []
    existing_names = [l.name if hasattr(l, "name") else l for l in task.labels]
    if label.name not in existing_names:
        task.labels.append(label)


def filter_by_label(tasks, label_name: str) -> list:
    """Filter tasks that have a specific label."""
    results = []
    for task in tasks:
        labels = getattr(task, "labels", None) or []
        names = [l.name if hasattr(l, "name") else l for l in labels]
        if label_name in names:
            results.append(task)
    return results


def default_registry() -> LabelRegistry:
    """Create a registry with common default labels."""
    registry = LabelRegistry()
    defaults = [
        Label("bug", "#d73a4a", "type"),
        Label("feature", "#a2eeef", "type"),
        Label("refactor", "#d876e3", "type"),
        Label("docs", "#0075ca", "type"),
        Label("urgent", "#e99695", "priority"),
        Label("wontfix", "#ffffff", "status"),
    ]
    for label in defaults:
        registry.register(label)
    return registry
