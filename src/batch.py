"""Batch operations for multiple tasks."""
from .models import Task, Status, Priority
from .storage import TaskStore

class BatchOperations:
    def __init__(self, store):
        self.store = store
    def bulk_update_status(self, task_ids, status):
        updated = []
        for tid in task_ids:
            task = self.store.update(tid, status=status)
            if task: updated.append(task)
        return updated
    def bulk_add_tag(self, task_ids, tag):
        updated = []
        for tid in task_ids:
            task = self.store.get(tid)
            if task and tag not in task.tags:
                updated_task = self.store.update(tid, tags=task.tags + [tag])
                updated.append(updated_task)
        return updated
    def bulk_set_priority(self, task_ids, priority):
        updated = []
        for tid in task_ids:
            task = self.store.update(tid, priority=priority)
            if task: updated.append(task)
        return updated
    def bulk_delete(self, task_ids):
        return [tid for tid in task_ids if self.store.delete(tid)]
    def bulk_complete(self, task_ids):
        return self.bulk_update_status(task_ids, "done")
    def archive_completed(self):
        done = self.store.list(status="done")
        return self.bulk_delete([t.id for t in done])
