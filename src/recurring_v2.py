"""Advanced recurring task scheduling with patterns."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional


@dataclass
class RecurrencePattern:
    """A recurring task schedule pattern."""
    id: int
    name: str
    frequency: str = "weekly"
    interval: int = 1
    days_of_week: List[int] = field(default_factory=list)
    day_of_month: int = 0
    start_date: str = ""
    end_date: Optional[str] = None
    max_occurrences: int = 0
    enabled: bool = True

    def __post_init__(self):
        if not self.start_date:
            self.start_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")


WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class RecurrenceScheduler:
    """Generates occurrence dates from recurrence patterns."""
    def __init__(self):
        self._patterns = {}
        self._next_id = 1

    def create(self, name, frequency="weekly", interval=1, days_of_week=None,
               day_of_month=0, start_date="", end_date=None, max_occurrences=0):
        p = RecurrencePattern(id=self._next_id, name=name, frequency=frequency,
                              interval=interval, days_of_week=days_of_week or [],
                              day_of_month=day_of_month, start_date=start_date,
                              end_date=end_date, max_occurrences=max_occurrences)
        self._patterns[self._next_id] = p
        self._next_id += 1
        return p

    def get(self, pattern_id):
        return self._patterns.get(pattern_id)

    def all_patterns(self):
        return list(self._patterns.values())

    def count(self):
        return len(self._patterns)

    def remove(self, pattern_id):
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            return True
        return False


def next_occurrence(pattern, from_date=None):
    if not pattern.enabled: return None
    if from_date is None: from_date = pattern.start_date
    current = datetime.fromisoformat(from_date + "T00:00:00+00:00") if "T" not in from_date else datetime.fromisoformat(from_date.replace("Z", "+00:00"))
    if pattern.frequency == "daily":
        next_date = current + timedelta(days=pattern.interval)
    elif pattern.frequency == "weekly":
        if pattern.days_of_week:
            next_date = current + timedelta(days=1)
            while next_date.weekday() not in pattern.days_of_week:
                next_date += timedelta(days=1)
        else:
            next_date = current + timedelta(weeks=pattern.interval)
    elif pattern.frequency == "monthly":
        if pattern.day_of_month > 0:
            month = current.month + pattern.interval
            year = current.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            try:
                next_date = current.replace(year=year, month=month, day=pattern.day_of_month)
            except ValueError:
                next_date = current + timedelta(days=30 * pattern.interval)
        else:
            next_date = current + timedelta(days=30 * pattern.interval)
    else:
        next_date = current + timedelta(days=pattern.interval)
    if pattern.end_date:
        end_str = pattern.end_date
        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00")) if "T" in end_str else datetime.fromisoformat(end_str + "T00:00:00+00:00")
        if next_date > end_dt: return None
    return next_date.strftime("%Y-%m-%d")


def generate_schedule(pattern, count=10, from_date=None):
    dates = []
    current = from_date or pattern.start_date
    for _ in range(count):
        if pattern.max_occurrences > 0 and len(dates) >= pattern.max_occurrences: break
        next_date = next_occurrence(pattern, current)
        if next_date is None: break
        dates.append(next_date)
        current = next_date
    return dates


def pattern_summary(pattern):
    return {"id": pattern.id, "name": pattern.name, "frequency": pattern.frequency,
            "interval": pattern.interval,
            "days_of_week": [WEEKDAY_NAMES[d] for d in pattern.days_of_week],
            "day_of_month": pattern.day_of_month, "start_date": pattern.start_date,
            "end_date": pattern.end_date, "max_occurrences": pattern.max_occurrences,
            "enabled": pattern.enabled}


def default_patterns():
    s = RecurrenceScheduler()
    s.create("Daily Standup", frequency="daily", interval=1)
    s.create("Weekly Review", frequency="weekly", interval=1, days_of_week=[4])
    s.create("Bi-weekly Retrospective", frequency="weekly", interval=2, days_of_week=[1])
    s.create("Monthly Report", frequency="monthly", interval=1, day_of_month=1)
    s.create("Quarterly Planning", frequency="monthly", interval=3, day_of_month=15)
    return s
