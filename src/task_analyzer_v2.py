"""Enhanced task analyzer with insights."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


@dataclass
class Insight:
    """A single actionable insight."""
    type: str  # bottleneck, risk, opportunity, warning, info
    message: str
    severity: str = "info"  # info, warning, error, critical
    data: Dict = field(default_factory=dict)


class TaskAnalyzerV2:
    """Comprehensive task analysis."""
    def __init__(self):
        self._insights: List[Insight] = []

    def analyze(self, tasks) -> Dict:
        """Run full analysis on tasks."""
        self._insights = []
        total = len(tasks)
        done = sum(1 for t in tasks if _get_status(t) == "done")
        open_count = total - done

        status_dist = {}
        for t in tasks:
            s = _get_status(t)
            status_dist[s] = status_dist.get(s, 0) + 1

        priority_dist = {}
        for t in tasks:
            p = _get_priority(t)
            priority_dist[p] = priority_dist.get(p, 0) + 1

        overdue = 0
        for t in tasks:
            due = getattr(t, "due_date", None)
            if due and _get_status(t) != "done":
                try:
                    if _parse(due) < datetime.now(timezone.utc):
                        overdue += 1
                except (ValueError, TypeError):
                    pass

        unassigned = sum(1 for t in tasks if not getattr(t, "assignee", None))
        blocked = sum(1 for t in tasks
                       if hasattr(t, "blockers") and t.blockers
                       and any(getattr(b, "status", "") == "active" for b in t.blockers))

        # Generate insights
        if open_count == 0:
            self._insights.append(Insight("info", "All tasks are completed!", "info"))
        else:
            completion_rate = round(done / total * 100, 1)
            if completion_rate > 80:
                self._insights.append(Insight("opportunity",
                    f"High completion rate ({completion_rate}%)", "info"))
            elif completion_rate < 20:
                self._insights.append(Insight("warning",
                    f"Low completion rate ({completion_rate}%)", "warning"))

        if overdue > 0:
            self._insights.append(Insight("risk",
                f"{overdue} overdue tasks need attention", "error",
                {"count": overdue}))

        if unassigned > total * 0.3:
            self._insights.append(Insight("bottleneck",
                f"{unassigned} tasks have no assignee", "warning"))

        if blocked > 0:
            self._insights.append(Insight("risk",
                f"{blocked} tasks are blocked", "error", {"count": blocked}))

        critical_open = sum(1 for t in tasks
                            if _get_priority(t) == "critical" and _get_status(t) != "done")
        if critical_open > 3:
            self._insights.append(Insight("risk",
                f"{critical_open} critical tasks still open", "critical",
                {"count": critical_open}))

        return {
            "total_tasks": total,
            "done": done,
            "open": open_count,
            "overdue": overdue,
            "unassigned": unassigned,
            "blocked": blocked,
            "status_distribution": status_dist,
            "priority_distribution": priority_dist,
            "insights": [{"type": i.type, "message": i.message,
                          "severity": i.severity} for i in self._insights],
            "insight_count": len(self._insights),
        }

    def insights(self) -> List[Insight]:
        return list(self._insights)

    def insight_count(self) -> int:
        return len(self._insights)

    def critical_insights(self) -> List[Insight]:
        return [i for i in self._insights if i.severity in ("error", "critical")]

    def health_trend(self, tasks, days: int = 7) -> List[Dict]:
        """Calculate daily completion trend."""
        now = datetime.now(timezone.utc)
        trend = []
        for i in range(days):
            day_start = now - timedelta(days=days - i - 1)
            day_end = day_start + timedelta(days=1)
            completed = 0
            for t in tasks:
                completed_at = getattr(t, "completed_at", None)
                if completed_at and _get_status(t) == "done":
                    try:
                        ct = _parse(completed_at)
                        if day_start <= ct < day_end:
                            completed += 1
                    except (ValueError, TypeError):
                        pass
            trend.append({"day": day_start.strftime("%Y-%m-%d"), "completed": completed})
        return trend


def insight_report(tasks) -> Dict:
    """Generate a detailed insight report."""
    analyzer = TaskAnalyzerV2()
    analysis = analyzer.analyze(tasks)
    trend = analyzer.health_trend(tasks, days=7)
    return {
        "analysis": analysis,
        "trend": trend,
        "critical_insights": [
            {"type": i.type, "message": i.message}
            for i in analyzer.critical_insights()
        ],
    }


def trend_summary(trend: List[Dict]) -> str:
    """Summarize trend direction."""
    if not trend:
        return "No data"
    recent = [d["completed"] for d in trend]
    first_half = recent[:len(recent)//2]
    second_half = recent[len(recent)//2:]
    avg_first = sum(first_half) / max(len(first_half), 1)
    avg_second = sum(second_half) / max(len(second_half), 1)
    if avg_second > avg_first * 1.1:
        return "improving"
    elif avg_second < avg_first * 0.9:
        return "declining"
    return "stable"
