"""Tests for task dependency tracking system."""

import pytest
from src.dependencies import DependencyGraph


@pytest.fixture
def graph():
    return DependencyGraph()


class TestDependencyGraph:
    def test_add_dependency(self, graph):
        result = graph.add_dependency(2, 1)
        assert result is True
        assert graph.get_blockers(2) == [1]
        assert graph.get_blocked(1) == [2]
        assert graph.is_blocked(2) is True
        assert graph.is_blocked(1) is False

    def test_self_dependency_rejected(self, graph):
        result = graph.add_dependency(1, 1)
        assert result is False

    def test_cycle_detection(self, graph):
        graph.add_dependency(2, 1)
        graph.add_dependency(3, 2)
        result = graph.add_dependency(1, 3)
        assert result is False

    def test_remove_dependency(self, graph):
        graph.add_dependency(2, 1)
        graph.remove_dependency(2, 1)
        assert graph.get_blockers(2) == []
        assert graph.is_blocked(2) is False

    def test_get_ready_tasks(self, graph):
        graph.add_dependency(2, 1)
        graph.add_dependency(3, 1)
        ready = graph.get_ready_tasks([1, 2, 3], [1])
        assert ready == [1, 2, 3]
        ready = graph.get_ready_tasks([1, 2, 3], [])
        assert ready == [1]

    def test_execution_order_linear(self, graph):
        graph.add_dependency(2, 1)
        graph.add_dependency(3, 2)
        order = graph.get_execution_order([1, 2, 3])
        assert order == [1, 2, 3]

    def test_execution_order_diamond(self, graph):
        graph.add_dependency(3, 1)
        graph.add_dependency(3, 2)
        graph.add_dependency(4, 3)
        order = graph.get_execution_order([1, 2, 3, 4])
        assert order is not None
        assert order.index(1) < order.index(3)
        assert order.index(2) < order.index(3)
        assert order.index(3) < order.index(4)

    def test_execution_order_cycle_returns_none(self, graph):
        graph.add_dependency(2, 1)
        graph.add_dependency(3, 2)
        graph._blocked_by[1].add(3)
        graph._blocks[3].add(1)
        order = graph.get_execution_order([1, 2, 3])
        assert order is None

    def test_serialization(self, graph):
        graph.add_dependency(2, 1)
        graph.add_dependency(3, 1)
        data = graph.to_dict()
        restored = DependencyGraph.from_dict(data)
        assert restored.get_blockers(2) == [1]
        assert restored.get_blocked(1) == [2, 3]
