"""Tests for workload balancer."""
import pytest
from src.workload_balancer import (
    WorkloadEntry, WorkloadBalancer, rebalance_report,
)


@pytest.fixture
def balancer():
    b = WorkloadBalancer()
    b.add_member("alice", capacity=5)
    b.add_member("bob", capacity=5)
    b.add_member("charlie", capacity=3)
    return b


def test_workload_entry():
    w = WorkloadEntry(member="alice", task_ids=[1, 2, 3], capacity=5)
    assert w.load == 3
    assert w.utilization == 60.0
    assert w.is_overloaded is False
    assert w.has_capacity is True


def test_workload_entry_overloaded():
    w = WorkloadEntry(member="alice", task_ids=[1, 2, 3, 4, 5, 6], capacity=5)
    assert w.is_overloaded is True
    assert w.has_capacity is False


def test_add_member(balancer):
    assert balancer.member_count() == 3


def test_assign(balancer):
    balancer.assign("alice", 1)
    assert balancer.get("alice").load == 1


def test_assign_new_member():
    b = WorkloadBalancer()
    b.assign("new_person", 1)
    assert b.get("new_person") is not None


def test_unassign(balancer):
    balancer.assign("alice", 1)
    assert balancer.unassign("alice", 1) is True
    assert balancer.get("alice").load == 0
    assert balancer.unassign("alice", 999) is False


def test_total_tasks(balancer):
    balancer.assign("alice", 1)
    balancer.assign("bob", 2)
    assert balancer.total_tasks() == 2


def test_avg_load(balancer):
    balancer.assign("alice", 1)
    balancer.assign("bob", 2)
    assert balancer.avg_load() == pytest.approx(1.0, abs=0.1)


def test_max_load_member(balancer):
    balancer.assign("alice", 1)
    balancer.assign("alice", 2)
    balancer.assign("bob", 3)
    assert balancer.max_load_member().member == "alice"


def test_min_load_member(balancer):
    balancer.assign("alice", 1)
    assert balancer.min_load_member().member in ("bob", "charlie")


def test_overloaded(balancer):
    for i in range(6):
        balancer.assign("charlie", i)
    assert len(balancer.overloaded()) == 1


def test_available(balancer):
    assert len(balancer.available()) == 3


def test_balance(balancer):
    tasks = list(range(10))
    assignments = balancer.balance(tasks)
    assert len(assignments) == 10
    assert balancer.total_tasks() == 10


def test_balance_empty_team():
    b = WorkloadBalancer()
    assignments = b.balance([1, 2, 3])
    assert assignments == {}


def test_rebalance(balancer):
    for i in range(6):
        balancer.assign("charlie", i)
    moves = balancer.rebalance()
    assert len(moves) >= 1
    assert len(balancer.overloaded()) == 0


def test_rebalance_log(balancer):
    balancer.balance([1, 2, 3])
    assert len(balancer.rebalance_log()) >= 1


def test_rebalance_report(balancer):
    balancer.assign("alice", 1)
    report = rebalance_report(balancer)
    assert report["members"] == 3
    assert "workloads" in report
    assert "avg_load" in report
