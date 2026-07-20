"""Task archiving system for completed tasks."""

import json
import os
from datetime import datetime, timezone


class TaskArchiver:
    """Archives completed tasks to a separate JSON file."""

    def __init__(self, archive_path="archive.json"):
        self.archive_path = archive_path
        self._ensure_archive()

    def _ensure_archive(self):
        if not os.path.exists(self.archive_path):
            with open(self.archive_path, "w") as f:
                json.dump([], f)

    def _read_archive(self):
        with open(self.archive_path, "r") as f:
            return json.load(f)

    def _write_archive(self, data):
        with open(self.archive_path, "w") as f:
            json.dump(data, f, indent=2)

    def archive_task(self, task_dict):
        """Move a completed task to the archive."""
        archive = self._read_archive()
        task_dict["archived_at"] = datetime.now(timezone.utc).isoformat()
        archive.append(task_dict)
        self._write_archive(archive)
        return True

    def archive_completed(self, tasks):
        """Archive all completed tasks from a task list.
        Returns (archived_count, remaining_tasks)."""
        completed = [t for t in tasks if t.get("status") == "done"]
        remaining = [t for t in tasks if t.get("status") != "done"]
        for task in completed:
            self.archive_task(task)
        return len(completed), remaining

    def list_archived(self, limit=None, tag=None):
        """List archived tasks with optional filtering."""
        archive = self._read_archive()
        if tag:
            archive = [t for t in archive if tag in t.get("tags", [])]
        if limit:
            archive = archive[-limit:]
        return archive

    def restore_task(self, task_id):
        """Restore a task from archive back to active."""
        archive = self._read_archive()
        for i, task in enumerate(archive):
            if task.get("id") == task_id:
                restored = archive.pop(i)
                restored.pop("archived_at", None)
                restored["status"] = "todo"
                self._write_archive(archive)
                return restored
        return None

    def archive_stats(self):
        """Return statistics about the archive."""
        archive = self._read_archive()
        tags = {}
        for task in archive:
            for tag in task.get("tags", []):
                tags[tag] = tags.get(tag, 0) + 1
        return {
            "total_archived": len(archive),
            "by_tag": tags,
        }
