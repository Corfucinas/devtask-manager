"""Tests for velocity tracking."""
import pytest
from src.velocity import (
    VelocityTracker, VelocityPoint, velocity_report,
    velocity_by_sprint_name, compare_sprints,
)


@pytest.fixture
def tracker():
    t = VelocityTracker()
    t.record(1, "Sprint 1", 30, 25)
    t.record(2, "Sprint 2", 30, 28)
    t.record(3, "Sprint 3", 35, 32)
    t.record(4, "Sprint 4", 35, 35)
    t.record(5, "Sprint 5", 40, 38)
    return t


def test_record():
    t = VelocityTracker()
    p = t.record(1, "Sprint 1", 30, 25)
    assert p.sprint_id == 1
    assert p.completed_points == 25


def test_get(tracker):
    assert tracker.get(1) is not None
    assert tracker.get(999) is None


def test_count(tracker):
    assert tracker.count() == 5


def test_average_velocity(tracker):
    assert tracker.average_velocity() == pytest.approx(31.6, abs=0.5)


def test_average_velocity_last_n(tracker):
    assert tracker.average_velocity(last_n=3) == pytest.approx(35.0, abs=0.5)


def test_velocity_trend(tracker):
    assert tracker.velocity_trend() in ("increasing", "decreasing", "stable")


def test_forecast(tracker):
    f = tracker.forecast(3)
    assert len(f) == 3
    assert f[0]["confidence"] == "high"


def test_forecast_low_confidence():
    t = VelocityTracker()
    t.record(1, "S1", 20, 20)
    assert t.forecast(3)[0]["confidence"] == "low"


def test_accuracy(tracker):
    assert 0 < tracker.accuracy() <= 100


def test_min_velocity(tracker):
    assert tracker.min_velocity() == 25


def test_max_velocity(tracker):
    assert tracker.max_velocity() == 38


def test_standard_deviation(tracker):
    assert tracker.standard_deviation() > 0


def test_velocity_report(tracker):
    r = velocity_report(tracker)
    assert r["sprints_tracked"] == 5
    assert len(r["history"]) == 5


def test_velocity_by_sprint_name(tracker):
    assert velocity_by_sprint_name(tracker, "Sprint 3") == 32


def test_compare_sprints(tracker):
    r = compare_sprints(tracker, 1, 5)
    assert r["comparable"] is True
    assert r["delta"] == 13.0


def test_compare_sprints_missing(tracker):
    assert compare_sprints(tracker, 1, 999)["comparable"] is False
