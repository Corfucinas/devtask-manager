"""Tests for time tracking."""
import time
import pytest
from src.timer import start_timer, stop_timer, session_duration, total_time, format_duration


class FakeTask:
    def __init__(self):
        self.time_entries = None


def test_start_timer():
    task = FakeTask()
    entry = start_timer(task)
    assert entry["start"] is not None
    assert entry["end"] is None
    assert len(task.time_entries) == 1


def test_stop_timer():
    task = FakeTask()
    start_timer(task)
    time.sleep(0.01)
    entry = stop_timer(task)
    assert entry is not None
    assert entry["end"] is not None


def test_stop_timer_no_active():
    task = FakeTask()
    result = stop_timer(task)
    assert result is None


def test_session_duration():
    entry = {"start": "2026-01-01T00:00:00+00:00", "end": "2026-01-01T00:05:00+00:00"}
    assert session_duration(entry) == 300


def test_total_time():
    task = FakeTask()
    task.time_entries = [
        {"start": "2026-01-01T00:00:00+00:00", "end": "2026-01-01T00:05:00+00:00"},
        {"start": "2026-01-01T01:00:00+00:00", "end": "2026-01-01T01:10:00+00:00"},
    ]
    assert total_time(task) == 900


def test_format_duration():
    assert format_duration(0) == "0m"
    assert format_duration(120) == "2m"
    assert format_duration(3661) == "1h 1m"
    assert format_duration(7200) == "2h 0m"
