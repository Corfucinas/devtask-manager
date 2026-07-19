"""Report generation for task summaries."""
from .models import Task, Status, Priority
from .stats import task_summary, productivity_score
from .tags import count_tags, tag_stats
from .search import group_by_status

def generate_daily_report(tasks):
    summary = task_summary(tasks)
    groups = group_by_status(tasks)
    return {"type": "daily", "total_tasks": summary["total"], "completed": summary["done"], "in_progress": summary["in_progress"], "todo": summary["todo"], "completion_rate": summary["completion_rate"], "productivity_score": productivity_score(tasks), "high_priority_pending": len([t for t in groups.get("todo", []) if t.priority in (Priority.HIGH, Priority.CRITICAL)])}

def generate_weekly_report(tasks):
    summary = task_summary(tasks)
    t_stats = tag_stats(tasks)
    return {"type": "weekly", "total_tasks": summary["total"], "completed": summary["done"], "completion_rate": summary["completion_rate"], "productivity_score": productivity_score(tasks), "tag_stats": t_stats, "priority_breakdown": summary["by_priority"]}

def format_report_text(report):
    lines = [f"=== {report['type'].upper()} REPORT ===", f"Total tasks: {report['total_tasks']}", f"Completed: {report['completed']}", f"Completion rate: {report['completion_rate']}%", f"Productivity score: {report['productivity_score']}"]
    if report.get("high_priority_pending") is not None:
        lines.append(f"High priority pending: {report['high_priority_pending']}")
    if report.get("priority_breakdown"):
        lines.append("Priority breakdown:")
        for p, c in report["priority_breakdown"].items():
            lines.append(f"  {p}: {c}")
    return "\n".join(lines)

def format_report_markdown(report):
    lines = [f"## {report['type'].title()} Report", "", "| Metric | Value |", "|--------|-------|"]
    lines.append(f"| Total tasks | {report['total_tasks']} |")
    lines.append(f"| Completed | {report['completed']} |")
    lines.append(f"| Completion rate | {report['completion_rate']}% |")
    lines.append(f"| Productivity score | {report['productivity_score']} |")
    if report.get("high_priority_pending") is not None:
        lines.append(f"| High priority pending | {report['high_priority_pending']} |")
    return "\n".join(lines)
