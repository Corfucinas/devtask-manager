"""Tests for timezone helpers."""
import pytest
from datetime import datetime, timezone, timedelta
from src.timezones import (
    timezone_offset, convert_timezone, format_in_timezone,
    now_in_timezone, business_hours, is_weekend, day_of_week,
    time_until, start_of_day, end_of_day, list_timezones, timezone_diff,
)


def test_timezone_offset():
    assert timezone_offset("UTC") == 0
    assert timezone_offset("PST") == -8
    assert timezone_offset("JST") == 9
    assert timezone_offset("IST") == 5.5
    assert timezone_offset("unknown") == 0


def test_convert_timezone_same():
    ts = "2026-01-15T12:00:00+00:00"
    result = convert_timezone(ts, "UTC", "UTC")
    assert "12:00" in result


def test_convert_timezone_pst():
    ts = "2026-01-15T12:00:00+00:00"
    result = convert_timezone(ts, "UTC", "PST")
    dt = datetime.fromisoformat(result.replace("Z", "+00:00"))
    assert dt.hour == 4


def test_format_in_timezone():
    ts = "2026-01-15T12:00:00+00:00"
    formatted = format_in_timezone(ts, "UTC", "%Y-%m-%d %H:%M")
    assert "2026-01-15 12:00" == formatted


def test_now_in_timezone():
    result = now_in_timezone("UTC")
    dt = datetime.fromisoformat(result.replace("Z", "+00:00"))
    assert dt is not None


def test_business_hours_during():
    ts = "2026-01-15T10:00:00+00:00"
    assert business_hours(ts, "UTC") is True


def test_business_hours_after():
    ts = "2026-01-15T18:00:00+00:00"
    assert business_hours(ts, "UTC") is False


def test_business_hours_weekend():
    ts = "2026-01-17T10:00:00+00:00"
    assert business_hours(ts, "UTC") is False


def test_is_weekend_false():
    ts = "2026-01-15T12:00:00+00:00"
    assert is_weekend(ts, "UTC") is False


def test_is_weekend_true():
    ts = "2026-01-18T12:00:00+00:00"
    assert is_weekend(ts, "UTC") is True


def test_day_of_week():
    ts = "2026-01-15T12:00:00+00:00"
    assert day_of_week(ts, "UTC") == "Thursday"


def test_time_until_future():
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    result = time_until(future)
    assert "h" in result


def test_time_until_past():
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    assert time_until(past) == "past due"


def test_start_of_day():
    ts = "2026-01-15T14:30:00+00:00"
    start = start_of_day(ts, "UTC")
    assert "00:00:00" in start


def test_end_of_day():
    ts = "2026-01-15T14:30:00+00:00"
    end = end_of_day(ts, "UTC")
    assert "23:59:59" in end


def test_list_timezones():
    zones = list_timezones()
    assert "UTC" in zones
    assert "PST" in zones
    assert "JST" in zones


def test_timezone_diff():
    diff = timezone_diff("PST", "EST")
    assert diff == -3.0
    diff = timezone_diff("UTC", "JST")
    assert diff == -9.0
