"""Tests for delegation and escalation."""
import pytest
from src.delegation import (
    DelegationRule, DelegationEngine, Escalation,
    delegation_report, default_delegation_engine,
)


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id=1, priority="medium", status="todo", tags=None, assignee=None):
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        self.assignee = assignee


@pytest.fixture
def engine():
    e = DelegationEngine()
    e.add_rule("Critical", lambda t: t.priority.value == "critical", "tech_lead", priority=10)
    e.add_rule("Bug", lambda t: "bug" in (t.tags or []), "qa_team", priority=5)
    return e


def test_delegation_rule_matches():
    rule = DelegationRule(id=1, name="test", condition=lambda t: True, target_assignee="alice")
    assert rule.matches(FakeTask(1)) is True


def test_delegation_rule_disabled():
    rule = DelegationRule(id=1, name="test", condition=lambda t: True, target_assignee="alice")
    rule.enabled = False
    assert rule.matches(FakeTask(1)) is False


def test_add_rule():
    e = DelegationEngine()
    rule = e.add_rule("Test", lambda t: True, "alice")
    assert rule.id == 1
    assert rule.name == "Test"


def test_remove_rule(engine):
    assert engine.remove_rule(1) is True
    assert engine.get_rule(1) is None


def test_all_rules_sorted(engine):
    rules = engine.all_rules()
    assert rules[0].priority >= rules[1].priority


def test_delegate_critical(engine):
    task = FakeTask(1, priority="critical")
    result = engine.delegate(task)
    assert result["delegated"] is True
    assert task.assignee == "tech_lead"


def test_delegate_bug(engine):
    task = FakeTask(1, priority="medium", tags=["bug"])
    result = engine.delegate(task)
    assert result["delegated"] is True
    assert task.assignee == "qa_team"


def test_delegate_no_match(engine):
    task = FakeTask(1, priority="low", tags=["docs"])
    result = engine.delegate(task)
    assert result["delegated"] is False


def test_escalate(engine):
    task = FakeTask(1, assignee="alice")
    esc = engine.escalate(task, level=2, reason="Stuck")
    assert esc.level == 2
    assert task.assignee == "manager_l2"


def test_escalations_for_task(engine):
    task = FakeTask(1, assignee="alice")
    engine.escalate(task, level=1)
    engine.escalate(task, level=2)
    assert len(engine.escalations_for_task(1)) == 2


def test_enable_disable(engine):
    assert engine.disable_rule(1) is True
    task = FakeTask(1, priority="critical")
    assert engine.delegate(task)["delegated"] is False
    engine.enable_rule(1)
    assert engine.delegate(task)["delegated"] is True


def test_delegation_report(engine):
    task = FakeTask(1, priority="critical")
    engine.delegate(task)
    report = delegation_report(engine, [task])
    assert report["total_rules"] == 2
    assert report["fired_rules"] == 1


def test_default_delegation_engine():
    e = default_delegation_engine()
    assert e.rule_count() == 3
    task = FakeTask(1, priority="critical")
    result = e.delegate(task)
    assert result["to"] == "tech_lead"


def test_fired_count_increments(engine):
    task = FakeTask(1, priority="critical")
    engine.delegate(task)
    assert engine.get_rule(1).fired_count == 1
