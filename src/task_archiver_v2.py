"""Enhanced task archiver with retention policies."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


@dataclass
class RetentionPolicy:
    """A retention policy for task archiving."""
    name: str
    max_age_days: int = 90
    only_completed: bool = True
    priority_filter: Optional[str] = None
    tags_filter: List[str] = field(default_factory=list)
    archive_tag: str = "archived"

    def should_archive(self, task) -> bool:
        """Check if a task should be archived by this policy."""
        status = _get_status(task)
        if self.only_completed and status != "done":
            return False
        if self.priority_filter:
            priority = task.priority.value if hasattr(task.priority, "value") else task.priority
            if priority != self.priority_filter:
                return False
        if self.tags_filter:
            tags = set(getattr(task, "tags", []) or [])
            if not any(t in tags for t in self.tags_filter):
                return False
        completed = getattr(task, "completed_at", None)
        if not completed:
            updated = getattr(task, "updated_at", None)
            if not updated:
                return False
            try:
                age = (datetime.now(timezone.utc) - _parse(updated)).days
            except (ValueError, TypeError):
                return False
        else:
            try:
                age = (datetime.now(timezone.utc) - _parse(completed)).days
            except (ValueError, TypeError):
                return False
        return age >= self.max_age_days


class TaskArchiverV2:
    """Enhanced archiver with retention policies."""
    def __init__(self):
        self._policies: List[RetentionPolicy] = []
        self._archived: List[Dict] = []

    def add_policy(self, name, max_age_days=90, only_completed=True,
                   priority_filter=None, tags_filter=None, archive_tag="archived"):
        policy = RetentionPolicy(name=name, max_age_days=max_age_days,
                                 only_completed=only_completed,
                                 priority_filter=priority_filter,
                                 tags_filter=tags_filter or [],
                                 archive_tag=archive_tag)
        self._policies.append(policy)
        return policy

    def remove_policy(self, name) -> bool:
        before = len(self._policies)
        self._policies = [p for p in self._policies if p.name != name]
        return len(self._policies) < before

    def all_policies(self):
        return list(self._policies)

    def policy_count(self):
        return len(self._policies)

    def find_archivable(self, tasks):
        """Find tasks that should be archived."""
        results = []
        for task in tasks:
            for policy in self._policies:
                if policy.should_archive(task):
                    results.append({
                        "task_id": getattr(task, "id", None),
                        "policy_name": policy.name,
                        "archive_tag": policy.archive_tag,
                    })
                    break
        return results

    def archive(self, tasks):
        """Archive tasks based on policies."""
        archivable = self.find_archivable(tasks)
        for entry in archivable:
            task = next((t for t in tasks if getattr(t, "id", None) == entry["task_id"]), None)
            if task:
                tags = getattr(task, "tags", []) or []
                tag = entry["archive_tag"]
                if tag not in tags:
                    tags.append(tag)
                    task.tags = tags
                task._archived = True
                task._archived_at = datetime.now(timezone.utc).isoformat()
            self._archived.append(entry)
        return archivable

    def archived_count(self):
        return len(self._archived)

    def archived_task_ids(self):
        return [e["task_id"] for e in self._archived]

    def clear_history(self):
        self._archived = []


def archive_report(tasks, archiver=None):
    """Generate an archiving report."""
    if archiver is None:
        archiver = TaskArchiverV2()
        archiver.add_policy("Default 90 days", max_age_days=90)
    archivable = archiver.find_archivable(tasks)
    already_archived = sum(1 for t in tasks if "archived" in (getattr(t, "tags", []) or []))
    return {
        "total_tasks": len(tasks),
        "archivable_count": len(archivable),
        "already_archived": already_archived,
        "active_count": len(tasks) - len(archivable) - already_archived,
        "policies": len(archiver.all_policies()),
        "by_policy": {p.name: sum(1 for a in archivable if a["policy_name"] == p.name)
                       for p in archiver.all_policies()},
    }


def default_archiver():
    """Create an archiver with default retention policies."""
    a = TaskArchiverV2()
    a.add_policy("Completed 90 days", max_age_days=90, only_completed=True)
    a.add_policy("Low priority 30 days", max_age_days=30, only_completed=True,
                 priority_filter="low")
    a.add_policy("Bug tasks 60 days", max_age_days=60, only_completed=True,
                 tags_filter=["bug"])
    return a
