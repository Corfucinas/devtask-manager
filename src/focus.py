"""Focus mode and intelligent task selection."""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def focus_score(task, context=None):
    """Calculate how suitable a task is for focused work (0-100)."""
    context = context or {}
    score = 0
    status = _get_status(task)
    if status == "done":
        return 0.0
    blockers = getattr(task, "blockers", None) or []
    if not blockers or not any(b.status == "active" for b in blockers):
        score += 30
    if status == "in-progress":
        score += 20
    effort = getattr(task, "story_points", None) or getattr(task, "effort_score", None)
    if effort is not None and effort <= 5:
        score += 20
    elif effort is not None and effort <= 8:
        score += 10
    desc = getattr(task, "description", "") or ""
    if len(desc.strip()) > 10:
        score += 15
    same_priority_count = context.get("priority_counts", {}).get(_get_priority(task), 1)
    if same_priority_count <= 3:
        score += 15
    return min(100.0, float(score))


def select_next_task(tasks, context=None):
    """Select the best task to focus on next."""
    context = context or {}
    priority_counts = {}
    for t in tasks:
        p = _get_priority(t)
        priority_counts[p] = priority_counts.get(p, 0) + 1
    context["priority_counts"] = priority_counts
    candidates = []
    for task in tasks:
        status = _get_status(task)
        if status == "done":
            continue
        score = focus_score(task, context)
        candidates.append({"task": task, "id": getattr(task, "id", None),
                           "title": getattr(task, "title", ""), "score": score,
                           "priority": _get_priority(task), "status": status})
    if not candidates:
        return None
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[0]


def focus_session(tasks, duration_min=25):
    """Plan a focus session: select tasks that fit within the time budget."""
    remaining_minutes = duration_min
    selected = []
    skipped = []
    for task in sorted(tasks, key=lambda t: -focus_score(t)):
        status = _get_status(task)
        if status == "done":
            continue
        effort = getattr(task, "story_points", None) or getattr(task, "effort_score", None)
        est_minutes = effort * 15 if effort is not None else 25
        if est_minutes <= remaining_minutes:
            selected.append({"id": getattr(task, "id", None),
                             "title": getattr(task, "title", ""),
                             "estimated_minutes": est_minutes})
            remaining_minutes -= est_minutes
        else:
            skipped.append({"id": getattr(task, "id", None),
                            "title": getattr(task, "title", ""),
                            "estimated_minutes": est_minutes})
    return {"duration_minutes": duration_min, "selected": selected, "skipped": skipped,
            "utilized_minutes": duration_min - remaining_minutes,
            "remaining_minutes": remaining_minutes, "task_count": len(selected)}


def distraction_report(tasks):
    """Identify tasks likely to cause context switching."""
    high_priority_count = sum(1 for t in tasks
        if _get_priority(t) in ("high", "critical") and _get_status(t) != "done")
    in_progress_count = sum(1 for t in tasks if _get_status(t) == "in-progress")
    blocked_count = sum(1 for t in tasks
        if hasattr(t, "blockers") and t.blockers
        and any(b.status == "active" for b in t.blockers))
    risk_level = "low"
    if high_priority_count > 5 or in_progress_count > 3:
        risk_level = "high"
    elif high_priority_count > 3 or in_progress_count > 2:
        risk_level = "medium"
    return {"high_priority_open": high_priority_count, "in_progress": in_progress_count,
            "blocked": blocked_count, "context_switch_risk": risk_level,
            "recommendation": _focus_recommendation(risk_level, in_progress_count)}


def _focus_recommendation(risk_level, in_progress_count):
    if risk_level == "high":
        return "High context-switch risk. Close all but one task. Focus on the highest-priority item."
    elif risk_level == "medium":
        return "Moderate risk. Limit work to 2 tasks max. Avoid starting new work."
    else:
        return "Low risk. Good conditions for focused work."


def deep_work_tasks(tasks, min_score=60):
    """Return tasks suitable for deep work (high focus score)."""
    results = []
    for task in tasks:
        score = focus_score(task)
        if score >= min_score and _get_status(task) != "done":
            results.append({"id": getattr(task, "id", None),
                            "title": getattr(task, "title", ""), "score": score})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def quick_wins(tasks, max_effort=3):
    """Return tasks that can be completed quickly for momentum."""
    results = []
    for task in tasks:
        if _get_status(task) == "done":
            continue
        effort = getattr(task, "story_points", None) or getattr(task, "effort_score", None)
        if effort is not None and effort <= max_effort:
            results.append({"id": getattr(task, "id", None),
                            "title": getattr(task, "title", ""), "effort": effort})
    results.sort(key=lambda x: x["effort"])
    return results


def context_switch_cost(tasks):
    """Estimate the cost of context switching between tasks."""
    in_progress = [t for t in tasks if _get_status(t) == "in-progress"]
    cost_per_switch = 15
    total_cost = len(in_progress) * cost_per_switch
    return {"in_progress_count": len(in_progress), "cost_per_switch_min": cost_per_switch,
            "total_switch_cost_min": total_cost,
            "recommendation": "Reduce in-progress tasks to minimize context switching."
                if len(in_progress) > 2 else "Good focus state."}
