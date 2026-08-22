"""Activity heatmap data generator."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


@dataclass
class HeatmapCell:
    """A single cell in the activity heatmap."""
    date: str
    count: int = 0
    intensity: int = 0  # 0-4
    day_of_week: int = 0  # 0=Monday
    week: int = 0
    is_weekend: bool = False


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def heatmap_intensity(count, max_count):
    """Calculate intensity level (0-4) based on count."""
    if max_count <= 0:
        return 0
    ratio = count / max_count
    if ratio <= 0:
        return 0
    elif ratio < 0.25:
        return 1
    elif ratio < 0.5:
        return 2
    elif ratio < 0.75:
        return 3
    else:
        return 4


def generate_heatmap(tasks, days=90):
    """Generate a daily activity heatmap for the last N days."""
    now = datetime.now(timezone.utc)
    cells = []
    daily_counts = {}

    for task in tasks:
        created = getattr(task, "created_at", None)
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
            except (ValueError, TypeError):
                pass
        completed = getattr(task, "completed_at", None)
        if completed and _get_status(task) == "done":
            try:
                dt = datetime.fromisoformat(completed.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
            except (ValueError, TypeError):
                pass

    max_count = max(daily_counts.values()) if daily_counts else 0
    week_num = 0
    for i in range(days):
        day = now - timedelta(days=days - i - 1)
        date_str = day.strftime("%Y-%m-%d")
        count = daily_counts.get(date_str, 0)
        cell = HeatmapCell(
            date=date_str,
            count=count,
            intensity=heatmap_intensity(count, max_count),
            day_of_week=day.weekday(),
            week=week_num,
            is_weekend=day.weekday() >= 5,
        )
        cells.append(cell)
        if day.weekday() == 6:  # Sunday
            week_num += 1
    return cells


def heatmap_report(tasks, days=90):
    """Generate a full heatmap report."""
    cells = generate_heatmap(tasks, days)
    active_days = sum(1 for c in cells if c.count > 0)
    total_activity = sum(c.count for c in cells)
    max_intensity = max(c.intensity for c in cells) if cells else 0
    by_intensity = {i: sum(1 for c in cells if c.intensity == i) for i in range(5)}
    by_dow = {i: sum(c.count for c in cells if c.day_of_week == i) for i in range(7)}

    return {
        "total_days": len(cells),
        "active_days": active_days,
        "total_activity": total_activity,
        "max_intensity": max_intensity,
        "by_intensity": by_intensity,
        "by_day_of_week": by_dow,
        "most_active_day": max(cells, key=lambda c: c.count).date if cells else None,
        "streak": _calculate_streak(cells),
    }


def _calculate_streak(cells):
    """Calculate the current activity streak."""
    streak = 0
    for cell in reversed(cells):
        if cell.count > 0:
            streak += 1
        else:
            break
    return streak


def heatmap_quarters(cells):
    """Split heatmap into quarters (weeks of 7)."""
    quarters = []
    for i in range(0, len(cells), 7):
        quarter = cells[i:i+7]
        if quarter:
            total = sum(c.count for c in quarter)
            quarters.append({
                "week": i // 7,
                "total": total,
                "avg_intensity": round(sum(c.intensity for c in quarter) / max(len(quarter), 1), 1),
            })
    return quarters


def heatmap_summary(cells):
    """Generate a compact heatmap summary."""
    return {
        "total_cells": len(cells),
        "active_cells": sum(1 for c in cells if c.count > 0),
        "max_count": max((c.count for c in cells), default=0),
        "avg_count": round(sum(c.count for c in cells) / max(len(cells), 1), 2),
        "intensity_distribution": {i: sum(1 for c in cells if c.intensity == i) for i in range(5)},
    }
