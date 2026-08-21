"""Workload balancer for team task distribution."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class WorkloadEntry:
    """A team member's workload summary."""
    member: str
    task_ids: List[int] = field(default_factory=list)
    capacity: int = 10
    story_points: float = 0.0

    @property
    def load(self):
        return len(self.task_ids)

    @property
    def utilization(self):
        return round(self.load / max(self.capacity, 1) * 100, 1)

    @property
    def is_overloaded(self):
        return self.load > self.capacity

    @property
    def has_capacity(self):
        return self.load < self.capacity


class WorkloadBalancer:
    """Balances task distribution across team members."""
    def __init__(self):
        self._workloads: Dict[str, WorkloadEntry] = {}
        self._rebalance_log: List[dict] = []

    def add_member(self, member, capacity=10):
        """Add a team member."""
        self._workloads[member] = WorkloadEntry(member=member, capacity=capacity)

    def assign(self, member, task_id, story_points=0):
        """Assign a task to a member."""
        if member not in self._workloads:
            self.add_member(member)
        self._workloads[member].task_ids.append(task_id)
        self._workloads[member].story_points += story_points

    def unassign(self, member, task_id):
        """Remove a task from a member."""
        if member in self._workloads:
            w = self._workloads[member]
            if task_id in w.task_ids:
                w.task_ids.remove(task_id)
                return True
        return False

    def get(self, member):
        return self._workloads.get(member)

    def all_workloads(self):
        return list(self._workloads.values())

    def member_count(self):
        return len(self._workloads)

    def total_tasks(self):
        return sum(w.load for w in self._workloads.values())

    def avg_load(self):
        n = len(self._workloads)
        if n == 0: return 0.0
        return round(self.total_tasks() / n, 1)

    def max_load_member(self):
        """Return the member with the highest load."""
        if not self._workloads: return None
        return max(self._workloads.values(), key=lambda w: w.load)

    def min_load_member(self):
        """Return the member with the lowest load."""
        if not self._workloads: return None
        return min(self._workloads.values(), key=lambda w: w.load)

    def overloaded(self):
        return [w for w in self._workloads.values() if w.is_overloaded]

    def available(self):
        return [w for w in self._workloads.values() if w.has_capacity]

    def balance(self, tasks, story_points_map=None):
        """Distribute tasks evenly across available members."""
        sp_map = story_points_map or {}
        available = self.available()
        if not available:
            return {}

        assignments = {}
        sorted_members = sorted(available, key=lambda w: w.load)

        for i, task_id in enumerate(tasks):
            member = sorted_members[i % len(sorted_members)]
            self.assign(member.member, task_id, sp_map.get(task_id, 0))
            assignments[task_id] = member.member
            sorted_members = sorted(self.available() or sorted_members, key=lambda w: w.load)

        self._rebalance_log.append({"timestamp": datetime.now(timezone.utc).isoformat(),
                                     "tasks_assigned": len(assignments)})
        return assignments

    def rebalance(self):
        """Move tasks from overloaded to available members."""
        moves = []
        for overloaded in self.overloaded():
            available = self.available()
            for task_id in list(overloaded.task_ids):
                if not available:
                    break
                target = min(available, key=lambda w: w.load)
                self.unassign(overloaded.member, task_id)
                self.assign(target.member, task_id)
                moves.append({"task_id": task_id, "from": overloaded.member,
                              "to": target.member})
                available = self.available()
                if not overloaded.is_overloaded:
                    break
        self._rebalance_log.append({"timestamp": datetime.now(timezone.utc).isoformat(),
                                     "tasks_moved": len(moves), "moves": moves})
        return moves

    def rebalance_log(self):
        return list(self._rebalance_log)


def rebalance_report(balancer):
    """Generate a rebalancing report."""
    return {
        "members": balancer.member_count(),
        "total_tasks": balancer.total_tasks(),
        "avg_load": balancer.avg_load(),
        "overloaded": len(balancer.overloaded()),
        "available": len(balancer.available()),
        "rebalance_count": len(balancer.rebalance_log()),
        "workloads": {w.member: {"load": w.load, "capacity": w.capacity,
                                 "utilization": w.utilization}
                     for w in balancer.all_workloads()},
    }
