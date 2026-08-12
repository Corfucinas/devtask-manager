"""Tests for task policy engine."""
import pytest
from datetime import datetime, timezone, timedelta
from src.policy import Policy, PolicyEngine, policy_report, default_policies


class FakeStatus:
    def __init__(self, value): self.value = value
class FakePriority:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id=1, title="Task", priority="medium", status="todo",
                 assignee=None, due_date=None, updated_days_ago=1):
        now = datetime.now(timezone.utc)
        self.id = id
        self.title = title
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.assignee = assignee
        self.due_date = due_date
        self.updated_at = (now - timedelta(days=updated_days_ago)).isoformat()


@pytest.fixture
def engine():
    e = PolicyEngine()
    e.add("No empty title", "Tasks must have titles", lambda t: not (t.title or "").strip(), "block", "critical")
    e.add("Critical needs assignee", "Critical needs assignee", lambda t: (t.priority.value == "critical" and not t.assignee), "block", "high")
    return e


def test_policy_evaluate():
    p = Policy(id=1, name="test", description="test", condition=lambda t: True)
    assert p.evaluate(FakeTask()) is True

def test_policy_disabled():
    p = Policy(id=1, name="test", description="test", condition=lambda t: True)
    p.enabled = False
    assert p.evaluate(FakeTask()) is False

def test_engine_add():
    e = PolicyEngine()
    p = e.add("Test", "desc", lambda t: False)
    assert p.id == 1

def test_engine_get(engine):
    assert engine.get(1) is not None
    assert engine.get(999) is None

def test_engine_remove(engine):
    assert engine.remove(1) is True
    assert engine.get(1) is None

def test_engine_count(engine):
    assert engine.count() == 2

def test_enforce_no_violation(engine):
    task = FakeTask(1, title="Task", priority="medium", assignee="alice")
    assert len(engine.enforce(task)) == 0

def test_enforce_empty_title(engine):
    task = FakeTask(1, title="")
    v = engine.enforce(task)
    assert len(v) == 1
    assert v[0]["action"] == "block"

def test_enforce_critical_no_assignee(engine):
    task = FakeTask(1, title="Task", priority="critical")
    v = engine.enforce(task)
    assert len(v) == 1

def test_enforce_batch(engine):
    tasks = [FakeTask(1, title=""), FakeTask(2, title="OK"), FakeTask(3, title="", priority="critical")]
    v = engine.enforce_batch(tasks)
    assert len(v) >= 2

def test_enable_disable(engine):
    assert engine.disable(1) is True
    task = FakeTask(1, title="")
    assert len(engine.enforce(task)) == 0
    engine.enable(1)
    assert len(engine.enforce(task)) == 1

def test_violations(engine):
    engine.enforce(FakeTask(1, title=""))
    assert engine.violation_count() == 1

def test_clear_violations(engine):
    engine.enforce(FakeTask(1, title=""))
    engine.clear_violations()
    assert engine.violation_count() == 0

def test_blocking_violations(engine):
    tasks = [FakeTask(1, title=""), FakeTask(2, title="OK")]
    b = engine.blocking_violations(tasks)
    assert len(b) == 1

def test_policy_report(engine):
    tasks = [FakeTask(1, title="OK"), FakeTask(2, title="", priority="critical")]
    r = policy_report(engine, tasks)
    assert r["total_tasks"] == 2
    assert r["total_violations"] >= 2

def test_default_policies():
    e = default_policies()
    assert e.count() == 4
    task = FakeTask(1, title="", priority="critical")
    assert len(e.enforce(task)) >= 2

def test_default_policies_compliant():
    e = default_policies()
    task = FakeTask(1, title="Good task", priority="medium", assignee="alice", due_date="2026-12-31T00:00:00+00:00")
    assert len(e.enforce(task)) == 0
