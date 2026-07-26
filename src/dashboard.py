"""Dashboard data aggregation and widgets."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DashboardWidget:
    """A single dashboard widget with data."""
    id: str
    title: str
    widget_type: str
    data: Any = None
    position: int = 0


def status_distribution(tasks) -> dict:
    """Return task status counts for pie chart."""
    counts = {"todo": 0, "in-progress": 0, "done": 0}
    for t in tasks:
        status = t.status.value if hasattr(t.status, "value") else t.status
        if status in counts:
            counts[status] += 1
        else:
            counts[status] = counts.get(status, 0) + 1
    return {"labels": list(counts.keys()), "values": list(counts.values())}


def priority_distribution(tasks) -> dict:
    """Return task priority counts for bar chart."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for t in tasks:
        priority = t.priority.value if hasattr(t.priority, "value") else t.priority
        if priority in counts:
            counts[priority] += 1
    return {"labels": list(counts.keys()), "values": list(counts.values())}


def task_counter(tasks) -> dict:
    """Return summary counters."""
    total = len(tasks)
    done = sum(
        1 for t in tasks
        if (t.status.value if hasattr(t.status, "value") else t.status) == "done"
    )
    open_count = total - done
    return {
        "total": total,
        "done": done,
        "open": open_count,
        "completion_rate": round((done / total * 100), 1) if total > 0 else 0.0,
    }


def tag_distribution(tasks) -> dict:
    """Return tag frequency distribution."""
    counts = {}
    for t in tasks:
        tags = getattr(t, "tags", []) or []
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1
    sorted_tags = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return {"labels": [t[0] for t in sorted_tags], "values": [t[1] for t in sorted_tags]}


def assignee_workload(tasks) -> dict:
    """Return task count per assignee."""
    counts = {}
    for t in tasks:
        assignee = getattr(t, "assignee", None)
        if assignee:
            counts[assignee] = counts.get(assignee, 0) + 1
    sorted_assignees = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return {"labels": [a[0] for a in sorted_assignees], "values": [a[1] for a in sorted_assignees]}


def build_dashboard(tasks) -> List[DashboardWidget]:
    """Build a complete dashboard from task data."""
    widgets = [
        DashboardWidget(id="status_pie", title="Task Status", widget_type="pie",
                        data=status_distribution(tasks), position=0),
        DashboardWidget(id="priority_bar", title="Priority Distribution", widget_type="bar",
                        data=priority_distribution(tasks), position=1),
        DashboardWidget(id="task_counter", title="Task Summary", widget_type="counter",
                        data=task_counter(tasks), position=2),
        DashboardWidget(id="tag_cloud", title="Tag Distribution", widget_type="bar",
                        data=tag_distribution(tasks), position=3),
        DashboardWidget(id="assignee_load", title="Assignee Workload", widget_type="bar",
                        data=assignee_workload(tasks), position=4),
    ]
    return widgets


def dashboard_summary(tasks) -> dict:
    """Generate a compact dashboard summary."""
    counter = task_counter(tasks)
    status = status_distribution(tasks)
    priority = priority_distribution(tasks)
    return {
        "total_tasks": counter["total"],
        "completion_rate": counter["completion_rate"],
        "status_breakdown": dict(zip(status["labels"], status["values"])),
        "priority_breakdown": dict(zip(priority["labels"], priority["values"])),
        "unique_tags": len(tag_distribution(tasks)["labels"]),
        "assignees": len(assignee_workload(tasks)["labels"]),
    }


def render_widget(widget: DashboardWidget) -> str:
    """Render a widget as a simple text summary."""
    lines = [f"## {widget.title}"]
    if widget.widget_type == "counter":
        for key, value in widget.data.items():
            lines.append(f"  {key}: {value}")
    elif widget.widget_type in ("pie", "bar"):
        labels = widget.data.get("labels", [])
        values = widget.data.get("values", [])
        for label, value in zip(labels, values):
            bar = "#" * min(int(value), 30)
            lines.append(f"  {label:15s} {value:3d} {bar}")
    return "\n".join(lines)


def render_dashboard(widgets: List[DashboardWidget]) -> str:
    """Render the full dashboard as text."""
    sections = [render_widget(w) for w in widgets]
    return "\n\n".join(sections)
