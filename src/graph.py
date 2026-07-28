"""Task dependency graph and cycle detection."""
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple


class DependencyGraph:
    """Directed acyclic graph for task dependencies."""

    def __init__(self):
        self._edges: Dict[int, Set[int]] = defaultdict(set)
        self._reverse: Dict[int, Set[int]] = defaultdict(set)
        self._nodes: Set[int] = set()

    def add_node(self, node_id: int) -> None:
        self._nodes.add(node_id)

    def add_edge(self, from_id: int, to_id: int) -> bool:
        self.add_node(from_id)
        self.add_node(to_id)
        if self._would_create_cycle(from_id, to_id):
            return False
        self._edges[from_id].add(to_id)
        self._reverse[to_id].add(from_id)
        return True

    def remove_edge(self, from_id: int, to_id: int) -> bool:
        if to_id in self._edges.get(from_id, set()):
            self._edges[from_id].discard(to_id)
            self._reverse[to_id].discard(from_id)
            return True
        return False

    def dependencies(self, node_id: int) -> List[int]:
        return sorted(self._edges.get(node_id, set()))

    def dependents(self, node_id: int) -> List[int]:
        return sorted(self._reverse.get(node_id, set()))

    def has_edge(self, from_id: int, to_id: int) -> bool:
        return to_id in self._edges.get(from_id, set())

    def all_nodes(self) -> List[int]:
        return sorted(self._nodes)

    def edge_count(self) -> int:
        return sum(len(targets) for targets in self._edges.values())

    def node_count(self) -> int:
        return len(self._nodes)

    def _would_create_cycle(self, from_id: int, to_id: int) -> bool:
        if from_id == to_id:
            return True
        visited = set()
        queue = deque([to_id])
        while queue:
            current = queue.popleft()
            if current == from_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            for dep in self._edges.get(current, set()):
                queue.append(dep)
        return False

    def roots(self) -> List[int]:
        return sorted(n for n in self._nodes if not self._reverse.get(n))

    def leaves(self) -> List[int]:
        return sorted(n for n in self._nodes if not self._edges.get(n))

    def reachable_from(self, node_id: int) -> Set[int]:
        visited = set()
        queue = deque([node_id])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for dep in self._edges.get(current, set()):
                queue.append(dep)
        return visited - {node_id}


def topological_sort(graph: DependencyGraph) -> List[int]:
    in_degree = {n: 0 for n in graph.all_nodes()}
    for node in graph.all_nodes():
        for dep in graph.dependencies(node):
            in_degree[dep] = in_degree.get(dep, 0)
            in_degree[node] = in_degree.get(node, 0) + 1
    queue = deque(sorted(n for n, d in in_degree.items() if d == 0))
    result = []
    visited = set()
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        result.append(current)
        for dep in graph.dependencies(current):
            in_degree[dep] -= 1
            if in_degree[dep] == 0 and dep not in visited:
                queue.append(dep)
    if len(result) != len(graph.all_nodes()):
        return []
    return result


def detect_cycles(graph: DependencyGraph) -> List[List[int]]:
    cycles = []
    visited = set()
    stack = []
    on_stack = set()

    def dfs(node):
        if node in on_stack:
            idx = stack.index(node)
            cycles.append(stack[idx:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        on_stack.add(node)
        stack.append(node)
        for dep in graph.dependencies(node):
            dfs(dep)
        stack.pop()
        on_stack.discard(node)

    for node in graph.all_nodes():
        if node not in visited:
            dfs(node)
    return cycles


def critical_path(graph: DependencyGraph) -> List[int]:
    sorted_nodes = topological_sort(graph)
    if not sorted_nodes:
        return []
    longest = {}
    parent = {}
    for node in sorted_nodes:
        deps = graph.dependencies(node)
        if not deps:
            longest[node] = 1
            parent[node] = None
        else:
            best = 0
            best_parent = None
            for dep in deps:
                if longest.get(dep, 0) > best:
                    best = longest[dep]
                    best_parent = dep
            longest[node] = best + 1
            parent[node] = best_parent
    if not longest:
        return []
    end_node = max(longest, key=longest.get)
    path = []
    current = end_node
    while current is not None:
        path.append(current)
        current = parent.get(current)
    return list(reversed(path))


def graph_summary(graph: DependencyGraph) -> dict:
    cycles = detect_cycles(graph)
    return {
        "nodes": graph.node_count(),
        "edges": graph.edge_count(),
        "roots": len(graph.roots()),
        "leaves": len(graph.leaves()),
        "cycles": len(cycles),
        "has_cycles": len(cycles) > 0,
        "is_dag": len(cycles) == 0,
    }
