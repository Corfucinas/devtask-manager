"""Batch scheduling for deferred task operations."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ScheduledOp:
    """A scheduled batch operation."""
    id: int
    operation: str  # update, delete, assign, notify, etc.
    task_ids: List[int] = field(default_factory=list)
    scheduled_time: str = ""
    callback: Optional[Callable] = None
    args: Dict[str, Any] = field(default_factory=dict)
    executed: bool = False
    result: Optional[Any] = None
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_due(self) -> bool:
        """Check if this operation is due to execute."""
        if self.executed:
            return False
        if not self.scheduled_time:
            return True
        try:
            scheduled = datetime.fromisoformat(self.scheduled_time.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) >= scheduled
        except (ValueError, TypeError):
            return True


class BatchScheduler:
    """Schedules and executes deferred task operations."""
    def __init__(self):
        self._ops: Dict[int, ScheduledOp] = {}
        self._next_id = 1
        self._history: List[ScheduledOp] = []

    def schedule(self, operation, task_ids=None, delay_seconds=0, callback=None, **args):
        """Schedule a new operation."""
        if delay_seconds > 0:
            scheduled_time = (datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)).isoformat()
        else:
            scheduled_time = ""
        op = ScheduledOp(id=self._next_id, operation=operation,
                         task_ids=task_ids or [], scheduled_time=scheduled_time,
                         callback=callback, args=args)
        self._ops[self._next_id] = op
        self._next_id += 1
        return op

    def cancel(self, op_id):
        """Cancel a scheduled operation."""
        if op_id in self._ops and not self._ops[op_id].executed:
            del self._ops[op_id]
            return True
        return False

    def get(self, op_id):
        return self._ops.get(op_id)

    def all_ops(self):
        return list(self._ops.values())

    def pending(self):
        return [op for op in self._ops.values() if not op.executed]

    def due(self):
        """Return operations that are due to execute."""
        return [op for op in self._ops.values() if op.is_due]

    def count(self):
        return len(self._ops)

    def process_due(self):
        """Process all due operations."""
        results = []
        for op in self.due():
            if op.callback:
                try:
                    result = op.callback(op.task_ids, **op.args)
                    op.result = result
                except Exception as e:
                    op.result = {"error": str(e)}
            else:
                op.result = {"executed": True, "task_ids": op.task_ids}
            op.executed = True
            self._history.append(op)
            results.append({"id": op.id, "operation": op.operation,
                            "task_count": len(op.task_ids), "result": op.result})
            if op.id in self._ops:
                del self._ops[op.id]
        return results

    def history(self):
        return list(self._history)

    def clear_history(self):
        self._history = []

    def clear_all(self):
        self._ops = {}
        self._history = []
        self._next_id = 1


def scheduler_report(scheduler):
    """Generate a scheduler status report."""
    return {
        "total_scheduled": scheduler.count(),
        "pending": len(scheduler.pending()),
        "due": len(scheduler.due()),
        "executed": len(scheduler.history()),
        "operations": [op.operation for op in scheduler.pending()],
    }
