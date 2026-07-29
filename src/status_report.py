"""Weekly status report generator."""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


def _parse(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def _get_status(task) -> str:
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task) -> str:
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def progress_summary(tasks) -> dict:
    """Summarize task progress: completed, created, in-progress."""
    completed = sum(1 for t in tasks if _get_status(t) == "done")
    in_progress = sum(1 for t in tasks if _get_status(t) == "in-progress")
    todo = sum(1 for t in tasks if _get_status(t) == "todo")
    total = len(tasks)
    return {
        "total": total, "completed": completed, "in_progress": in_progress,
        "todo": todo,
        "completion_rate": round((completed / total * 100), 1) if total > 0 else 0.0,
    }


def tasks_in_range(tasks, start: str, end: str) -> list:
    start_dt = _parse(start)
    end_dt = _parse(end)
    return [t for t in tasks if hasattr(t, "created_at") and t.created_at
            and start_dt <= _parse(t.created_at) <= end_dt]


def completed_in_range(tasks, start: str, end: str) -> list:
    start_dt = _parse(start)
    end_dt = _parse(end)
    results = []
    for t in tasks:
        completed_at = getattr(t, "completed_at", None)
        if completed_at and _get_status(t) == "done":
            if start_dt <= _parse(completed_at) <= end_dt:
                results.append(t)
    return results


def top_performers(tasks, n: int = 5) -> List[dict]:
    """Return the most active contributors by completed task count."""
    counts = {}
    for t in tasks:
        if _get_status(t) == "done":
            assignee = getattr(t, "assignee", None)
            if assignee:
                counts[assignee] = counts.get(assignee, 0) + 1
    sorted_performers = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [{"assignee": name, "completed": count} for name, count in sorted_performers[:n]]


def priority_breakdown(tasks) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for t in tasks:
        p = _get_priority(t)
        if p in counts:
            counts[p] += 1
    return counts


def weekly_report(tasks, week_start: str = None) -> dict:
    """Generate a comprehensive weekly status report."""
    if week_start is None:
        today = datetime.now(timezone.utc)
        week_start = (today - timedelta(days=today.weekday())).date().isoformat()

    week_start_dt = _parse(week_start) if "T" in week_start else datetime.fromisoformat(week_start).replace(tzinfo=timezone.utc)
    week_end_dt = week_start_dt + timedelta(days=7)
    week_end = week_end_dt.isoformat()

    week_tasks = tasks_in_range(tasks, week_start, week_end)
    completed_tasks = completed_in_range(tasks, week_start, week_end)

    return {
        "week_start": week_start, "week_end": week_end,
        "summary": progress_summary(tasks),
        "week_summary": progress_summary(week_tasks),
        "completed_this_week": len(completed_tasks),
        "top_performers": top_performers(completed_tasks),
        "priority_breakdown": priority_breakdown(tasks),
        "new_tasks": len(week_tasks),
    }


def format_report(report: dict) -> str:
    """Format a weekly report as markdown."""
    lines = [
        "# Weekly Status Report",
        f"**Week:** {report['week_start']} to {report['week_end']}",
        "",
        "## Overall Summary",
        f"- Total tasks: {report['summary']['total']}",
        f"- Completed: {report['summary']['completed']}",
        f"- In Progress: {report['summary']['in_progress']}",
        f"- Todo: {report['summary']['todo']}",
        f"- Completion Rate: {report['summary']['completion_rate']}%",
        "",
        "## This Week",
        f"- New tasks: {report['new_tasks']}",
        f"- Completed: {report['completed_this_week']}",
        "",
    ]
    if report["top_performers"]:
        lines.append("## Top Performers")
        for p in report["top_performers"]:
            lines.append(f"- {p['assignee']}: {p['completed']} tasks completed")
        lines.append("")
    lines.append("## Priority Breakdown")
    for level in ("critical", "high", "medium", "low"):
        count = report["priority_breakdown"].get(level, 0)
        lines.append(f"- {level}: {count}")
    return "\n".join(lines)


def daily_standup(tasks, user: str) -> dict:
    """Generate a daily standup report for a user."""
    user_tasks = [t for t in tasks if getattr(t, "assignee", None) == user]
    done = [t for t in user_tasks if _get_status(t) == "done"]
    in_progress = [t for t in user_tasks if _get_status(t) == "in-progress"]
    todo = [t for t in user_tasks if _get_status(t) == "todo"]
    return {
        "user": user,
        "completed": [getattr(t, "title", str(t.id)) for t in done],
        "in_progress": [getattr(t, "title", str(t.id)) for t in in_progress],
        "planned": [getattr(t, "title", str(t.id)) for t in todo],
        "blocked": [
            getattr(t, "title", str(t.id))
            for t in user_tasks
            if hasattr(t, "blockers") and t.blockers
            and any(b.status == "active" for b in t.blockers)
        ],
    }


def format_standup(standup: dict) -> str:
    """Format a daily standup as markdown."""
    lines = [f"## Standup: {standup['user']}", "", "**Completed:**"]
    for item in standup["completed"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("**In Progress:**")
    for item in standup["in_progress"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("**Planned:**")
    for item in standup["planned"]:
        lines.append(f"- {item}")
    if standup["blocked"]:
        lines.append("")
        lines.append("**Blocked:**")
        for item in standup["blocked"]:
            lines.append(f"- {item}")
    return "\n".join(lines)
