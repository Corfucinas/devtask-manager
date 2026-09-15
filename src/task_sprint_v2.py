"""Sprint management with capacity and velocity."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class SprintV2:
    """A sprint with capacity and point tracking."""
    id: int
    name: str
    capacity: float = 0.0
    committed_points: float = 0.0
    completed_points: float = 0.0
    added_points: float = 0.0
    removed_points: float = 0.0
    task_ids: List[int] = field(default_factory=list)

    @property
    def velocity(self) -> float:
        return self.completed_points

    @property
    def scope_creep(self) -> float:
        return self.added_points - self.removed_points

    @property
    def load_ratio(self) -> float:
        if self.capacity <= 0:
            return 0.0
        return round(self.committed_points / self.capacity, 2)

    @property
    def is_over_capacity(self) -> bool:
        return self.committed_points > self.capacity


class SprintManager:
    """Manages multiple sprints with capacity and velocity."""
    def __init__(self):
        self._sprints: Dict[int, SprintV2] = {}
        self._next_id = 1

    def create(self, name: str, capacity: float = 0.0) -> SprintV2:
        sprint = SprintV2(id=self._next_id, name=name, capacity=capacity)
        self._sprints[self._next_id] = sprint
        self._next_id += 1
        return sprint

    def get(self, sprint_id: int) -> Optional[SprintV2]:
        return self._sprints.get(sprint_id)

    def all_sprints(self) -> List[SprintV2]:
        return list(self._sprints.values())

    def count(self) -> int:
        return len(self._sprints)

    def commit(self, sprint_id: int, points: float) -> bool:
        s = self._sprints.get(sprint_id)
        if not s:
            return False
        s.committed_points += points
        return True

    def complete(self, sprint_id: int, points: float) -> bool:
        s = self._sprints.get(sprint_id)
        if not s:
            return False
        s.completed_points += points
        return True

    def add_scope(self, sprint_id: int, points: float) -> bool:
        s = self._sprints.get(sprint_id)
        if not s:
            return False
        s.added_points += points
        s.committed_points += points
        return True

    def remove_scope(self, sprint_id: int, points: float) -> bool:
        s = self._sprints.get(sprint_id)
        if not s:
            return False
        s.removed_points += points
        s.committed_points = max(0, s.committed_points - points)
        return True

    def average_velocity(self) -> float:
        if not self._sprints:
            return 0.0
        return round(sum(s.velocity for s in self._sprints.values()) / len(self._sprints), 2)

    def over_capacity_sprints(self) -> List[SprintV2]:
        return [s for s in self._sprints.values() if s.is_over_capacity]


def sprint_report(mgr: SprintManager) -> Dict:
    return {
        "total_sprints": mgr.count(),
        "avg_velocity": mgr.average_velocity(),
        "over_capacity": len(mgr.over_capacity_sprints()),
        "sprints": [{"id": s.id, "name": s.name, "velocity": s.velocity,
                     "capacity": s.capacity, "load_ratio": s.load_ratio,
                     "scope_creep": s.scope_creep}
                    for s in mgr.all_sprints()],
    }
