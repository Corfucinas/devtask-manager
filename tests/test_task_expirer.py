"""Tests for task expirer."""
import pytest
from datetime import datetime, timezone, timedelta
from src.task_expirer import (
    ExpirationRule, TaskExpirer, expiration_report, default_expirer,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, priority="medium", status="todo", tags=None,
                 updated_days_ago=1):
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        self.updated_at = (datetime.now(timezone.utc) - timedelta(days=updated_days_ago)).isoformat()


@pytest.fixture
def expirer():
    e = TaskExpirer()
    e.add_rule("Old todos", max_age_days=30, status_filter="todo", action="archive")
    e.add_rule("Stale progress", max_age_days=60, status_filter="in-progress", action="flag")
    return e


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "medium", "todo", updated_days_ago=5),
        FakeTask(2, "high", "todo", updated_days_ago=40),
        FakeTask(3, "low", "in-progress", updated_days_ago=70),
        FakeTask(4, "medium", "done", updated_days_ago=100),
    ]


def test_expiration_rule_applies():
    rule = ExpirationRule(name="test", max_age_days=30, status_filter="todo")
    task = FakeTask(1, status="todo")
    assert rule.applies_to(task) is True


def test_expiration_rule_status_filter():
    rule = ExpirationRule(name="test", max_age_days=30, status_filter="todo")
    task = FakeTask(1, status="done")
    assert rule.applies_to(task) is False


def test_expiration_rule_priority_filter():
    rule = ExpirationRule(name="test", max_age_days=30, priority_filter="high")
    assert rule.applies_to(FakeTask(1, priority="high")) is True
    assert rule.applies_to(FakeTask(2, priority="low")) is False


def test_expiration_rule_tags_filter():
    rule = ExpirationRule(name="test", max_age_days=30, tags_filter=["bug"])
    assert rule.applies_to(FakeTask(1, tags=["bug", "ui"])) is True
    assert rule.applies_to(FakeTask(2, tags=["docs"])) is False


def test_expiration_rule_is_expired(expirer, tasks):
    rule = expirer._rules[0]
    assert rule.is_expired(tasks[1]) is True  # 40 days old todo
    assert rule.is_expired(tasks[0]) is False  # 5 days old todo


def test_expirer_add_rule():
    e = TaskExpirer()
    r = e.add_rule("test", max_age_days=10)
    assert r.name == "test"
    assert e.rule_count() == 1


def test_expirer_remove_rule(expirer):
    assert expirer.remove_rule("Old todos") is True
    assert expirer.rule_count() == 1
    assert expirer.remove_rule("nonexistent") is False


def test_find_expired(expirer, tasks):
    expired = expirer.find_expired(tasks)
    assert len(expired) == 2  # task 2 (40d todo) and task 3 (70d in-progress)
    ids = {e["task_id"] for e in expired}
    assert ids == {2, 3}


def test_expire_tasks_archive(expirer, tasks):
    expired = expirer.expire_tasks(tasks)
    task2 = next(t for t in tasks if t.id == 2)
    assert task2.status.value == "done"
    assert "archived" in task2.tags


def test_expire_tasks_flag(expirer, tasks):
    expired = expirer.expire_tasks(tasks)
    task3 = next(t for t in tasks if t.id == 3)
    assert "expired" in task3.tags


def test_expired_count(expirer, tasks):
    expirer.expire_tasks(tasks)
    assert expirer.expired_count() == 2


def test_clear_history(expirer, tasks):
    expirer.expire_tasks(tasks)
    expirer.clear_history()
    assert expirer.expired_count() == 0


def test_expiration_report(tasks):
    report = expiration_report(tasks)
    assert report["total_tasks"] == 4
    assert "expired_count" in report
    assert "by_action" in report


def test_default_expirer():
    e = default_expirer()
    assert e.rule_count() == 3
