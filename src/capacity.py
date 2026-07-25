"""Team capacity planning and allocation."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TeamMember:
    """A team member with capacity and skills."""
    name: str
    weekly_capacity: float = 40.0
    skills: List[str] = field(default_factory=list)
    allocated_hours: float = 0.0

    @property
    def remaining_capacity(self) -> float:
        return max(0.0, self.weekly_capacity - self.allocated_hours)

    @property
    def utilization_percentage(self) -> float:
        if self.weekly_capacity <= 0:
            return 0.0
        return round((self.allocated_hours / self.weekly_capacity) * 100, 1)

    @property
    def is_overallocated(self) -> bool:
        return self.allocated_hours > self.weekly_capacity


def allocate_task(member: TeamMember, task, hours: float) -> bool:
    if member.allocated_hours + hours > member.weekly_capacity:
        return False
    member.allocated_hours += hours
    if not hasattr(member, "assigned_tasks") or member.assigned_tasks is None:
        member.assigned_tasks = []
    member.assigned_tasks.append({"task_id": getattr(task, "id", None), "hours": hours})
    return True


def deallocate_task(member: TeamMember, task_id: int) -> bool:
    if not hasattr(member, "assigned_tasks") or not member.assigned_tasks:
        return False
    before = len(member.assigned_tasks)
    removed = [t for t in member.assigned_tasks if t["task_id"] == task_id]
    member.assigned_tasks = [t for t in member.assigned_tasks if t["task_id"] != task_id]
    for r in removed:
        member.allocated_hours -= r["hours"]
    return len(member.assigned_tasks) < before


def team_capacity(team: List[TeamMember]) -> dict:
    total_capacity = sum(m.weekly_capacity for m in team)
    total_allocated = sum(m.allocated_hours for m in team)
    return {
        "total_capacity": round(total_capacity, 1),
        "total_allocated": round(total_allocated, 1),
        "total_remaining": round(total_capacity - total_allocated, 1),
        "utilization_percentage": round((total_allocated / total_capacity * 100), 1)
            if total_capacity > 0 else 0.0,
        "overallocated_members": sum(1 for m in team if m.is_overallocated),
    }


def available_capacity(team: List[TeamMember], min_hours: float = 0) -> List[TeamMember]:
    return [m for m in team if m.remaining_capacity >= min_hours]


def find_by_skill(team: List[TeamMember], skill: str) -> List[TeamMember]:
    return [m for m in team if skill in m.skills]


def most_available(team: List[TeamMember]) -> Optional[TeamMember]:
    if not team:
        return None
    return max(team, key=lambda m: m.remaining_capacity)


def least_busy(team: List[TeamMember]) -> Optional[TeamMember]:
    if not team:
        return None
    return min(team, key=lambda m: m.utilization_percentage)


def rebalance_suggestion(team: List[TeamMember]) -> List[dict]:
    overallocated = [m for m in team if m.is_overallocated]
    underallocated = [m for m in team if m.remaining_capacity > 0]
    suggestions = []
    for over in overallocated:
        surplus = over.allocated_hours - over.weekly_capacity
        for under in underallocated:
            if under.name == over.name:
                continue
            transfer = min(surplus, under.remaining_capacity)
            if transfer > 0:
                suggestions.append({
                    "from": over.name,
                    "to": under.name,
                    "hours": round(transfer, 1),
                })
                surplus -= transfer
                under.allocated_hours += transfer
                if surplus <= 0:
                    break
    return suggestions
