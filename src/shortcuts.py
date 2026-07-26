"""Keyboard shortcut definitions and binding management."""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Shortcut:
    """A keyboard shortcut binding."""
    key: str
    action: str
    description: str = ""
    context: str = "global"


class ShortcutMap:
    """Manages keyboard shortcut bindings."""

    def __init__(self):
        self._bindings: Dict[str, Shortcut] = {}

    def bind(self, key: str, action: str, description: str = "", context: str = "global") -> Shortcut:
        shortcut = Shortcut(key=key, action=action, description=description, context=context)
        self._bindings[key] = shortcut
        return shortcut

    def unbind(self, key: str) -> bool:
        if key in self._bindings:
            del self._bindings[key]
            return True
        return False

    def lookup(self, key: str) -> Optional[Shortcut]:
        return self._bindings.get(key)

    def action_for_key(self, key: str) -> Optional[str]:
        shortcut = self.lookup(key)
        return shortcut.action if shortcut else None

    def keys_for_action(self, action: str) -> List[str]:
        return [s.key for s in self._bindings.values() if s.action == action]

    def all_bindings(self) -> List[Shortcut]:
        return sorted(self._bindings.values(), key=lambda s: s.key)

    def by_context(self, context: str) -> List[Shortcut]:
        return [s for s in self._bindings.values() if s.context == context]

    def rebind(self, old_key: str, new_key: str) -> bool:
        if old_key not in self._bindings:
            return False
        if new_key in self._bindings:
            return False
        shortcut = self._bindings.pop(old_key)
        shortcut.key = new_key
        self._bindings[new_key] = shortcut
        return True

    def has_key(self, key: str) -> bool:
        return key in self._bindings

    def count(self) -> int:
        return len(self._bindings)


def default_shortcuts() -> ShortcutMap:
    sm = ShortcutMap()
    defaults = [
        ("n", "new_task", "Create a new task", "task_list"),
        ("e", "edit_task", "Edit selected task", "task_detail"),
        ("d", "done_task", "Mark task as done", "task_list"),
        ("x", "delete_task", "Delete selected task", "task_list"),
        ("s", "search", "Search tasks", "global"),
        ("f", "filter", "Filter tasks", "task_list"),
        ("?", "help", "Show help", "global"),
        ("q", "quit", "Quit application", "global"),
        ("j", "next_task", "Select next task", "task_list"),
        ("k", "prev_task", "Select previous task", "task_list"),
        ("Enter", "open_task", "Open task detail", "task_list"),
        ("Esc", "back", "Go back", "global"),
    ]
    for key, action, desc, ctx in defaults:
        sm.bind(key, action, desc, ctx)
    return sm


def merge_maps(*maps: ShortcutMap) -> ShortcutMap:
    result = ShortcutMap()
    for m in maps:
        for s in m.all_bindings():
            result.bind(s.key, s.action, s.description, s.context)
    return result


def conflicts(map1: ShortcutMap, map2: ShortcutMap) -> List[str]:
    keys1 = set(map1._bindings.keys())
    keys2 = set(map2._bindings.keys())
    return sorted(keys1 & keys2)
