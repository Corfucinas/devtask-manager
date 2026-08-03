"""Velocity-based completion projection."""
from datetime import datetime, timezone, timedelta
from typing import List, Optional


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def remaining_tasks(tasks):
    return [t for t in tasks if _get_status(t) != "done"]


def completed_count(tasks):
    return sum(1 for t in tasks if _get_status(t) == "done")


def velocity_trend(tasks, days=7):
    now = datetime.now(timezone.utc)
    results = []
    for i in range(days):
        day_start = now - timedelta(days=days - i - 1)
        day_end = day_start + timedelta(days=1)
        count = 0
        for t in tasks:
            completed_at = getattr(t, "completed_at", None)
            if completed_at and _get_status(t) == "done":
                ct = _parse(completed_at)
                if day_start <= ct < day_end:
                    count += 1
        results.append({"day": i, "date": day_start.strftime("%Y-%m-%d"), "completed": count})
    return results


def average_velocity(tasks, days=7):
    trend = velocity_trend(tasks, days)
    if not trend:
        return 0.0
    total = sum(d["completed"] for d in trend)
    return round(total / days, 2)


def velocity_std_dev(tasks, days=7):
    trend = velocity_trend(tasks, days)
    if not trend:
        return 0.0
    values = [d["completed"] for d in trend]
    avg = sum(values) / len(values)
    if len(values) < 2:
        return 0.0
    variance = sum((v - avg) ** 2 for v in values) / len(values)
    return round(variance ** 0.5, 2)


def confidence_interval(velocity, std_dev, confidence="95%"):
    multipliers = {"90%": 1.645, "95%": 1.96, "99%": 2.576}
    z = multipliers.get(confidence, 1.96)
    low = max(0, velocity - z * std_dev)
    high = velocity + z * std_dev
    return (round(low, 2), round(high, 2))


def project_completion(tasks, velocity_per_day):
    remaining = len(remaining_tasks(tasks))
    if velocity_per_day <= 0 or remaining == 0:
        return None
    days_needed = remaining / velocity_per_day
    completion_date = datetime.now(timezone.utc) + timedelta(days=days_needed)
    return {
        "remaining_tasks": remaining,
        "velocity_per_day": velocity_per_day,
        "days_needed": round(days_needed, 1),
        "projected_completion": completion_date.strftime("%Y-%m-%d"),
    }


def projection_report(tasks, days=7):
    avg_vel = average_velocity(tasks, days)
    std = velocity_std_dev(tasks, days)
    ci_low, ci_high = confidence_interval(avg_vel, std)
    projection = project_completion(tasks, avg_vel)
    return {
        "total_tasks": len(tasks),
        "completed": completed_count(tasks),
        "remaining": len(remaining_tasks(tasks)),
        "avg_velocity": avg_vel,
        "velocity_std_dev": std,
        "confidence_95": (ci_low, ci_high),
        "projection": projection,
        "trend": velocity_trend(tasks, days),
    }


def estimate_sprint_completion(tasks, sprint_days, velocity):
    remaining = len(remaining_tasks(tasks))
    completable = int(velocity * sprint_days)
    return {
        "remaining": remaining,
        "estimated_completable": min(completable, remaining),
        "carryover": max(0, remaining - completable),
        "completion_percentage": round(
            min(completable, remaining) / remaining * 100, 1
        ) if remaining > 0 else 100.0,
    }


def burn_rate(tasks, days=7):
    return average_velocity(tasks, days)


def days_until_empty(tasks, velocity):
    remaining = len(remaining_tasks(tasks))
    if velocity <= 0 or remaining == 0:
        return None
    return round(remaining / velocity)


def velocity_by_day_of_week(tasks):
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    counts = {i: [] for i in range(7)}
    for t in tasks:
        completed_at = getattr(t, "completed_at", None)
        if completed_at and _get_status(t) == "done":
            dt = _parse(completed_at)
            counts[dt.weekday()].append(1)
    result = {}
    for day_idx, name in enumerate(day_names):
        result[name] = len(counts[day_idx])
    return result
