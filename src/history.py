"""Task history tracking for audit trail."""
from datetime import datetime, timezone
from .models import Task

class TaskHistory:
    def __init__(self):
        self._entries = []

    def record(self, task, action, old_value=None, new_value=None):
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "task_id": task.id, "task_title": task.title, "action": action, "old_value": old_value, "new_value": new_value}
        self._entries.append(entry)
        return entry

    def record_create(self, task):
        return self.record(task, "created", new_value=task.to_dict())

    def record_update(self, task, field, old_value, new_value):
        return self.record(task, f"updated_{field}", old_value, new_value)

    def record_delete(self, task):
        return self.record(task, "deleted", old_value=task.to_dict())

    def record_status_change(self, task, old_status, new_status):
        return self.record(task, "status_changed", old_status, new_status)

    def get_history(self, task_id=None):
        if task_id is None:
            return list(self._entries)
        return [e for e in self._entries if e["task_id"] == task_id]

    def get_recent(self, count=10):
        return list(reversed(self._entries[-count:]))

    def get_stats(self):
        from collections import Counter
        actions = Counter(e["action"] for e in self._entries)
        return {"total_entries": len(self._entries), "actions": dict(actions), "unique_tasks": len(set(e["task_id"] for e in self._entries))}

    def clear(self):
        self._entries.clear()
