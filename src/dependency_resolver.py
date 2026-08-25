"""Dependency resolver with topological ordering."""
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


class DependencyResolver:
    """Resolves task execution order based on dependencies."""
    def __init__(self):
        self._deps: Dict[int, Set[int]] = defaultdict(set)
        self._reverse: Dict[int, Set[int]] = defaultdict(set)
        self._nodes: Set[int] = set()

    def add_node(self, node_id: int):
        self._nodes.add(node_id)

    def add_dependency(self, task_id: int, depends_on: int):
        """Add a dependency: task_id depends on depends_on."""
        self.add_node(task_id)
        self.add_node(depends_on)
        self._deps[task_id].add(depends_on)
        self._reverse[depends_on].add(task_id)

    def remove_dependency(self, task_id: int, depends_on: int) -> bool:
        if depends_on in self._deps.get(task_id, set()):
            self._deps[task_id].discard(depends_on)
            self._reverse[depends_on].discard(task_id)
            return True
        return False

    def dependencies_of(self, task_id: int) -> List[int]:
        return sorted(self._deps.get(task_id, set()))

    def dependents_of(self, task_id: int) -> List[int]:
        return sorted(self._reverse.get(task_id, set()))

    def all_nodes(self) -> List[int]:
        return sorted(self._nodes)

    def node_count(self) -> int:
        return len(self._nodes)

    def can_execute(self, task_id: int, completed: Set[int]) -> bool:
        """Check if all dependencies of a task are completed."""
        return self._deps.get(task_id, set()).issubset(completed)

    def ready_tasks(self, completed: Set[int]) -> List[int]:
        """Return tasks whose dependencies are all completed."""
        return sorted(n for n in self._nodes
                      if n not in completed and self.can_execute(n, completed))

    def resolve_order(self) -> List[int]:
        """Compute topological execution order. Returns [] if cycle exists."""
        in_degree = {n: len(self._deps.get(n, set())) for n in self._nodes}
        queue = deque(sorted(n for n, d in in_degree.items() if d == 0))
        result = []
        while queue:
            current = queue.popleft()
            result.append(current)
            for dependent in sorted(self._reverse.get(current, set())):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        if len(result) != len(self._nodes):
            return []
        return result

    def resolve_layers(self) -> List[List[int]]:
        """Return execution layers (tasks that can run in parallel)."""
        in_degree = {n: len(self._deps.get(n, set())) for n in self._nodes}
        layers = []
        remaining = set(self._nodes)
        while remaining:
            layer = sorted(n for n in remaining if in_degree[n] == 0)
            if not layer:
                break
            layers.append(layer)
            for node in layer:
                remaining.discard(node)
                for dep in self._reverse.get(node, set()):
                    in_degree[dep] -= 1
        return layers

    def has_cycle(self) -> bool:
        return len(self.resolve_order()) == 0 and len(self._nodes) > 0

    def critical_path(self) -> List[int]:
        """Find the longest dependency chain."""
        order = self.resolve_order()
        if not order:
            return []
        longest = {}
        parent = {}
        for node in order:
            deps = self.dependencies_of(node)
            if not deps:
                longest[node] = 1
                parent[node] = None
            else:
                best = 0
                best_parent = None
                for d in deps:
                    if longest.get(d, 0) > best:
                        best = longest[d]
                        best_parent = d
                longest[node] = best + 1
                parent[node] = best_parent
        if not longest:
            return []
        end = max(longest, key=longest.get)
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = parent.get(current)
        return list(reversed(path))


def resolution_report(resolver: DependencyResolver) -> Dict:
    """Generate a full dependency resolution report."""
    order = resolver.resolve_order()
    layers = resolver.resolve_layers()
    critical = resolver.critical_path()
    return {
        "total_tasks": resolver.node_count(),
        "has_cycle": resolver.has_cycle(),
        "execution_order": order,
        "execution_layers": layers,
        "layer_count": len(layers),
        "critical_path": critical,
        "critical_path_length": len(critical),
        "root_tasks": [n for n in resolver.all_nodes() if not resolver.dependencies_of(n)],
        "leaf_tasks": [n for n in resolver.all_nodes() if not resolver.dependents_of(n)],
    }


def default_resolver() -> DependencyResolver:
    """Create a resolver with sample dependencies."""
    r = DependencyResolver()
    r.add_dependency(1, 3)  # 1 depends on 3
    r.add_dependency(2, 3)  # 2 depends on 3
    r.add_dependency(3, 4)  # 3 depends on 4
    r.add_dependency(5, 4)  # 5 depends on 4
    r.add_dependency(5, 1)  # 5 depends on 1
    return r
