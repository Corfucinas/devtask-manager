"""Task warden for quality enforcement."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional


@dataclass
class QualityCheck:
    """A single quality check for tasks."""
    id: int
    name: str
    check: Callable
    severity: str = "error"  # error, warning, info
    message: str = ""
    enabled: bool = True

    def run(self, task) -> bool:
        """Returns True if check passes, False if it fails."""
        if not self.enabled:
            return True
        try:
            return self.check(task)
        except Exception:
            return False


class TaskWarden:
    """Enforces quality rules on tasks."""
    def __init__(self):
        self._checks: Dict[int, QualityCheck] = {}
        self._next_id = 1
        self._results: List[dict] = []

    def add_check(self, name, check, severity="error", message=""):
        qc = QualityCheck(id=self._next_id, name=name, check=check,
                          severity=severity, message=message)
        self._checks[self._next_id] = qc
        self._next_id += 1
        return qc

    def remove_check(self, check_id):
        if check_id in self._checks:
            del self._checks[check_id]
            return True
        return False

    def get_check(self, check_id):
        return self._checks.get(check_id)

    def all_checks(self):
        return list(self._checks.values())

    def enabled_checks(self):
        return [c for c in self._checks.values() if c.enabled]

    def enable(self, check_id):
        if check_id in self._checks:
            self._checks[check_id].enabled = True
            return True
        return False

    def disable(self, check_id):
        if check_id in self._checks:
            self._checks[check_id].enabled = False
            return True
        return False

    def count(self):
        return len(self._checks)

    def check_task(self, task):
        """Run all quality checks on a single task."""
        results = []
        for check in self.enabled_checks():
            passed = check.run(task)
            result = {
                "check_id": check.id,
                "check_name": check.name,
                "severity": check.severity,
                "passed": passed,
                "message": check.message if not passed else "",
                "task_id": getattr(task, "id", None),
            }
            results.append(result)
            self._results.append(result)
        return results

    def check_batch(self, tasks):
        """Run quality checks on multiple tasks."""
        all_results = []
        for task in tasks:
            all_results.extend(self.check_task(task))
        return all_results

    def failing_checks(self, task):
        """Return only failing checks for a task."""
        return [r for r in self.check_task(task) if not r["passed"]]

    def blocking_checks(self, task):
        """Return failing checks with error severity."""
        return [r for r in self.failing_checks(task) if r["severity"] == "error"]

    def can_complete(self, task):
        """Check if task can be marked as complete (no blocking checks fail)."""
        return len(self.blocking_checks(task)) == 0

    def results(self):
        return list(self._results)

    def clear_results(self):
        self._results = []


def warden_report(warden, tasks):
    """Generate a quality compliance report."""
    all_results = warden.check_batch(tasks)
    total = len(all_results)
    passed = sum(1 for r in all_results if r["passed"])
    failed = total - passed
    errors = sum(1 for r in all_results if not r["passed"] and r["severity"] == "error")
    warnings = sum(1 for r in all_results if not r["passed"] and r["severity"] == "warning")
    return {
        "total_tasks": len(tasks),
        "total_checks_run": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "warnings": warnings,
        "pass_rate": round(passed / max(total, 1) * 100, 1),
        "compliant_tasks": sum(1 for t in tasks if warden.can_complete(t)),
    }


def default_warden():
    """Create a warden with default quality checks."""
    w = TaskWarden()

    def has_title(task, context=None):
        return bool((getattr(task, "title", "") or "").strip())

    def has_description(task, context=None):
        priority = task.priority.value if hasattr(task.priority, "value") else task.priority
        if priority in ("high", "critical"):
            return bool((getattr(task, "description", "") or "").strip())
        return True

    def has_assignee_if_not_trivial(task, context=None):
        priority = task.priority.value if hasattr(task.priority, "value") else task.priority
        if priority in ("high", "critical"):
            return bool(getattr(task, "assignee", None))
        return True

    def title_not_too_long(task, context=None):
        return len(getattr(task, "title", "")) <= 200

    w.add_check("Has title", has_title, "error", "Task must have a title")
    w.add_check("Has description for high", has_description, "warning",
                "High/critical tasks should have a description")
    w.add_check("Has assignee for high", has_assignee_if_not_trivial, "error",
                "High/critical tasks must have an assignee")
    w.add_check("Title length", title_not_too_long, "warning",
                "Title should be 200 characters or less")
    return w
