"""Tests for SLA tracking."""
import pytest
from datetime import datetime, timezone, timedelta
from src.sla import SLAPolicy, SLAManager, default_sla_manager


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, priority="medium", status="todo", created_hours_ago=1):
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.created_at = (datetime.now(timezone.utc) - timedelta(hours=created_hours_ago)).isoformat()


@pytest.fixture
def manager():
    m = SLAManager()
    m.set_policy("critical", response_time_hours=2, resolution_time_hours=8)
    m.set_policy("high", response_time_hours=8, resolution_time_hours=24)
    return m


def test_set_policy():
    m = SLAManager()
    p = m.set_policy("low", response_time_hours=48, resolution_time_hours=168)
    assert p.priority == "low"


def test_get_policy(manager):
    p = manager.get_policy("critical")
    assert p is not None
    assert p.resolution_time_hours == 8


def test_remove_policy(manager):
    assert manager.remove_policy("critical") is True
    assert manager.get_policy("critical") is None


def test_count(manager):
    assert manager.count() == 2


def test_check_sla_no_policy():
    m = SLAManager()
    task = FakeTask(1, priority="low")
    result = m.check_sla(task)
    assert result["has_policy"] is False


def test_check_sla_compliant(manager):
    task = FakeTask(1, priority="critical", created_hours_ago=1)
    result = manager.check_sla(task)
    assert result["response_breached"] is False
    assert result["resolution_breached"] is False


def test_check_sla_response_breached(manager):
    task = FakeTask(1, priority="critical", created_hours_ago=5)
    result = manager.check_sla(task)
    assert result["response_breached"] is True


def test_check_sla_resolution_breached(manager):
    task = FakeTask(1, priority="critical", created_hours_ago=10)
    result = manager.check_sla(task)
    assert result["resolution_breached"] is True


def test_check_sla_done_not_breached(manager):
    task = FakeTask(1, priority="critical", status="done", created_hours_ago=100)
    result = manager.check_sla(task)
    assert result["response_breached"] is False
    assert result["resolution_breached"] is False


def test_breached_tasks(manager):
    tasks = [
        FakeTask(1, "critical", created_hours_ago=1),
        FakeTask(2, "critical", created_hours_ago=10),
        FakeTask(3, "high", created_hours_ago=30),
    ]
    breached = manager.breached_tasks(tasks)
    assert len(breached) == 2


def test_at_risk_tasks(manager):
    tasks = [
        FakeTask(1, "critical", created_hours_ago=6),
        FakeTask(2, "critical", created_hours_ago=1),
    ]
    at_risk = manager.at_risk_tasks(tasks, threshold_percent=0.7)
    assert len(at_risk) == 1
    assert at_risk[0]["task_id"] == 1


def test_compliance_report(manager):
    tasks = [
        FakeTask(1, "critical", created_hours_ago=1),
        FakeTask(2, "critical", created_hours_ago=10),
    ]
    report = manager.compliance_report(tasks)
    assert report["total_tasks"] == 2
    assert report["breached"] == 1
    assert report["compliant"] == 1


def test_default_sla_manager():
    m = default_sla_manager()
    assert m.count() == 4
    assert m.get_policy("critical").response_time_hours == 2
