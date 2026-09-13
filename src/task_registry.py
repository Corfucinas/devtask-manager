"""Central registry for task operations."""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class RegistryEntry:
    """A registered callable."""
    name: str
    func: Callable
    namespace: str = "default"
    description: str = ""
    call_count: int = 0


class Registry:
    """A central named registry of callables."""
    def __init__(self):
        self._entries: Dict[str, RegistryEntry] = {}
        self._next_anon = 1

    def register(self, name: str, func: Callable, namespace: str = "default",
                 description: str = "") -> RegistryEntry:
        """Register a callable; overwrites existing name."""
        entry = RegistryEntry(name=name, func=func, namespace=namespace,
                              description=description)
        self._entries[f"{namespace}.{name}"] = entry
        return entry

    def unregister(self, name: str, namespace: str = "default") -> bool:
        key = f"{namespace}.{name}"
        if key in self._entries:
            del self._entries[key]
            return True
        return False

    def get(self, name: str, namespace: str = "default") -> Optional[RegistryEntry]:
        return self._entries.get(f"{namespace}.{name}")

    def has(self, name: str, namespace: str = "default") -> bool:
        return f"{namespace}.{name}" in self._entries

    def call(self, name: str, *args, namespace: str = "default", **kwargs) -> Any:
        """Invoke a registered callable by name."""
        entry = self.get(name, namespace)
        if not entry:
            raise KeyError(f"Not registered: {namespace}.{name}")
        entry.call_count += 1
        return entry.func(*args, **kwargs)

    def names(self, namespace: str = None) -> List[str]:
        """List registered names, optionally filtered by namespace."""
        return sorted(k for k in self._entries
                      if namespace is None or k.startswith(f"{namespace}."))

    def namespaces(self) -> List[str]:
        return sorted({e.namespace for e in self._entries.values()})

    def entries(self) -> List[RegistryEntry]:
        return list(self._entries.values())

    def entry_count(self) -> int:
        return len(self._entries)

    def clear(self, namespace: str = None):
        """Clear all or one namespace."""
        if namespace is None:
            self._entries.clear()
        else:
            keys = [k for k in self._entries
                    if k.startswith(f"{namespace}.")]
            for k in keys:
                del self._entries[k]

    def most_called(self, n: int = 5) -> List[RegistryEntry]:
        """Return the most-invoked entries."""
        return sorted(self._entries.values(), key=lambda e: -e.call_count)[:n]


def registry_report(registry: Registry) -> Dict:
    return {"total_entries": registry.entry_count(),
            "namespaces": registry.namespaces(),
            "total_calls": sum(e.call_count for e in registry.entries()),
            "most_called": [{"name": e.name, "calls": e.call_count}
                             for e in registry.most_called()]}
