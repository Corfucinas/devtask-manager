"""Task dependency tracking system."""

from collections import defaultdict


class DependencyGraph:
    """Tracks task dependencies (blocked by / blocks relationships)."""

    def __init__(self):
        self._blocked_by = defaultdict(set)  # task_id -> set of blocker_ids
        self._blocks = defaultdict(set)      # task_id -> set of blocked_ids

    def add_dependency(self, task_id, depends_on_id):
        """Mark task_id as blocked by depends_on_id.
        Returns False if it would create a cycle."""
        if task_id == depends_on_id:
            return False
        if self._would_create_cycle(depends_on_id, task_id):
            return False
        self._blocked_by[task_id].add(depends_on_id)
        self._blocks[depends_on_id].add(task_id)
        return True

    def remove_dependency(self, task_id, depends_on_id):
        """Remove a dependency relationship."""
        self._blocked_by[task_id].discard(depends_on_id)
        self._blocks[depends_on_id].discard(task_id)

    def get_blockers(self, task_id):
        """Get IDs of tasks blocking this task."""
        return sorted(self._blocked_by.get(task_id, set()))

    def get_blocked(self, task_id):
        """Get IDs of tasks blocked by this task."""
        return sorted(self._blocks.get(task_id, set()))

    def is_blocked(self, task_id):
        """Check if a task has any unresolved blockers."""
        return len(self._blocked_by.get(task_id, set())) > 0

    def get_ready_tasks(self, task_ids, completed_ids):
        """From a set of task_ids, return those not blocked by any
        incomplete task."""
        completed = set(completed_ids)
        ready = []
        for tid in task_ids:
            blockers = self._blocked_by.get(tid, set())
            if all(b in completed for b in blockers):
                ready.append(tid)
        return ready

    def get_execution_order(self, task_ids):
        """Return tasks in dependency-respecting order (topological sort)."""
        in_degree = {tid: len(self._blocked_by.get(tid, set())) for tid in task_ids}
        graph = {tid: list(self._blocks.get(tid, set())) for tid in task_ids}

        queue = [tid for tid in task_ids if in_degree[tid] == 0]
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)
            for neighbor in graph.get(current, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return order if len(order) == len(task_ids) else None

    def _would_create_cycle(self, from_id, to_id):
        """Check if adding from_id -> to_id would create a cycle."""
        visited = set()
        stack = [to_id]
        while stack:
            current = stack.pop()
            if current == from_id:
                return True
            if current not in visited:
                visited.add(current)
                stack.extend(self._blocks.get(current, set()))
        return False

    def to_dict(self):
        """Serialize to dict."""
        return {
            "blocked_by": {str(k): sorted(v) for k, v in self._blocked_by.items()},
            "blocks": {str(k): sorted(v) for k, v in self._blocks.items()},
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize from dict."""
        graph = cls()
        for k, v in data.get("blocked_by", {}).items():
            graph._blocked_by[int(k)] = set(v)
        for k, v in data.get("blocks", {}).items():
            graph._blocks[int(k)] = set(v)
        return graph
