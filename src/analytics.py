"""Task analytics and insights engine."""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def throughput_analysis(tasks, period="daily", days=30):
    now = datetime.now(timezone.utc)
    results = []
    for i in range(days):
        if period == "daily":
            period_start = now - timedelta(days=days - i - 1)
            period_end = period_start + timedelta(days=1)
        elif period == "weekly":
            period_start = now - timedelta(weeks=days - i - 1)
            period_end = period_start + timedelta(weeks=1)
        else:
            period_start = now - timedelta(days=days - i - 1)
            period_end = period_start + timedelta(days=1)
        completed = 0
        created = 0
        for t in tasks:
            completed_at = getattr(t, "completed_at", None)
            created_at = getattr(t, "created_at", None)
            status = _get_status(t)
            if completed_at and status == "done":
                ct = _parse(completed_at)
                if period_start <= ct < period_end:
                    completed += 1
            if created_at:
                ct = _parse(created_at)
                if period_start <= ct < period_end:
                    created += 1
        results.append({"period": period_start.strftime("%Y-%m-%d"),
                        "created": created, "completed": completed})
    return results


def bottleneck_analysis(tasks):
    status_counts = {"todo": 0, "in-progress": 0, "review": 0, "done": 0, "blocked": 0}
    for t in tasks:
        status = _get_status(t)
        if status in status_counts:
            status_counts[status] += 1
    total = len(tasks)
    bottlenecks = []
    if status_counts["in-progress"] > total * 0.3:
        bottlenecks.append("Too many tasks in-progress - consider limiting WIP")
    if status_counts["review"] > total * 0.2:
        bottlenecks.append("Review queue is backing up - assign more reviewers")
    blocked_count = sum(1 for t in tasks
        if hasattr(t, "blockers") and t.blockers
        and any(b.status == "active" for b in t.blockers))
    if blocked_count > total * 0.15:
        bottlenecks.append(f"{blocked_count} tasks are blocked - resolve impediments")
    if status_counts["todo"] > total * 0.5:
        bottlenecks.append("Large backlog - prioritize and start tasks")
    return {"status_distribution": status_counts, "bottlenecks": bottlenecks,
            "bottleneck_count": len(bottlenecks)}


def trend_analysis(tasks, metric="completion", days=14):
    daily = throughput_analysis(tasks, period="daily", days=days)
    values = [d["completed"] if metric == "completion" else d["created"] for d in daily]
    if not values:
        return {"trend": "stable", "values": [], "change": 0.0}
    first_half = values[:len(values)//2]
    second_half = values[len(values)//2:]
    avg_first = sum(first_half) / max(len(first_half), 1)
    avg_second = sum(second_half) / max(len(second_half), 1)
    if avg_second > avg_first * 1.1:
        trend = "increasing"
    elif avg_second < avg_first * 0.9:
        trend = "decreasing"
    else:
        trend = "stable"
    change = ((avg_second - avg_first) / max(avg_first, 1)) * 100
    return {"trend": trend, "values": values, "change_percent": round(change, 1),
            "avg_first_half": round(avg_first, 2), "avg_second_half": round(avg_second, 2)}


def cycle_time_distribution(tasks):
    cycle_times = []
    for t in tasks:
        if _get_status(t) != "done":
            continue
        started = getattr(t, "started_at", None)
        completed = getattr(t, "completed_at", None)
        if started and completed:
            try:
                start_dt = _parse(started)
                end_dt = _parse(completed)
                hours = (end_dt - start_dt).total_seconds() / 3600
                cycle_times.append(round(hours, 1))
            except (ValueError, TypeError):
                continue
    if not cycle_times:
        return {"count": 0, "average": 0, "median": 0, "min": 0, "max": 0, "p90": 0}
    sorted_times = sorted(cycle_times)
    n = len(sorted_times)
    return {"count": n, "average": round(sum(cycle_times) / n, 1),
            "median": sorted_times[n // 2], "min": sorted_times[0],
            "max": sorted_times[-1], "p90": sorted_times[int(n * 0.9)] if n > 1 else sorted_times[0]}


def assignee_workload_analysis(tasks):
    workload = {}
    for t in tasks:
        assignee = getattr(t, "assignee", None)
        if not assignee:
            continue
        if assignee not in workload:
            workload[assignee] = {"total": 0, "done": 0, "open": 0}
        workload[assignee]["total"] += 1
        if _get_status(t) == "done":
            workload[assignee]["done"] += 1
        else:
            workload[assignee]["open"] += 1
    overloaded = [name for name, w in workload.items() if w["open"] > 5]
    return {"assignees": workload, "assignee_count": len(workload),
            "overloaded": overloaded,
            "unassigned_count": sum(1 for t in tasks if not getattr(t, "assignee", None))}


def insights_report(tasks):
    total = len(tasks)
    completed = sum(1 for t in tasks if _get_status(t) == "done")
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0.0
    insights = []
    if completion_rate > 80:
        insights.append("Excellent completion rate - team is delivering effectively")
    elif completion_rate < 30:
        insights.append("Low completion rate - many tasks are stuck")
    bottleneck = bottleneck_analysis(tasks)
    for b in bottleneck["bottlenecks"]:
        insights.append(b)
    workload = assignee_workload_analysis(tasks)
    if workload["overloaded"]:
        insights.append(f"{len(workload['overloaded'])} assignees are overloaded")
    trend = trend_analysis(tasks, metric="completion", days=14)
    if trend["trend"] == "increasing":
        insights.append("Completion rate is trending up - momentum is building")
    elif trend["trend"] == "decreasing":
        insights.append("Completion rate is declining - investigate blockers")
    cycle = cycle_time_distribution(tasks)
    if cycle["count"] > 0 and cycle["average"] > 48:
        insights.append(f"Average cycle time is {cycle['average']}h - consider breaking down tasks")
    return {"total_tasks": total, "completion_rate": completion_rate,
            "insights": insights, "insight_count": len(insights),
            "bottleneck_analysis": bottleneck, "trend": trend["trend"],
            "cycle_time": cycle, "workload": workload}
