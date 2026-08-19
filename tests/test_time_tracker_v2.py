"""Tests for enhanced time tracking."""
import pytest
from datetime import datetime, timezone, timedelta
from src.time_tracker_v2 import (
    TimeEntry, TimeTrackerV2, daily_summary, weekly_summary, default_categories,
)


@pytest.fixture
def tracker():
    t = TimeTrackerV2()
    e = t.start(task_id=1, category="development", description="Fix bug")
    e.start = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    e.end = datetime.now(timezone.utc).isoformat()
    e2 = t.start(task_id=2, category="review", description="Review PR")
    e2.start = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    e2.end = datetime.now(timezone.utc).isoformat()
    return t


def test_time_entry_duration():
    e = TimeEntry(id=1, task_id=None,
                  start=(datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
                  end=datetime.now(timezone.utc).isoformat())
    assert e.duration_hours == pytest.approx(3.0, abs=0.1)


def test_time_entry_active():
    e = TimeEntry(id=1, task_id=None)
    assert e.is_active is True


def test_start():
    t = TimeTrackerV2()
    e = t.start(category="dev")
    assert e.id == 1
    assert e.category == "dev"
    assert t.active_entry() is not None


def test_stop(tracker):
    tracker.stop()
    assert tracker.active_entry() is None


def test_auto_stop_on_new_start():
    t = TimeTrackerV2()
    e1 = t.start(category="a")
    e2 = t.start(category="b")
    assert e1.end is not None
    assert e2.end is None


def test_get(tracker):
    assert tracker.get(1) is not None
    assert tracker.get(999) is None


def test_all_entries(tracker):
    assert len(tracker.all_entries()) == 2


def test_by_category(tracker):
    dev = tracker.by_category("development")
    assert len(dev) == 1


def test_by_task(tracker):
    task1 = tracker.by_task(1)
    assert len(task1) == 1


def test_total_hours(tracker):
    total = tracker.total_hours()
    assert total > 0


def test_hours_by_category(tracker):
    cats = tracker.hours_by_category()
    assert "development" in cats
    assert "review" in cats


def test_count(tracker):
    assert tracker.count() == 2


def test_delete(tracker):
    assert tracker.delete(1) is True
    assert tracker.get(1) is None
    assert tracker.count() == 1
    assert tracker.delete(999) is False


def test_daily_summary(tracker):
    s = daily_summary(tracker)
    assert s["entry_count"] == 2
    assert "by_category" in s


def test_weekly_summary(tracker):
    s = weekly_summary(tracker)
    assert "week_start" in s
    assert len(s["days"]) == 7


def test_default_categories():
    cats = default_categories()
    assert "development" in cats
    assert "testing" in cats
    assert len(cats) == 8
