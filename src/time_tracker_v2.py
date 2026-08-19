"""Enhanced time tracking with categories."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


@dataclass
class TimeEntry:
    """A time tracking entry."""
    id: int
    task_id: Optional[int]
    category: str = "general"
    start: str = ""
    end: Optional[str] = None
    description: str = ""
    billable: bool = True

    def __post_init__(self):
        if not self.start:
            self.start = datetime.now(timezone.utc).isoformat()

    @property
    def duration_hours(self) -> float:
        """Calculate duration in hours."""
        if not self.end:
            return 0.0
        try:
            start_dt = datetime.fromisoformat(self.start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(self.end.replace("Z", "+00:00"))
            return round((end_dt - start_dt).total_seconds() / 3600, 2)
        except (ValueError, TypeError):
            return 0.0

    @property
    def is_active(self) -> bool:
        """Check if this entry is currently active."""
        return self.end is None


class TimeTrackerV2:
    """Enhanced time tracker with categories."""
    def __init__(self):
        self._entries: Dict[int, TimeEntry] = {}
        self._next_id = 1
        self._active: Optional[int] = None

    def start(self, task_id=None, category="general", description=""):
        """Start a new time entry."""
        if self._active is not None:
            self.stop()
        entry = TimeEntry(id=self._next_id, task_id=task_id, category=category,
                          description=description)
        self._entries[self._next_id] = entry
        self._active = self._next_id
        self._next_id += 1
        return entry

    def stop(self):
        """Stop the active time entry."""
        if self._active is None:
            return None
        entry = self._entries.get(self._active)
        if entry:
            entry.end = datetime.now(timezone.utc).isoformat()
        self._active = None
        return entry

    def get(self, entry_id):
        return self._entries.get(entry_id)

    def all_entries(self):
        return list(self._entries.values())

    def active_entry(self):
        """Return the currently active entry."""
        if self._active is None:
            return None
        return self._entries.get(self._active)

    def by_category(self, category):
        return [e for e in self._entries.values() if e.category == category]

    def by_task(self, task_id):
        return [e for e in self._entries.values() if e.task_id == task_id]

    def total_hours(self):
        """Total tracked hours."""
        return round(sum(e.duration_hours for e in self._entries.values()), 2)

    def hours_by_category(self):
        """Hours grouped by category."""
        result = {}
        for e in self._entries.values():
            h = e.duration_hours
            result[e.category] = round(result.get(e.category, 0) + h, 2)
        return result

    def count(self):
        return len(self._entries)

    def delete(self, entry_id):
        if entry_id in self._entries:
            del self._entries[entry_id]
            if self._active == entry_id:
                self._active = None
            return True
        return False


def daily_summary(tracker, date=None):
    """Generate a daily time breakdown."""
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = [e for e in tracker.all_entries()
               if e.start.startswith(date)]
    by_cat = {}
    for e in entries:
        h = e.duration_hours
        by_cat[e.category] = round(by_cat.get(e.category, 0) + h, 2)
    return {"date": date, "entry_count": len(entries),
            "total_hours": round(sum(e.duration_hours for e in entries), 2),
            "by_category": by_cat}


def weekly_summary(tracker, week_start=None):
    """Generate a weekly time report."""
    if week_start is None:
        today = datetime.now(timezone.utc)
        week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    start_dt = datetime.fromisoformat(week_start)
    days = []
    for i in range(7):
        day = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
        days.append(daily_summary(tracker, day))
    return {"week_start": week_start, "days": days,
            "total_hours": round(sum(d["total_hours"] for d in days), 2)}


def default_categories():
    """Return common time tracking categories."""
    return ["development", "review", "meetings", "planning",
            "documentation", "debugging", "testing", "research"]
