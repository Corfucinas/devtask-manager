"""Task expirer for automatic task expiration."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


@dataclass
class ExpirationRule:
    """A rule for when tasks should expire."""
    name: str
    max_age_days: int = 30
    status_filter: Optional[str] = None  # only expire tasks with this status
    priority_filter: Optional[str] = None  # only expire tasks with this priority
    tags_filter: List[str] = field(default_factory=list)  # only expire tasks with these tags
    action: str = "archive"  # archive, delete, close, flag

    def applies_to(self, task) -> bool:
        """Check if this rule applies to a task."""
        status = _get_status(task)
        if self.status_filter and status != self.status_filter:
            return False
        priority = task.priority.value if hasattr(task.priority, "value") else task.priority
        if self.priority_filter and priority != self.priority_filter:
            return False
        if self.tags_filter:
            tags = set(getattr(task, "tags", []) or [])
            if not any(t in tags for t in self.tags_filter):
                return False
        return True

    def is_expired(self, task) -> bool:
        """Check if a task is expired by this rule."""
        if not self.applies_to(task):
            return False
        updated = getattr(task, "updated_at", None)
        if not updated:
            return False
        try:
            age = (datetime.now(timezone.utc) - _parse(updated)).days
            return age >= self.max_age_days
        except (ValueError, TypeError):
            return False


class TaskExpirer:
    """Detects and expires old tasks."""
    def __init__(self):
        self._rules: List[ExpirationRule] = []
        self._expired: List[Dict] = []

    def add_rule(self, name, max_age_days=30, status_filter=None,
                 priority_filter=None, tags_filter=None, action="archive"):
        rule = ExpirationRule(name=name, max_age_days=max_age_days,
                              status_filter=status_filter,
                              priority_filter=priority_filter,
                              tags_filter=tags_filter or [],
                              action=action)
        self._rules.append(rule)
        return rule

    def remove_rule(self, name) -> bool:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.name != name]
        return len(self._rules) < before

    def all_rules(self):
        return list(self._rules)

    def rule_count(self):
        return len(self._rules)

    def find_expired(self, tasks):
        """Find all tasks that match any expiration rule."""
        results = []
        for task in tasks:
            for rule in self._rules:
                if rule.is_expired(task):
                    results.append({
                        "task_id": getattr(task, "id", None),
                        "rule_name": rule.name,
                        "action": rule.action,
                        "max_age_days": rule.max_age_days,
                    })
                    break
        return results

    def expire_tasks(self, tasks):
        """Mark expired tasks with the appropriate action."""
        expired = self.find_expired(tasks)
        for entry in expired:
            task = next((t for t in tasks if getattr(t, "id", None) == entry["task_id"]), None)
            if task:
                action = entry["action"]
                if action == "archive":
                    task.status = "done"
                    tags = getattr(task, "tags", []) or []
                    if "archived" not in tags:
                        tags.append("archived")
                        task.tags = tags
                elif action == "close":
                    task.status = "done"
                elif action == "flag":
                    tags = getattr(task, "tags", []) or []
                    if "expired" not in tags:
                        tags.append("expired")
                        task.tags = tags
            self._expired.append(entry)
        return expired

    def expired_count(self):
        return len(self._expired)

    def clear_history(self):
        self._expired = []


def expiration_report(tasks, expirer=None):
    """Generate an expiration report."""
    if expirer is None:
        expirer = TaskExpirer()
        expirer.add_rule("Default 30 days", max_age_days=30, status_filter="todo")
    expired = expirer.find_expired(tasks)
    by_action = {}
    for e in expired:
        by_action[e["action"]] = by_action.get(e["action"], 0) + 1
    return {
        "total_tasks": len(tasks),
        "expired_count": len(expired),
        "by_action": by_action,
        "rules": len(expirer.all_rules()),
        "expirable_count": len(tasks) - len(expired),
    }


def default_expirer():
    """Create an expirer with default rules."""
    e = TaskExpirer()
    e.add_rule("Old todo tasks", max_age_days=30, status_filter="todo", action="archive")
    e.add_rule("Stale in-progress", max_age_days=60, status_filter="in-progress", action="flag")
    e.add_rule("Old low priority", max_age_days=90, status_filter="todo",
               priority_filter="low", action="archive")
    return e
