"""Tests for priority-urgency matrix."""
import pytest
from datetime import datetime, timezone, timedelta
from src.matrix import (
    classify_task, matrix_distribution, tasks_by_quadrant,
    matrix_report, quadrant_summary, QUADRANTS,
)


class FakeStatus:
    def __init__(self, value): self.value = value
class FakePriority:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, priority="medium", status="todo", due_in_days=None,
                 dependents=None, tags=None):
        now = datetime.now(timezone.utc)
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.due_date = (now + timedelta(days=due_in_days)).isoformat() if due_in_days is not None else None
        self.dependents = dependents or []
        self.tags = tags or []


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "critical", "todo", due_in_days=1),  # do
        FakeTask(2, "high", "todo", due_in_days=14),     # schedule
        FakeTask(3, "low", "todo", due_in_days=1),       # delegate
        FakeTask(4, "low", "todo", due_in_days=30),      # delete
        FakeTask(5, "medium", "done"),                   # done
    ]


def test_classify_do(tasks):
    assert classify_task(tasks[0]) == "do"


def test_classify_schedule(tasks):
    assert classify_task(tasks[1]) == "schedule"


def test_classify_delegate(tasks):
    assert classify_task(tasks[2]) == "delegate"


def test_classify_delete(tasks):
    assert classify_task(tasks[3]) == "delete"


def test_classify_done(tasks):
    assert classify_task(tasks[4]) == "done"


def test_classify_no_due_date():
    task = FakeTask(1, "high")
    assert classify_task(task) == "schedule"  # important but not urgent


def test_classify_low_no_due():
    task = FakeTask(1, "low")
    assert classify_task(task) == "delete"


def test_matrix_distribution(tasks):
    dist = matrix_distribution(tasks)
    assert dist["do"] == 1
    assert dist["schedule"] == 1
    assert dist["delegate"] == 1
    assert dist["delete"] == 1
    assert dist["done"] == 1


def test_tasks_by_quadrant(tasks):
    groups = tasks_by_quadrant(tasks)
    assert len(groups["do"]) == 1
    assert len(groups["done"]) == 1


def test_matrix_report(tasks):
    report = matrix_report(tasks)
    assert report["total_tasks"] == 5
    assert "distribution" in report
    assert "percentages" in report
    assert "recommendation" in report


def test_matrix_report_empty():
    report = matrix_report([])
    assert report["total_tasks"] == 0


def test_quadrant_summary(tasks):
    s = quadrant_summary(tasks, "do")
    assert s["count"] == 1
    assert s["label"] == "Do First"
    assert 1 in s["task_ids"]


def test_important_by_dependents():
    task = FakeTask(1, "low", dependents=[1, 2, 3])
    assert classify_task(task) == "schedule"  # important due to dependents


def test_important_by_tags():
    task = FakeTask(1, "low", tags=["core"])
    assert classify_task(task) == "schedule"
