"""JSON file-based storage for tasks."""

import json
import os
from .models import Task, Status, Priority


class TaskStore:
    """CRUD operations for tasks backed by a JSON file."""

    def __init__(self, filepath=None):
        if filepath is None:
            home = os.path.expanduser("~")
            filepath = os.path.join(home, ".devtask", "tasks.json")
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            with open(self.filepath, "w") as f:
                json.dump([], f)

    def _read(self):
        with open(self.filepath, "r") as f:
            return json.load(f)

    def _write(self, tasks):
        with open(self.filepath, "w") as f:
            json.dump(
                [t.to_dict() if isinstance(t, Task) else t for t in tasks], f, indent=2
            )

    def _next_id(self, tasks):
        return max((t["id"] for t in tasks), default=0) + 1

    def create(self, title, description="", priority="medium", tags=None):
        tasks = self._read()
        task = Task(
            id=self._next_id(tasks),
            title=title,
            description=description,
            priority=Priority.from_string(priority),
            tags=tags or [],
        )
        tasks.append(task.to_dict())
        self._write(tasks)
        return task

    def list(self, status=None, priority=None, tag=None):
        tasks = [Task.from_dict(t) for t in self._read()]
        if status:
            tasks = [t for t in tasks if t.status == Status.from_string(status)]
        if priority:
            tasks = [t for t in tasks if t.priority == Priority.from_string(priority)]
        if tag:
            tasks = [t for t in tasks if tag in t.tags]
        return tasks

    def get(self, task_id):
        tasks = self._read()
        data = next((t for t in tasks if t["id"] == task_id), None)
        return Task.from_dict(data) if data else None

    def update(self, task_id, **kwargs):
        tasks = self._read()
        data = next((t for t in tasks if t["id"] == task_id), None)
        if not data:
            return None
        task = Task.from_dict(data)
        task.update(**kwargs)
        tasks = [t if t["id"] != task_id else task.to_dict() for t in tasks]
        self._write(tasks)
        return task

    def delete(self, task_id):
        tasks = self._read()
        original = len(tasks)
        tasks = [t for t in tasks if t["id"] != task_id]
        if len(tasks) == original:
            return False
        self._write(tasks)
        return True
