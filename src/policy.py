"""Task policy engine with configurable rules."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Policy:
    """A policy rule that can be enforced on tasks."""
    id: int
    name: str
    description: str
    condition: Callable
    action: str = "warn"
    severity: str = "medium"
    enabled: bool = True

    def evaluate(self, task):
        if not self.enabled: return False
        try:
            return self.condition(task)
        except Exception:
            return False


class PolicyEngine:
    """Evaluates policies against tasks."""
    def __init__(self):
        self._policies = {}
        self._next_id = 1
        self._violations = []

    def add(self, name, description, condition, action="warn", severity="medium"):
        p = Policy(id=self._next_id, name=name, description=description,
                   condition=condition, action=action, severity=severity)
        self._policies[self._next_id] = p
        self._next_id += 1
        return p

    def remove(self, policy_id):
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    def get(self, policy_id):
        return self._policies.get(policy_id)

    def all_policies(self):
        return list(self._policies.values())

    def enabled_policies(self):
        return [p for p in self._policies.values() if p.enabled]

    def enable(self, policy_id):
        if policy_id in self._policies:
            self._policies[policy_id].enabled = True
            return True
        return False

    def disable(self, policy_id):
        if policy_id in self._policies:
            self._policies[policy_id].enabled = False
            return True
        return False

    def count(self):
        return len(self._policies)

    def enforce(self, task):
        violations = []
        for policy in self.enabled_policies():
            if policy.evaluate(task):
                v = {"policy_id": policy.id, "policy_name": policy.name,
                     "action": policy.action, "severity": policy.severity,
                     "task_id": getattr(task, "id", None),
                     "description": policy.description}
                violations.append(v)
                self._violations.append(v)
        return violations

    def enforce_batch(self, tasks):
        all_v = []
        for task in tasks:
            all_v.extend(self.enforce(task))
        return all_v

    def violations(self):
        return list(self._violations)

    def violation_count(self):
        return len(self._violations)

    def clear_violations(self):
        self._violations = []

    def blocking_violations(self, tasks):
        return [v for v in self.enforce_batch(tasks) if v["action"] == "block"]


def policy_report(engine, tasks):
    violations = engine.enforce_batch(tasks)
    return {"total_tasks": len(tasks), "total_policies": engine.count(),
            "enabled_policies": len(engine.enabled_policies()),
            "total_violations": len(violations),
            "blocking_violations": sum(1 for v in violations if v["action"] == "block"),
            "warning_violations": sum(1 for v in violations if v["action"] == "warn"),
            "compliant_tasks": len(tasks) - len(set(v["task_id"] for v in violations)),
            "compliance_rate": round(
                (len(tasks) - len(set(v["task_id"] for v in violations))) / max(len(tasks), 1) * 100, 1),
            "violations_by_severity": {
                s: sum(1 for v in violations if v["severity"] == s)
                for s in ("low", "medium", "high", "critical")}}


def default_policies():
    engine = PolicyEngine()
    def no_title(task, context=None):
        return not (getattr(task, "title", "") or "").strip()
    def no_assignee_critical(task, context=None):
        p = task.priority.value if hasattr(task.priority, "value") else task.priority
        if p == "critical": return not getattr(task, "assignee", None)
        return False
    def no_due_high(task, context=None):
        p = task.priority.value if hasattr(task.priority, "value") else task.priority
        if p in ("high", "critical"): return not getattr(task, "due_date", None)
        return False
    def stale(task, context=None):
        updated = getattr(task, "updated_at", None)
        if not updated: return False
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(updated.replace("Z", "+00:00"))).days
            return age > 30
        except: return False
    engine.add("Title required", "Tasks must have a non-empty title", no_title, "block", "critical")
    engine.add("Critical needs assignee", "Critical tasks must have an assignee", no_assignee_critical, "block", "high")
    engine.add("High priority needs due date", "High/critical need due date", no_due_high, "warn", "medium")
    engine.add("No stale tasks", "No 30+ day stale tasks", stale, "warn", "low")
    return engine
