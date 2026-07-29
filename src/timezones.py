"""Timezone conversion and display helpers."""
from datetime import datetime, timezone, timedelta
from typing import Optional


COMMON_TIMEZONES = {
    "UTC": 0, "PST": -8, "PDT": -7, "MST": -7, "CST": -6,
    "EST": -5, "EDT": -4, "GMT": 0, "CET": 1, "EET": 2,
    "IST": 5.5, "JST": 9, "AEST": 10, "NZST": 12,
}


def timezone_offset(tz: str) -> float:
    return COMMON_TIMEZONES.get(tz.upper(), 0.0)


def convert_timezone(timestamp: str, from_tz: str = "UTC", to_tz: str = "UTC") -> str:
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    from_offset = timedelta(hours=timezone_offset(from_tz))
    to_offset = timedelta(hours=timezone_offset(to_tz))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc_dt = dt - from_offset
    result = utc_dt + to_offset
    return result.isoformat()


def format_in_timezone(timestamp: str, tz: str = "UTC", fmt: str = "%Y-%m-%d %H:%M") -> str:
    converted = convert_timezone(timestamp, "UTC", tz)
    dt = datetime.fromisoformat(converted.replace("Z", "+00:00"))
    return dt.strftime(fmt)


def now_in_timezone(tz: str = "UTC") -> str:
    offset = timedelta(hours=timezone_offset(tz))
    tz_info = timezone(offset)
    return datetime.now(tz_info).isoformat()


def business_hours(timestamp: str, tz: str = "UTC") -> bool:
    converted = convert_timezone(timestamp, "UTC", tz)
    dt = datetime.fromisoformat(converted.replace("Z", "+00:00"))
    return 9 <= dt.hour < 17 and dt.weekday() < 5


def is_weekend(timestamp: str, tz: str = "UTC") -> bool:
    converted = convert_timezone(timestamp, "UTC", tz)
    dt = datetime.fromisoformat(converted.replace("Z", "+00:00"))
    return dt.weekday() >= 5


def day_of_week(timestamp: str, tz: str = "UTC") -> str:
    converted = convert_timezone(timestamp, "UTC", tz)
    dt = datetime.fromisoformat(converted.replace("Z", "+00:00"))
    return dt.strftime("%A")


def time_until(target_timestamp: str, from_tz: str = "UTC") -> str:
    now = datetime.now(timezone.utc)
    target = datetime.fromisoformat(target_timestamp.replace("Z", "+00:00"))
    delta = target - now
    if delta.total_seconds() < 0:
        return "past due"
    days = delta.days
    hours = int(delta.seconds / 3600)
    minutes = int((delta.seconds % 3600) / 60)
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def start_of_day(timestamp: str, tz: str = "UTC") -> str:
    converted = convert_timezone(timestamp, "UTC", tz)
    dt = datetime.fromisoformat(converted.replace("Z", "+00:00"))
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.isoformat()


def end_of_day(timestamp: str, tz: str = "UTC") -> str:
    converted = convert_timezone(timestamp, "UTC", tz)
    dt = datetime.fromisoformat(converted.replace("Z", "+00:00"))
    end = dt.replace(hour=23, minute=59, second=59, microsecond=0)
    return end.isoformat()


def list_timezones() -> list:
    return sorted(COMMON_TIMEZONES.keys())


def timezone_diff(tz_a: str, tz_b: str) -> float:
    return timezone_offset(tz_a) - timezone_offset(tz_b)
