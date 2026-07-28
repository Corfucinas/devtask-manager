"""Tests for dependency graph."""
import pytest
from src.graph import (
    DependencyGraph, topological_sort, detect_cycles,
    critical_path, graph_summary,
)


@pytest.fixture
def dag():
    g = DependencyGraph()
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(1, 3)
    g.add_edge(4, 3)
    return g


def test_add_node():
    g = DependencyGraph()
    g.add_node(5)
    assert g.node_count() == 1


def test_add_edge(dag):
    assert dag.has_edge(1, 2)
    assert not dag.has_edge(2, 1)
    assert dag.edge_count() == 4


def test_add_edge_self_loop():
    g = DependencyGraph()
    assert g.add_edge(1, 1) is False


def test_add_edge_cycle_prevented():
    g = DependencyGraph()
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    assert g.add_edge(3, 1) is False


def test_remove_edge(dag):
    assert dag.remove_edge(1, 2) is True
    assert not dag.has_edge(1, 2)
    assert dag.remove_edge(1, 2) is False


def test_dependencies(dag):
    assert dag.dependencies(1) == [2, 3]


def test_dependents(dag):
    assert dag.dependents(3) == [1, 2, 4]


def test_roots(dag):
    assert 3 in dag.roots()


def test_leaves(dag):
    assert 1 in dag.leaves()
    assert 4 in dag.leaves()


def test_reachable_from(dag):
    reachable = dag.reachable_from(1)
    assert 2 in reachable
    assert 3 in reachable
    assert 4 not in reachable


def test_topological_sort(dag):
    result = topological_sort(dag)
    assert len(result) == 4
    assert result.index(3) < result.index(2)
    assert result.index(3) < result.index(1)


def test_topological_sort_with_cycle():
    g = DependencyGraph()
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g._edges[3].add(1)
    g._reverse[1].add(3)
    assert topological_sort(g) == []


def test_detect_cycles_none(dag):
    assert detect_cycles(dag) == []


def test_detect_cycles_present():
    g = DependencyGraph()
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g._edges[3].add(1)
    g._reverse[1].add(3)
    cycles = detect_cycles(g)
    assert len(cycles) >= 1


def test_critical_path(dag):
    path = critical_path(dag)
    assert len(path) >= 2
    assert path[0] == 3


def test_critical_path_empty():
    g = DependencyGraph()
    assert critical_path(g) == []


def test_graph_summary(dag):
    summary = graph_summary(dag)
    assert summary["nodes"] == 4
    assert summary["is_dag"] is True
