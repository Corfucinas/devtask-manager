"""Activity streak tracker for daily engagement."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set


@dataclass
class StreakData:
    """Current streak information."""
    current_streak: int = 0
    longest_streak: int = 0
    total_active_days: int = 0
    last_active_date: Optional[str] = None
    streak_started: Optional[str] = None
    is_active_today: bool = False


class StreakTracker:
    """Tracks daily activity streaks."""
    def __init__(self):
        self._active_dates: Set[str] = set()
        self._activities: Dict[str, List[str]] = {}  # date -> activity types
        self._streak_data = StreakData()

    def record_activity(self, date: str = None, activity_type: str = "default"):
        """Record an activity for a specific date."""
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        date = date[:10]
        self._active_dates.add(date)
        if date not in self._activities:
            self._activities[date] = []
        self._activities[date].append(activity_type)
        self._update_streaks()

    def _update_streaks(self):
        """Recalculate streak data."""
        if not self._active_dates:
            return
        sorted_dates = sorted(self._active_dates)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

        self._streak_data.last_active_date = sorted_dates[-1]
        self._streak_data.total_active_days = len(self._active_dates)
        self._streak_data.is_active_today = today in self._active_dates

        current = 0
        streak_start = None
        check_date = today
        if today not in self._active_dates:
            check_date = yesterday

        for d in reversed(sorted_dates):
            if d == check_date:
                if current == 0:
                    streak_start = d
                current += 1
                check_date = (datetime.fromisoformat(d) - timedelta(days=1)).strftime("%Y-%m-%d")
            elif d < check_date:
                break

        self._streak_data.current_streak = current
        self._streak_data.streak_started = streak_start
        longest = self._calculate_longest_streak()
        self._streak_data.longest_streak = longest

    def _calculate_longest_streak(self) -> int:
        """Calculate the longest streak from active dates."""
        if not self._active_dates:
            return 0
        sorted_dates = sorted(self._active_dates)
        longest = 1
        current = 1
        for i in range(1, len(sorted_dates)):
            prev = datetime.fromisoformat(sorted_dates[i-1])
            curr = datetime.fromisoformat(sorted_dates[i])
            if (curr - prev).days == 1:
                current += 1
            else:
                longest = max(longest, current)
                current = 1
        return max(longest, current)

    def get_data(self) -> StreakData:
        return self._streak_data

    def active_dates(self) -> List[str]:
        return sorted(self._active_dates)

    def is_active_on(self, date: str) -> bool:
        return date[:10] in self._active_dates

    def activities_on(self, date: str) -> List[str]:
        return list(self._activities.get(date[:10], []))

    def total_active_days(self) -> int:
        return len(self._active_dates)

    def current_streak(self) -> int:
        return self._streak_data.current_streak

    def longest_streak(self) -> int:
        return self._streak_data.longest_streak

    def clear(self):
        self._active_dates = set()
        self._activities = {}
        self._streak_data = StreakData()


def streak_report(tracker: StreakTracker) -> Dict:
    """Generate a full streak report."""
    data = tracker.get_data()
    return {
        "current_streak": data.current_streak,
        "longest_streak": data.longest_streak,
        "total_active_days": data.total_active_days,
        "is_active_today": data.is_active_today,
        "last_active": data.last_active_date,
        "streak_started": data.streak_started,
        "activities_today": tracker.activities_on(
            datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ),
    }


def streak_emoji(streak: int) -> str:
    """Return an emoji representation of streak length."""
    if streak == 0: return "⚪"
    elif streak < 3: return "🔥"
    elif streak < 7: return "🔥🔥"
    elif streak < 14: return "🔥🔥🔥"
    elif streak < 30: return "🏆"
    else: return "👑"
