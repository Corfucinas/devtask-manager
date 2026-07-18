"""Tests for date utilities."""
import pytest
from datetime import datetime, timezone, timedelta
from src.date_utils import parse_date, format_relative, get_due_date_info, get_week_range

class TestParseDate:
    def test_iso_date(self):
        dt = parse_date("2026-07-15")
        assert dt.year == 2026
    def test_iso_datetime(self):
        dt = parse_date("2026-07-15T10:30:00+00:00")
        assert dt.hour == 10
    def test_slash(self):
        dt = parse_date("2026/07/15")
        assert dt.year == 2026
    def test_invalid(self):
        with pytest.raises(ValueError, match="Unable to parse"):
            parse_date("not a date")

class TestFormatRelative:
    def test_just_now(self):
        now = datetime.now(timezone.utc).isoformat()
        assert format_relative(now) == "just now"

class TestGetDueDateInfo:
    def test_overdue(self):
        past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        info = get_due_date_info(past)
        assert info["is_overdue"] is True
    def test_future(self):
        future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        info = get_due_date_info(future)
        assert info["is_overdue"] is False

class TestGetWeekRange:
    def test_returns_range(self):
        start, end = get_week_range()
        assert start < end
        assert (end - start).days == 6
