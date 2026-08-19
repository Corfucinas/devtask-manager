"""AI-powered task hints and suggestions."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


@dataclass
class TaskHint:
    """A single AI hint for a task."""
    hint_type: str  # next_action, breakdown, priority, estimate, blocker
    text: str
    confidence: float = 0.5  # 0-1
    metadata: Dict = field(default_factory=dict)


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def suggest_next_action(task, context=None) -> TaskHint:
    """Suggest the next action for a task based on its state."""
    status = _get_status(task)
    priority = _get_priority(task)

    if status == "todo":
        if priority in ("high", "critical"):
            return TaskHint("next_action", "Start this high-priority task immediately", 0.9)
        return TaskHint("next_action", "Consider starting this task in your next session", 0.6)
    elif status == "in_progress":
        due = getattr(task, "due_date", None)
        if due:
            try:
                days = (datetime.fromisoformat(due.replace("Z", "+00:00")) - datetime.now(timezone.utc)).days
                if days <= 1:
                    return TaskHint("next_action", "This task is due soon - focus on completing it", 0.85)
            except (ValueError, TypeError):
                pass
        return TaskHint("next_action", "Continue working on this task", 0.7)
    elif status == "review":
        return TaskHint("next_action", "Address review feedback and update the task", 0.8)
    elif status == "done":
        return TaskHint("next_action", "This task is complete - consider archiving it", 0.5)
    elif status == "blocked":
        return TaskHint("next_action", "Resolve blocking issue before continuing", 0.9)
    return TaskHint("next_action", "Review and update this task", 0.5)


def suggest_breakdown(task, max_subtasks=5) -> List[TaskHint]:
    """Suggest breaking down a large task into smaller pieces."""
    hints = []
    effort = getattr(task, "story_points", None) or getattr(task, "effort_score", None)
    desc = getattr(task, "description", "") or ""
    title = getattr(task, "title", "") or ""

    if effort and effort > 8:
        hints.append(TaskHint("breakdown",
            f"This task has {effort} story points - consider breaking it into {min(int(effort/3), max_subtasks)} subtasks",
            0.8))
    elif not desc and len(title) < 20:
        hints.append(TaskHint("breakdown",
            "Add more details to help break this task into actionable steps",
            0.6))

    if not desc:
        hints.append(TaskHint("breakdown",
            "Add a description with acceptance criteria to clarify scope",
            0.7))

    if not getattr(task, "tags", None):
        hints.append(TaskHint("breakdown",
            "Add tags to categorize and help break down this task",
            0.4))

    return hints[:max_subtasks]


def suggest_priority(task, context=None) -> TaskHint:
    """Suggest a priority level for a task."""
    current = _get_priority(task)
    due = getattr(task, "due_date", None)
    dependents = getattr(task, "dependents", None) or []
    tags = set(getattr(task, "tags", []) or [])

    score = 0
    if due:
        try:
            days = (datetime.fromisoformat(due.replace("Z", "+00:00")) - datetime.now(timezone.utc)).days
            if days < 0: score += 40
            elif days <= 1: score += 30
            elif days <= 3: score += 20
            elif days <= 7: score += 10
        except (ValueError, TypeError):
            pass

    if len(dependents) >= 3:
        score += 20
    if "bug" in tags:
        score += 10
    if "urgent" in tags:
        score += 15
    if "critical" in tags:
        score += 20

    if score >= 50:
        suggested = "critical"
    elif score >= 30:
        suggested = "high"
    elif score >= 15:
        suggested = "medium"
    else:
        suggested = "low"

    confidence = 0.5 + min(score / 100, 0.4)
    return TaskHint("priority",
        f"Suggested priority: {suggested} (current: {current})",
        round(confidence, 2),
        {"suggested": suggested, "current": current, "score": score})


def suggest_estimate(task) -> TaskHint:
    """Suggest a story point estimate based on task attributes."""
    desc = getattr(task, "description", "") or ""
    tags = set(getattr(task, "tags", []) or [])
    priority = _get_priority(task)

    base = 3
    if len(desc) > 200:
        base += 3
    elif len(desc) > 100:
        base += 1

    if "research" in tags:
        base += 5
    if "refactor" in tags:
        base += 2
    if "bug" in tags:
        base -= 1

    if priority == "critical":
        base = max(base, 5)

    estimate = min(max(base, 1), 21)

    return TaskHint("estimate",
        f"Estimated effort: {estimate} story points",
        0.6,
        {"estimate": estimate, "factors": {"description_length": len(desc), "tags": list(tags)}})


def detect_blockers(task) -> List[TaskHint]:
    """Detect potential blockers for a task."""
    hints = []
    status = _get_status(task)

    if status == "in_progress":
        days_stuck = getattr(task, "days_in_progress", 0)
        if days_stuck > 5:
            hints.append(TaskHint("blocker",
                f"Task has been in progress for {days_stuck} days - may be blocked",
                0.7))

    dependencies = getattr(task, "dependencies", None) or []
    if len(dependencies) > 3:
        hints.append(TaskHint("blocker",
            f"Task has {len(dependencies)} dependencies - high risk of blocking",
            0.6))

    if not getattr(task, "assignee", None) and status != "done":
        hints.append(TaskHint("blocker",
            "No assignee - this task may stall without ownership",
            0.5))

    return hints


def full_hints(task, context=None) -> Dict[str, List]:
    """Generate all hints for a task."""
    return {
        "next_action": [suggest_next_action(task, context)],
        "breakdown": suggest_breakdown(task),
        "priority": [suggest_priority(task, context)],
        "estimate": [suggest_estimate(task)],
        "blockers": detect_blockers(task),
    }
