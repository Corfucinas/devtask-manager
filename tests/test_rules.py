"""Tests for automation rules engine."""
import pytest
from src.rules import (
    Rule, RuleEngine, make_condition_priority_high,
    make_action_set_tag, make_action_notify,
)


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id=1, priority="medium", status="todo"):
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = []


@pytest.fixture
def engine():
    e = RuleEngine()
    e.add_rule("High priority alert", "task.created",
               condition=make_condition_priority_high(),
               action=make_action_set_tag("urgent"))
    e.add_rule("Notify on complete", "task.completed",
               action=make_action_notify("email"))
    return e


def test_add_rule():
    e = RuleEngine()
    rule = e.add_rule("Test", "task.created")
    assert rule.id == 1
    assert rule.name == "Test"
    assert rule.enabled is True


def test_remove_rule(engine):
    assert engine.remove_rule(1) is True
    assert engine.get_rule(1) is None
    assert engine.remove_rule(999) is False


def test_get_rule(engine):
    rule = engine.get_rule(1)
    assert rule is not None
    assert rule.name == "High priority alert"


def test_all_rules(engine):
    assert len(engine.all_rules()) == 2


def test_rules_for_trigger(engine):
    created_rules = engine.rules_for_trigger("task.created")
    assert len(created_rules) == 1


def test_enable_disable(engine):
    assert engine.disable_rule(1) is True
    assert engine.get_rule(1).enabled is False
    assert len(engine.rules_for_trigger("task.created")) == 0
    assert engine.enable_rule(1) is True


def test_evaluate_condition_met(engine):
    task = FakeTask(1, priority="high")
    fired = engine.evaluate("task.created", task)
    assert len(fired) == 1
    assert "urgent" in task.tags
    assert fired[0].fired_count == 1


def test_evaluate_condition_not_met(engine):
    task = FakeTask(1, priority="low")
    fired = engine.evaluate("task.created", task)
    assert len(fired) == 0


def test_evaluate_no_matching_trigger(engine):
    task = FakeTask(1, priority="high")
    fired = engine.evaluate("task.updated", task)
    assert len(fired) == 0


def test_evaluate_action_notify(engine):
    task = FakeTask(1, status="done")
    fired = engine.evaluate("task.completed", task)
    assert len(fired) == 1
    assert hasattr(task, "notifications")
    assert len(task.notifications) == 1


def test_rule_count(engine):
    assert engine.rule_count() == 2


def test_enabled_count(engine):
    assert engine.enabled_count() == 2
    engine.disable_rule(1)
    assert engine.enabled_count() == 1


def test_fired_rules(engine):
    task = FakeTask(1, priority="high")
    engine.evaluate("task.created", task)
    fired = engine.fired_rules()
    assert len(fired) == 1


def test_make_action_set_tag():
    action = make_action_set_tag("review")
    task = FakeTask(1)
    action(task, {})
    assert "review" in task.tags
    action(task, {})
    assert task.tags.count("review") == 1


def test_disabled_rule_not_fired(engine):
    engine.disable_rule(1)
    task = FakeTask(1, priority="high")
    fired = engine.evaluate("task.created", task)
    assert len(fired) == 0
