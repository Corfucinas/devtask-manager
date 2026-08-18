"""Tests for enhanced dependency graph."""
import pytest
from src.dependency_graph_v2 import (
    EnhancedDependencyGraph, topological_layers, critical_path_length,
    critical_path, bottleneck_nodes, graph_depth, graph_breadth, graph_summary,
)


@pytest.fixture
def graph():
    g = EnhancedDependencyGraph()
    g.add_edge(1, 2, weight=2.0)
    g.add_edge(2, 3, weight=1.0)
    g.add_edge(1, 3, weight=1.5)
    g.add_edge(4, 3, weight=1.0)
    g.add_edge(3, 5, weight=3.0)
    return g


def test_add_node():
    g = EnhancedDependencyGraph()
    g.add_node(5, weight=2.0)
    assert g.node_count() == 1


def test_add_edge(graph):
    assert graph.has_edge(1, 2)
    assert not graph.has_edge(2, 1)
    assert graph.edge_count() == 5


def test_edge_weight(graph):
    assert graph.edge_weight(1, 2) == 2.0
    assert graph.edge_weight(2, 3) == 1.0


def test_remove_edge(graph):
    assert graph.remove_edge(1, 2) is True
    assert not graph.has_edge(1, 2)
    assert graph.remove_edge(1, 2) is False


def test_dependencies(graph):
    assert graph.dependencies(1) == [2, 3]


def test_dependents(graph):
    assert graph.dependents(3) == [1, 2, 4]


def test_roots(graph):
    assert 5 in graph.roots()


def test_leaves(graph):
    assert 1 in graph.leaves()
    assert 4 in graph.leaves()


def test_in_degree(graph):
    assert graph.in_degree(3) == 3


def test_out_degree(graph):
    assert graph.out_degree(1) == 2


def test_topological_layers(graph):
    layers = topological_layers(graph)
    assert len(layers) >= 2


def test_critical_path_length(graph):
    length = critical_path_length(graph)
    assert length >= 3


def test_critical_path(graph):
    path = critical_path(graph)
    assert len(path) >= 3
    assert path[0] in graph.leaves()
    assert path[-1] in graph.roots()


def test_critical_path_empty():
    g = EnhancedDependencyGraph()
    assert critical_path(g) == []


def test_bottleneck_nodes(graph):
    bottlenecks = bottleneck_nodes(graph, threshold=2)
    assert len(bottlenecks) >= 1
    assert any(b["node"] == 3 for b in bottlenecks)


def test_graph_depth(graph):
    assert graph_depth(graph) >= 3


def test_graph_breadth(graph):
    assert graph_breadth(graph) >= 1


def test_graph_summary(graph):
    s = graph_summary(graph)
    assert s["nodes"] == 5
    assert s["edges"] == 5
    assert "depth" in s
    assert "critical_path_length" in s
