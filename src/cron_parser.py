"""Cron expression parser for scheduled tasks."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set


@dataclass
class CronField:
    """A single cron field (minute, hour, day, month, weekday)."""
    raw: str
    values: Set[int] = field(default_factory=set)

    @classmethod
    def parse(cls, raw: str, min_val: int, max_val: int) -> "CronField":
        """Parse a cron field string into allowed values."""
        values = set()
        for part in raw.split(","):
            part = part.strip()
            if part == "*":
                values.update(range(min_val, max_val + 1))
            elif "/" in part:
                base, step = part.split("/")
                step = int(step)
                if base == "*":
                    start = min_val
                else:
                    start = int(base)
                values.update(range(start, max_val + 1, step))
            elif "-" in part:
                start, end = part.split("-")
                values.update(range(int(start), int(end) + 1))
            else:
                values.add(int(part))
        return cls(raw=raw, values=values)

    def matches(self, value: int) -> bool:
        """Check if a value matches this field."""
        return value in self.values


class CronExpression:
    """A parsed cron expression."""
    def __init__(self, expression: str):
        self.expression = expression
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
        self.minute = CronField.parse(parts[0], 0, 59)
        self.hour = CronField.parse(parts[1], 0, 23)
        self.day = CronField.parse(parts[2], 1, 31)
        self.month = CronField.parse(parts[3], 1, 12)
        self.weekday = CronField.parse(parts[4], 0, 6)

    def matches(self, dt: datetime) -> bool:
        """Check if a datetime matches this cron expression."""
        return (self.minute.matches(dt.minute) and
                self.hour.matches(dt.hour) and
                self.day.matches(dt.day) and
                self.month.matches(dt.month) and
                self.weekday.matches(dt.weekday()))

    def next_run(self, from_dt: datetime = None, max_iterations: int = 366 * 24 * 60) -> Optional[datetime]:
        """Calculate the next execution time after from_dt."""
        if from_dt is None:
            from_dt = datetime.now(timezone.utc)
        dt = from_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
        for _ in range(max_iterations):
            if self.matches(dt):
                return dt
            dt += timedelta(minutes=1)
        return None

    def __repr__(self):
        return f"CronExpression('{self.expression}')"


def parse_cron(expression: str) -> CronExpression:
    """Parse a cron expression string."""
    return CronExpression(expression)


def matches_cron(expression: str, dt: datetime) -> bool:
    """Check if a datetime matches a cron expression."""
    return parse_cron(expression).matches(dt)


def next_run(expression: str, from_dt: datetime = None) -> Optional[datetime]:
    """Get the next run time for a cron expression."""
    return parse_cron(expression).next_run(from_dt)


def validate_cron(expression: str) -> bool:
    """Validate that a cron expression is well-formed."""
    try:
        parse_cron(expression)
        return True
    except (ValueError, IndexError):
        return False


def cron_description(expression: str) -> str:
    """Generate a human-readable description of a cron expression."""
    try:
        cron = parse_cron(expression)
        parts = expression.split()
        if parts[0] == "*" and parts[1] == "*" and parts[2] == "*" and parts[3] == "*" and parts[4] == "*":
            return "Every minute"
        elif parts[0] != "*" and parts[1] == "*" and parts[2] == "*":
            return f"Every hour at minute {parts[0]}"
        elif parts[0] == "0" and parts[1] != "*" and parts[2] == "*":
            return f"Every day at {parts[1]}:00"
        elif parts[0] == "0" and parts[1] != "*" and parts[4] != "*":
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_names = [days[int(d)] for d in parts[4].split(",")]
            return f"Every {','.join(day_names)} at {parts[1]}:00"
        else:
            return f"Custom: {expression}"
    except (ValueError, IndexError):
        return f"Invalid: {expression}"


COMMON_CRONS = {
    "every_minute": "* * * * *",
    "hourly": "0 * * * *",
    "daily_midnight": "0 0 * * *",
    "daily_9am": "0 9 * * *",
    "weekly_monday": "0 9 * * 1",
    "monthly_first": "0 0 1 * *",
    "quarterly": "0 0 1 1,4,7,10 *",
}
