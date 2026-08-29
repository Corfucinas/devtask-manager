"""Tests for task scheduler."""
import pytest
from datetime import datetime, timezone, timedelta
from src.task_scheduler_v2 import (
    ScheduledJob, TaskSchedulerV2, scheduler_report, default_scheduler,
)


@pytest.fixture
def scheduler():
    s = TaskSchedulerV2()
    s.schedule("One-time job", operation="notify",
               scheduled_time=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat())
    s.schedule("Recurring job", operation="notify",
               recurring=True, interval_seconds=3600)
    s.schedule("Future job", operation="notify",
               scheduled_time=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())
    return s


def test_schedule():
    s = TaskSchedulerV2()
    job = s.schedule("test", operation="notify")
    assert job.id == 1
    assert job.name == "test"


def test_get(scheduler):
    assert scheduler.get(1) is not None
    assert scheduler.get(999) is None


def test_all_jobs(scheduler):
    assert len(scheduler.all_jobs()) == 3


def test_due_jobs(scheduler):
    due = scheduler.due_jobs()
    assert len(due) == 1  # only the past one-time job


def test_execute_due(scheduler):
    results = scheduler.execute_due()
    assert len(results) == 1
    assert results[0]["executed"] is True


def test_execute_due_with_callback():
    s = TaskSchedulerV2()
    called = []
    def cb(task_ids, operation=None):
        called.append((task_ids, operation))
    s.schedule("Callback job", task_ids=[1, 2], operation="notify",
               scheduled_time=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
               callback=cb)
    s.execute_due()
    assert len(called) == 1
    assert called[0] == ([1, 2], "notify")


def test_cancel(scheduler):
    assert scheduler.cancel(1) is True
    assert scheduler.get(1).enabled is False
    assert scheduler.cancel(999) is False


def test_remove(scheduler):
    assert scheduler.remove(1) is True
    assert scheduler.get(1) is None
    assert scheduler.remove(999) is False


def test_count(scheduler):
    assert scheduler.count() == 3


def test_recurring_count(scheduler):
    assert scheduler.recurring_count() == 1


def test_clear(scheduler):
    scheduler.clear()
    assert scheduler.count() == 0


def test_recurring_reschedules():
    s = TaskSchedulerV2()
    job = s.schedule("Recurring", operation="notify", recurring=True, interval_seconds=60,
                      scheduled_time=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat())
    s.execute_due()
    assert job.executed_count == 1
    assert job.next_run is not None  # rescheduled
    assert job.enabled is True  # still enabled


def test_one_time_disables():
    s = TaskSchedulerV2()
    job = s.schedule("One-time", operation="notify",
                      scheduled_time=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat())
    s.execute_due()
    assert job.executed_count == 1
    assert job.enabled is False  # disabled after one-time


def test_scheduler_report(scheduler):
    report = scheduler_report(scheduler)
    assert report["total_jobs"] == 3
    assert report["recurring"] == 1
    assert "due" in report


def test_default_scheduler():
    s = default_scheduler()
    assert s.count() == 2
    assert s.recurring_count() == 2
