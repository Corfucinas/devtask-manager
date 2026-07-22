"""Tests for task ageing analysis."""
import pytest
from datetime import datetime, timezone, timedelta
from src.ageing import (
    task_age, days_since_update, stale_tasks, age_buckets,
    oldest_task, average_age, ageing_report,
)


class FakeTask:
    def __init__(self, id, created_days_ago=0, updated_days_ago=0):
        self.id = id
        now = datetime.now(timezone.utc)
        self.created_at = (now - timedelta(days=created_days_ago)).isoformat()
        self.updated_at = (now - timedelta(days=updated_days_ago)).isoformat()


@pytest.fixture
def tasks():
    return [
        FakeTask(1, created_days_ago=3, updated_days_ago=1),
        FakeTask(2, created_days_ago=20, updated_days_ago=20),
        FakeTask(3, created_days_ago=100, updated_days_ago=50),
        FakeTask(4, created_days_ago=1, updated_days_ago=0),
    ]


def test_task_age(tasks):
    assert task_age(tasks[0]) == 3
    assert task_age(tasks[3]) == 1


def test_days_since_update(tasks):
    assert days_since_update(tasks[0]) == 1
    assert days_since_update(tasks[1]) == 20


def test_stale_tasks(tasks):
    stale = stale_tasks(tasks, threshold=14)
    assert len(stale) == 2
    ids = {t.id for t in stale}
    assert ids == {2, 3}


def test_stale_tasks_custom_threshold(tasks):
    stale = stale_tasks(tasks, threshold=40)
    assert len(stale) == 1
    assert stale[0].id == 3


def test_age_buckets(tasks):
    buckets = age_buckets(tasks)
    assert len(buckets["fresh"]) == 2
    assert len(buckets["aging"]) == 1
    assert len(buckets["old"]) == 1
    assert len(buckets["ancient"]) == 0


def test_oldest_task(tasks):
    oldest = oldest_task(tasks)
    assert oldest.id == 3


def test_oldest_task_empty():
    assert oldest_task([]) is None


def test_average_age(tasks):
    avg = average_age(tasks)
    assert avg == pytest.approx(31.0, abs=1.0)


def test_average_age_empty():
    assert average_age([]) == 0.0


def test_ageing_report(tasks):
    report = ageing_report(tasks)
    assert report["total"] == 4
    assert "average_age_days" in report
    assert report["stale_count"] == 2
    assert report["buckets"]["fresh"] == 2
