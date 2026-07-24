"""Milestone tracking and progress calculation."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Milestone:
    """A project milestone with associated tasks."""
    id: int
    name: str
    description: str = ""
    due_date: Optional[str] = None
    tasks: List[int] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


def add_to_milestone(task, milestone: Milestone) -> None:
    """Link a task to a milestone."""
    if task.id not in milestone.tasks:
        milestone.tasks.append(task.id)
    task.milestone_id = milestone.id


def remove_from_milestone(task, milestone: Milestone) -> bool:
    """Remove a task from a milestone."""
    if task.id in milestone.tasks:
        milestone.tasks.remove(task.id)
        if hasattr(task, "milestone_id"):
            task.milestone_id = None
        return True
    return False


def milestone_progress(milestone: Milestone, tasks) -> dict:
    """Calculate progress for a milestone."""
    milestone_task_ids = set(milestone.tasks)
    milestone_tasks = [t for t in tasks if t.id in milestone_task_ids]
    total = len(milestone_tasks)
    if total == 0:
        return {"total": 0, "done": 0, "percentage": 0.0}
    done = sum(
        1 for t in milestone_tasks
        if (t.status.value if hasattr(t.status, "value") else t.status) == "done"
    )
    return {
        "total": total,
        "done": done,
        "percentage": round((done / total) * 100, 1),
    }


def is_milestone_complete(milestone: Milestone, tasks) -> bool:
    """Check if all tasks in a milestone are done."""
    progress = milestone_progress(milestone, tasks)
    return progress["total"] > 0 and progress["done"] == progress["total"]


def milestone_summary(milestones: List[Milestone], tasks) -> List[dict]:
    """Generate summary for all milestones."""
    results = []
    for m in milestones:
        progress = milestone_progress(m, tasks)
        results.append({
            "id": m.id,
            "name": m.name,
            "due_date": m.due_date,
            "total": progress["total"],
            "done": progress["done"],
            "percentage": progress["percentage"],
            "complete": progress["total"] > 0 and progress["done"] == progress["total"],
        })
    return results


def overdue_milestones(milestones: List[Milestone]) -> List[Milestone]:
    """Return milestones past their due date that aren't complete."""
    now = datetime.now(timezone.utc)
    overdue = []
    for m in milestones:
        if m.due_date:
            due = datetime.fromisoformat(m.due_date.replace("Z", "+00:00"))
            if due < now:
                overdue.append(m)
    return overdue


def upcoming_milestones(milestones: List[Milestone], days: int = 7) -> List[Milestone]:
    """Return milestones due within N days."""
    now = datetime.now(timezone.utc)
    results = []
    for m in milestones:
        if m.due_date:
            due = datetime.fromisoformat(m.due_date.replace("Z", "+00:00"))
            delta = (due - now).days
            if 0 <= delta <= days:
                results.append(m)
    return results


def tasks_without_milestone(tasks) -> list:
    """Return tasks not linked to any milestone."""
    return [t for t in tasks if not getattr(t, "milestone_id", None)]
