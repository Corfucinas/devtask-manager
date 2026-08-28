"""Task summarizer for generating text summaries."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


@dataclass
class SummaryConfig:
    """Configuration for task summaries."""
    detail_level: str = "medium"  # brief, medium, detailed
    include_completed: bool = True
    include_metadata: bool = False
    max_tasks_per_group: int = 10
    format: str = "text"  # text, markdown, json


def summarize_tasks(tasks, config=None):
    """Generate a text summary of tasks."""
    if config is None:
        config = SummaryConfig()
    total = len(tasks)
    done = sum(1 for t in tasks if _get_status(t) == "done")
    open_count = total - done
    lines = []
    if config.format == "markdown":
        lines.append(f"## Task Summary")
        lines.append(f"")
        lines.append(f"- **Total:** {total}")
        lines.append(f"- **Completed:** {done}")
        lines.append(f"- **Open:** {open_count}")
        lines.append(f"- **Completion Rate:** {round(done / max(total, 1) * 100, 1)}%")
        if config.detail_level != "brief":
            lines.append("")
            lines.append("### By Priority")
            for p in ("critical", "high", "medium", "low"):
                count = sum(1 for t in tasks if _get_priority(t) == p and _get_status(t) != "done")
                if count > 0:
                    lines.append(f"- {p}: {count} open")
            lines.append("")
            lines.append("### By Status")
            for s in ("todo", "in-progress", "review", "done"):
                count = sum(1 for t in tasks if _get_status(t) == s)
                if count > 0:
                    lines.append(f"- {s}: {count}")
    else:
        lines.append(f"Task Summary: {total} total, {done} done, {open_count} open")
        if config.detail_level != "brief":
            for p in ("critical", "high", "medium", "low"):
                count = sum(1 for t in tasks if _get_priority(t) == p and _get_status(t) != "done")
                if count > 0:
                    lines.append(f"  {p}: {count} open")
    return "\n".join(lines)


def summarize_by_group(tasks, group_key="status", config=None):
    """Generate a grouped summary."""
    if config is None:
        config = SummaryConfig()
    groups: Dict[str, List] = {}
    for task in tasks:
        if group_key == "status":
            key = _get_status(task)
        elif group_key == "priority":
            key = _get_priority(task)
        elif group_key == "assignee":
            key = getattr(task, "assignee", None) or "unassigned"
        else:
            key = str(getattr(task, group_key, "unknown"))
        if key not in groups:
            groups[key] = []
        groups[key].append(task)
    lines = []
    for key in sorted(groups.keys()):
        group_tasks = groups[key]
        lines.append(f"### {key} ({len(group_tasks)} tasks)")
        if config.detail_level == "detailed":
            for t in group_tasks[:config.max_tasks_per_group]:
                lines.append(f"  - #{getattr(t, 'id', '?')}: {getattr(t, 'title', '')}")
            if len(group_tasks) > config.max_tasks_per_group:
                lines.append(f"  ... and {len(group_tasks) - config.max_tasks_per_group} more")
    return "\n".join(lines)


def summary_report(tasks):
    """Generate structured summary data."""
    total = len(tasks)
    done = sum(1 for t in tasks if _get_status(t) == "done")
    return {
        "total": total,
        "done": done,
        "open": total - done,
        "completion_rate": round(done / max(total, 1) * 100, 1),
        "by_status": {s: sum(1 for t in tasks if _get_status(t) == s)
                      for s in ("todo", "in-progress", "review", "done")},
        "by_priority": {p: sum(1 for t in tasks if _get_priority(t) == p)
                        for p in ("critical", "high", "medium", "low")},
        "assigned": sum(1 for t in tasks if getattr(t, "assignee", None)),
        "unassigned": sum(1 for t in tasks if not getattr(t, "assignee", None)),
        "has_due_date": sum(1 for t in tasks if getattr(t, "due_date", None)),
        "overdue": sum(1 for t in tasks
            if getattr(t, "due_date", None) and _get_status(t) != "done"
            and _is_overdue(t)),
    }


def _is_overdue(task):
    due = getattr(task, "due_date", None)
    if not due:
        return False
    try:
        return datetime.fromisoformat(due.replace("Z", "+00:00")) < datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return False


def brief_summary(tasks):
    """One-line summary."""
    total = len(tasks)
    done = sum(1 for t in tasks if _get_status(t) == "done")
    return f"{done}/{total} tasks completed ({round(done / max(total, 1) * 100, 0):.0f}%)"


def daily_summary_text(tasks, date=None):
    """Generate a daily summary as text."""
    report = summary_report(tasks)
    lines = [
        f"Daily Report - {date or datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"Completed: {report['done']}/{report['total']} ({report['completion_rate']}%)",
        f"Open: {report['open']}",
        f"Overdue: {report['overdue']}",
        f"Unassigned: {report['unassigned']}",
    ]
    return "\n".join(lines)
