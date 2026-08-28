"""Tests for enhanced task archiver."""
import pytest
from datetime import datetime, timezone, timedelta
from src.task_archiver_v2 import (
    RetentionPolicy, TaskArchiverV2, archive_report, default_archiver,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, priority="medium", status="todo", tags=None,
                 completed_days_ago=None, updated_days_ago=1):
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        now = datetime.now(timezone.utc)
        if completed_days_ago is not None:
            self.completed_at = (now - timedelta(days=completed_days_ago)).isoformat()
        else:
            self.completed_at = None
        self.updated_at = (now - timedelta(days=updated_days_ago)).isoformat()


@pytest.fixture
def archiver():
    a = TaskArchiverV2()
    a.add_policy("Completed 90 days", max_age_days=90, only_completed=True)
    a.add_policy("Low 30 days", max_age_days=30, only_completed=True, priority_filter="low")
    return a


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "medium", "done", completed_days_ago=100),
        FakeTask(2, "low", "done", completed_days_ago=40),
        FakeTask(3, "high", "todo", updated_days_ago=5),
        FakeTask(4, "medium", "done", completed_days_ago=10),
    ]


def test_retention_policy_should_archive():
    p = RetentionPolicy(name="test", max_age_days=30, only_completed=True)
    task = FakeTask(1, status="done", completed_days_ago=40)
    assert p.should_archive(task) is True


def test_retention_policy_not_completed():
    p = RetentionPolicy(name="test", max_age_days=30, only_completed=True)
    task = FakeTask(1, status="todo")
    assert p.should_archive(task) is False


def test_retention_policy_too_recent():
    p = RetentionPolicy(name="test", max_age_days=30, only_completed=True)
    task = FakeTask(1, status="done", completed_days_ago=10)
    assert p.should_archive(task) is False


def test_retention_policy_priority_filter():
    p = RetentionPolicy(name="test", max_age_days=30, priority_filter="low")
    assert p.should_archive(FakeTask(1, priority="low", status="done", completed_days_ago=40)) is True
    assert p.should_archive(FakeTask(2, priority="high", status="done", completed_days_ago=40)) is False


def test_archiver_add_policy():
    a = TaskArchiverV2()
    p = a.add_policy("test", max_age_days=60)
    assert p.name == "test"
    assert a.policy_count() == 1


def test_archiver_remove_policy(archiver):
    assert archiver.remove_policy("Completed 90 days") is True
    assert archiver.policy_count() == 1
    assert archiver.remove_policy("nonexistent") is False


def test_find_archivable(archiver, tasks):
    archivable = archiver.find_archivable(tasks)
    ids = {a["task_id"] for a in archivable}
    assert 1 in ids  # 100 days done
    assert 2 in ids  # 40 days low done


def test_archive(archiver, tasks):
    archiver.archive(tasks)
    task1 = next(t for t in tasks if t.id == 1)
    assert "archived" in task1.tags
    assert hasattr(task1, "_archived")


def test_archived_count(archiver, tasks):
    archiver.archive(tasks)
    assert archiver.archived_count() == 2


def test_archived_task_ids(archiver, tasks):
    archiver.archive(tasks)
    ids = archiver.archived_task_ids()
    assert 1 in ids
    assert 2 in ids


def test_clear_history(archiver, tasks):
    archiver.archive(tasks)
    archiver.clear_history()
    assert archiver.archived_count() == 0


def test_archive_report(tasks):
    report = archive_report(tasks)
    assert report["total_tasks"] == 4
    assert "archivable_count" in report
    assert "by_policy" in report


def test_default_archiver():
    a = default_archiver()
    assert a.policy_count() == 3
