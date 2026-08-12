"""Task completion analysis and predictions."""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def completion_rate(tasks, period_days=7):
    total = len(tasks)
    if total == 0:
        return 0.0
    done = sum(1 for t in tasks if _get_status(t) == "done")
    return round(done / total * 100, 1)


def daily_completion_rate(tasks, days=14):
    now = datetime.now(timezone.utc)
    results = []
    for i in range(days):
        day_start = now - timedelta(days=days - i - 1)
        day_end = day_start + timedelta(days=1)
        completed = 0
        for t in tasks:
            completed_at = getattr(t, "completed_at", None)
            if completed_at and _get_status(t) == "done":
                ct = _parse(completed_at)
                if day_start <= ct < day_end:
                    completed += 1
        results.append({"day": day_start.strftime("%Y-%m-%d"), "completed": completed})
    return results


def predict_completion(tasks, days=7):
    daily = daily_completion_rate(tasks, days=14)
    recent_rates = [d["completed"] for d in daily[-7:]]
    avg_rate = sum(recent_rates) / max(len(recent_rates), 1)
    remaining = sum(1 for t in tasks if _get_status(t) != "done")
    predicted = int(avg_rate * days)
    return {"remaining_tasks": remaining,
            "avg_daily_completion": round(avg_rate, 2),
            "prediction_days": days,
            "predicted_completions": min(predicted, remaining),
            "will_complete_all": predicted >= remaining,
            "days_to_clear_backlog": round(remaining / max(avg_rate, 0.1)) if remaining > 0 else 0}


class CompletionAnalyzer:
    """Analyzes task completion patterns."""
    def __init__(self):
        self._history = []

    def record(self, tasks, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        snapshot = {"timestamp": timestamp, "total": len(tasks),
                    "done": sum(1 for t in tasks if _get_status(t) == "done"),
                    "open": sum(1 for t in tasks if _get_status(t) != "done")}
        snapshot["rate"] = round(snapshot["done"] / max(snapshot["total"], 1) * 100, 1)
        self._history.append(snapshot)
        return snapshot

    def trend(self):
        if len(self._history) < 2:
            return "stable"
        n = min(len(self._history), 5)
        recent = self._history[-n:]
        first = sum(s["rate"] for s in recent[:n//2]) / max(n//2, 1)
        second = sum(s["rate"] for s in recent[n//2:]) / max(n - n//2, 1)
        if second > first * 1.05: return "improving"
        elif second < first * 0.95: return "declining"
        return "stable"

    def history(self):
        return list(self._history)

    def count(self):
        return len(self._history)

    def latest(self):
        return self._history[-1] if self._history else None

    def average_rate(self, last_n=0):
        history = self._history[-last_n:] if last_n > 0 else self._history
        if not history: return 0.0
        return round(sum(s["rate"] for s in history) / len(history), 1)


def completion_report(tasks):
    return {"total_tasks": len(tasks),
            "done": sum(1 for t in tasks if _get_status(t) == "done"),
            "open": sum(1 for t in tasks if _get_status(t) != "done"),
            "completion_rate": completion_rate(tasks),
            "daily_rates": daily_completion_rate(tasks, 14),
            "prediction": predict_completion(tasks, 7),
            "by_priority": {p: sum(1 for t in tasks
                if (t.priority.value if hasattr(t.priority, "value") else t.priority) == p
                and _get_status(t) != "done")
                for p in ("critical", "high", "medium", "low")}}


def completion_velocity(tasks, days=7):
    daily = daily_completion_rate(tasks, days)
    if not daily: return 0.0
    return round(sum(d["completed"] for d in daily) / len(daily), 2)


def estimated_completion_date(tasks, velocity=None):
    remaining = sum(1 for t in tasks if _get_status(t) != "done")
    if remaining == 0: return None
    if velocity is None: velocity = completion_velocity(tasks)
    if velocity <= 0: return None
    days = remaining / velocity
    return (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
