"""Enhanced dependency graph with critical path analysis."""
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple


class EnhancedDependencyGraph:
    """Dependency graph with weighted edges and analysis capabilities."""
    def __init__(self):
        self._edges: Dict[int, Dict[int, float]] = defaultdict(dict)
        self._reverse: Dict[int, Set[int]] = defaultdict(set)
        self._nodes: Set[int] = set()
        self._weights: Dict[int, float] = {}

    def add_node(self, node_id, weight=1.0):
        self._nodes.add(node_id)
        self._weights[node_id] = weight

    def add_edge(self, from_id, to_id, weight=1.0):
        self.add_node(from_id)
        self.add_node(to_id)
        self._edges[from_id][to_id] = weight
        self._reverse[to_id].add(from_id)

    def remove_edge(self, from_id, to_id):
        if to_id in self._edges.get(from_id, {}):
            del self._edges[from_id][to_id]
            self._reverse[to_id].discard(from_id)
            return True
        return False

    def dependencies(self, node_id):
        return sorted(self._edges.get(node_id, {}).keys())

    def dependents(self, node_id):
        return sorted(self._reverse.get(node_id, set()))

    def all_nodes(self):
        return sorted(self._nodes)

    def node_count(self):
        return len(self._nodes)

    def edge_count(self):
        return sum(len(targets) for targets in self._edges.values())

    def edge_weight(self, from_id, to_id):
        return self._edges.get(from_id, {}).get(to_id)

    def has_edge(self, from_id, to_id):
        return to_id in self._edges.get(from_id, {})

    def roots(self):
        return sorted(n for n in self._nodes if not self._reverse.get(n))

    def leaves(self):
        return sorted(n for n in self._nodes if not self._edges.get(n))

    def in_degree(self, node_id):
        return len(self._reverse.get(node_id, set()))

    def out_degree(self, node_id):
        return len(self._edges.get(node_id, {}))


def topological_layers(graph):
    """Return nodes grouped into topological layers."""
    layers = []
    remaining = set(graph.all_nodes())
    while remaining:
        layer = [n for n in sorted(remaining) if graph.in_degree(n) == 0]
        if not layer:
            break  # cycle
        layers.append(layer)
        for node in layer:
            remaining.discard(node)
            for dep in graph.dependencies(node):
                graph._reverse[dep].discard(node)
    return layers


def critical_path_length(graph):
    """Find the longest path in the graph (by node count)."""
    nodes = graph.all_nodes()
    if not nodes:
        return 0
    longest = {}
    for node in nodes:
        deps = graph.dependencies(node)
        if not deps:
            longest[node] = 1
        else:
            longest[node] = max((longest.get(d, 0) for d in deps), default=0) + 1
    return max(longest.values()) if longest else 0


def critical_path(graph):
    """Return the critical path as a list of node IDs."""
    nodes = graph.all_nodes()
    if not nodes:
        return []
    longest = {}
    parent = {}
    for node in nodes:
        deps = graph.dependencies(node)
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


def bottleneck_nodes(graph, threshold=3):
    """Find nodes with many dependents (bottlenecks)."""
    result = []
    for node in graph.all_nodes():
        dep_count = len(graph.dependents(node))
        if dep_count >= threshold:
            result.append({"node": node, "dependent_count": dep_count})
    result.sort(key=lambda x: x["dependent_count"], reverse=True)
    return result


def graph_depth(graph):
    """Return the maximum depth of the graph."""
    return critical_path_length(graph)


def graph_breadth(graph):
    """Return the maximum breadth (widest layer)."""
    layers = topological_layers(graph)
    return max((len(layer) for layer in layers), default=0)


def graph_summary(graph):
    """Generate a summary of the graph."""
    return {
        "nodes": graph.node_count(),
        "edges": graph.edge_count(),
        "roots": len(graph.roots()),
        "leaves": len(graph.leaves()),
        "depth": graph_depth(graph),
        "breadth": graph_breadth(graph),
        "bottlenecks": len(bottleneck_nodes(graph)),
        "critical_path_length": critical_path_length(graph),
    }
