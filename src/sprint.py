"""Sprint planning and iteration management."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional


@dataclass
class Sprint:
    """A sprint/iteration with capacity and date range."""
    id: int
    name: str
    start_date: str
    end_date: str
    capacity: int = 0
    tasks: List[int] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            name=data["name"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            capacity=data.get("capacity", 0),
            tasks=data.get("tasks", []),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "capacity": self.capacity,
            "tasks": list(self.tasks),
        }

    def duration_days(self) -> int:
        """Return sprint duration in days."""
        start = datetime.fromisoformat(self.start_date)
        end = datetime.fromisoformat(self.end_date)
        return (end - start).days


def add_to_sprint(task, sprint: Sprint) -> None:
    """Assign a task to a sprint."""
    if task.id not in sprint.tasks:
        sprint.tasks.append(task.id)
    if not hasattr(task, "sprint_id") or task.sprint_id is None:
        task.sprint_id = sprint.id


def sprint_capacity(sprint: Sprint, tasks) -> dict:
    """Calculate used vs available capacity."""
    sprint_task_ids = set(sprint.tasks)
    sprint_tasks = [t for t in tasks if t.id in sprint_task_ids]
    used = sum(getattr(t, "story_points", 0) or 0 for t in sprint_tasks)
    return {
        "total": sprint.capacity,
        "used": used,
        "remaining": max(0, sprint.capacity - used),
        "over_capacity": used > sprint.capacity,
    }


def sprint_velocity(sprint: Sprint, tasks) -> int:
    """Sum completed story points in a sprint."""
    sprint_task_ids = set(sprint.tasks)
    total = 0
    for t in tasks:
        if t.id in sprint_task_ids:
            status = t.status.value if hasattr(t.status, "value") else t.status
            if status == "done":
                total += getattr(t, "story_points", 0) or 0
    return total


def active_sprint(sprints: List[Sprint]) -> Optional[Sprint]:
    """Find the currently active sprint based on today's date."""
    today = datetime.now(timezone.utc).date()
    for sprint in sprints:
        start = datetime.fromisoformat(sprint.start_date).date()
        end = datetime.fromisoformat(sprint.end_date).date()
        if start <= today <= end:
            return sprint
    return None


def sprint_completion_rate(sprint: Sprint, tasks) -> float:
    """Return percentage of sprint tasks that are done."""
    sprint_task_ids = set(sprint.tasks)
    sprint_tasks = [t for t in tasks if t.id in sprint_task_ids]
    if not sprint_tasks:
        return 0.0
    done = sum(
        1 for t in sprint_tasks
        if (t.status.value if hasattr(t.status, "value") else t.status) == "done"
    )
    return (done / len(sprint_tasks)) * 100
