"""Burndown chart data generation."""
from datetime import datetime, timezone, timedelta
from typing import List, Optional


def _parse(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def ideal_burndown(total_points: int, days: int) -> List[dict]:
    """Generate ideal burndown line (linear from total to zero)."""
    if days <= 0:
        return [{"day": 0, "ideal": total_points}]
    points = []
    for i in range(days + 1):
        remaining = total_points - (total_points / days) * i
        points.append({"day": i, "ideal": round(remaining, 1)})
    return points


def actual_burndown(tasks, total_points: int, start_date: str) -> List[dict]:
    """Generate actual remaining points per day from task completion data."""
    start = _parse(start_date)
    now = datetime.now(timezone.utc)
    days_elapsed = max(1, (now - start).days)

    results = []
    for day in range(days_elapsed + 1):
        day_start = start + timedelta(days=day)
        if day_start > now:
            break
        completed = 0
        for t in tasks:
            completed_at = getattr(t, "completed_at", None)
            if completed_at:
                ct = _parse(completed_at)
                if ct <= day_start:
                    status = t.status.value if hasattr(t.status, "value") else t.status
                    if status == "done":
                        completed += getattr(t, "story_points", 1) or 1
        remaining = max(0, total_points - completed)
        results.append({"day": day, "remaining": remaining})
    return results


def burndown_report(tasks, total_points: int, sprint_days: int, start_date: str) -> dict:
    """Generate a complete burndown report with ideal and actual data."""
    ideal = ideal_burndown(total_points, sprint_days)
    actual = actual_burndown(tasks, total_points, start_date)
    on_track = is_on_track(actual, ideal)
    return {
        "total_points": total_points,
        "sprint_days": sprint_days,
        "ideal": ideal,
        "actual": actual,
        "on_track": on_track,
    }


def is_on_track(actual: List[dict], ideal: List[dict]) -> bool:
    """Compare latest actual data point with ideal. True if actual <= ideal."""
    if not actual or not ideal:
        return True
    last_actual = actual[-1]["remaining"]
    day = actual[-1]["day"]
    ideal_at_day = next((p["ideal"] for p in ideal if p["day"] == day), None)
    if ideal_at_day is None:
        return True
    return last_actual <= ideal_at_day


def velocity_trend(tasks, sprint_days: int) -> List[dict]:
    """Calculate daily completion velocity."""
    now = datetime.now(timezone.utc)
    results = []
    for day in range(sprint_days):
        day_end = now - timedelta(days=sprint_days - day - 1)
        completed = 0
        for t in tasks:
            completed_at = getattr(t, "completed_at", None)
            status = t.status.value if hasattr(t.status, "value") else t.status
            if completed_at and status == "done":
                ct = _parse(completed_at)
                day_start = day_end.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end_full = day_start + timedelta(days=1)
                if day_start <= ct < day_end_full:
                    completed += getattr(t, "story_points", 1) or 1
        results.append({"day": day, "velocity": completed})
    return results


def projected_completion(tasks, total_points: int, elapsed_days: int) -> Optional[int]:
    """Project total days needed based on current velocity."""
    if elapsed_days <= 0:
        return None
    completed = sum(
        getattr(t, "story_points", 1) or 1
        for t in tasks
        if (t.status.value if hasattr(t.status, "value") else t.status) == "done"
    )
    if completed <= 0:
        return None
    daily_rate = completed / elapsed_days
    if daily_rate <= 0:
        return None
    return round(total_points / daily_rate)
