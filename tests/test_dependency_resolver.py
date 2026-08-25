"""Tests for dependency resolver."""
import pytest
from src.dependency_resolver import DependencyResolver, resolution_report, default_resolver


@pytest.fixture
def resolver():
    r = DependencyResolver()
    r.add_dependency(1, 2)
    r.add_dependency(1, 3)
    r.add_dependency(2, 4)
    r.add_dependency(3, 4)
    r.add_dependency(5, 2)
    return r


def test_add_node():
    r = DependencyResolver()
    r.add_node(1)
    assert r.node_count() == 1


def test_add_dependency():
    r = DependencyResolver()
    r.add_dependency(1, 2)
    assert 2 in r.dependencies_of(1)
    assert 1 in r.dependents_of(2)


def test_remove_dependency(resolver):
    assert resolver.remove_dependency(1, 2) is True
    assert 2 not in resolver.dependencies_of(1)
    assert resolver.remove_dependency(1, 999) is False


def test_dependencies_of(resolver):
    deps = resolver.dependencies_of(1)
    assert deps == [2, 3]


def test_dependents_of(resolver):
    deps = resolver.dependents_of(2)
    assert deps == [1, 5]


def test_all_nodes(resolver):
    assert resolver.all_nodes() == [1, 2, 3, 4, 5]


def test_node_count(resolver):
    assert resolver.node_count() == 5


def test_can_execute(resolver):
    assert resolver.can_execute(4, set()) is True  # no deps
    assert resolver.can_execute(2, set()) is False  # depends on 4
    assert resolver.can_execute(2, {4}) is True


def test_ready_tasks(resolver):
    ready = resolver.ready_tasks(set())
    assert 4 in ready  # no deps
    assert 1 not in ready  # has deps


def test_resolve_order(resolver):
    order = resolver.resolve_order()
    assert len(order) == 5
    assert order.index(4) < order.index(2)  # 4 before 2
    assert order.index(4) < order.index(3)  # 4 before 3
    assert order.index(2) < order.index(1)  # 2 before 1


def test_resolve_order_cycle():
    r = DependencyResolver()
    r.add_dependency(1, 2)
    r.add_dependency(2, 3)
    r.add_dependency(3, 1)
    assert r.resolve_order() == []


def test_resolve_layers(resolver):
    layers = resolver.resolve_layers()
    assert len(layers) >= 2
    assert 4 in layers[0]  # no deps


def test_has_cycle_false(resolver):
    assert resolver.has_cycle() is False


def test_has_cycle_true():
    r = DependencyResolver()
    r.add_dependency(1, 2)
    r.add_dependency(2, 1)
    assert r.has_cycle() is True


def test_critical_path(resolver):
    path = resolver.critical_path()
    assert len(path) >= 2
    assert 4 in path


def test_critical_path_empty():
    r = DependencyResolver()
    assert r.critical_path() == []


def test_resolution_report(resolver):
    report = resolution_report(resolver)
    assert report["total_tasks"] == 5
    assert report["has_cycle"] is False
    assert "execution_order" in report
    assert "critical_path" in report


def test_default_resolver():
    r = default_resolver()
    assert r.node_count() == 5
    order = r.resolve_order()
    assert len(order) == 5
