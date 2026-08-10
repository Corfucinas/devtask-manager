"""SLA tracking and breach detection."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


@dataclass
class SLAPolicy:
    """An SLA policy for a priority level."""
    priority: str
    response_time_hours: float = 24.0
    resolution_time_hours: float = 72.0
    escalation_after_hours: float = 48.0

    def response_breached(self, task):
        status = task.status.value if hasattr(task.status, "value") else task.status
        if status != "todo":
            return False
        created = getattr(task, "created_at", None)
        if not created:
            return False
        try:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - created_dt).total_seconds() / 3600
            return elapsed > self.response_time_hours
        except (ValueError, TypeError):
            return False

    def resolution_breached(self, task):
        status = task.status.value if hasattr(task.status, "value") else task.status
        if status == "done":
            return False
        created = getattr(task, "created_at", None)
        if not created:
            return False
        try:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - created_dt).total_seconds() / 3600
            return elapsed > self.resolution_time_hours
        except (ValueError, TypeError):
            return False


class SLAManager:
    """Manages SLA policies and tracks compliance."""

    def __init__(self):
        self._policies = {}

    def set_policy(self, priority, response_time_hours=24.0,
                   resolution_time_hours=72.0, escalation_after_hours=48.0):
        policy = SLAPolicy(priority=priority, response_time_hours=response_time_hours,
                           resolution_time_hours=resolution_time_hours,
                           escalation_after_hours=escalation_after_hours)
        self._policies[priority] = policy
        return policy

    def get_policy(self, priority):
        return self._policies.get(priority)

    def remove_policy(self, priority):
        if priority in self._policies:
            del self._policies[priority]
            return True
        return False

    def all_policies(self):
        return list(self._policies.values())

    def count(self):
        return len(self._policies)

    def check_sla(self, task):
        priority = task.priority.value if hasattr(task.priority, "value") else task.priority
        policy = self.get_policy(priority)
        if not policy:
            return {"priority": priority, "has_policy": False,
                    "response_breached": False, "resolution_breached": False}
        return {"priority": priority, "has_policy": True,
                "response_breached": policy.response_breached(task),
                "resolution_breached": policy.resolution_breached(task),
                "response_target_hours": policy.response_time_hours,
                "resolution_target_hours": policy.resolution_time_hours}

    def breached_tasks(self, tasks):
        results = []
        for task in tasks:
            sla = self.check_sla(task)
            if sla.get("response_breached") or sla.get("resolution_breached"):
                results.append({"task_id": getattr(task, "id", None),
                                "title": getattr(task, "title", ""),
                                "priority": sla["priority"],
                                "response_breached": sla["response_breached"],
                                "resolution_breached": sla["resolution_breached"]})
        return results

    def at_risk_tasks(self, tasks, threshold_percent=0.8):
        results = []
        now = datetime.now(timezone.utc)
        for task in tasks:
            priority = task.priority.value if hasattr(task.priority, "value") else task.priority
            policy = self.get_policy(priority)
            if not policy:
                continue
            status = task.status.value if hasattr(task.status, "value") else task.status
            if status == "done":
                continue
            created = getattr(task, "created_at", None)
            if not created:
                continue
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                elapsed = (now - created_dt).total_seconds() / 3600
                ratio = elapsed / policy.resolution_time_hours
                if ratio >= threshold_percent and elapsed <= policy.resolution_time_hours:
                    results.append({"task_id": getattr(task, "id", None),
                                    "title": getattr(task, "title", ""),
                                    "elapsed_hours": round(elapsed, 1),
                                    "target_hours": policy.resolution_time_hours,
                                    "percent_elapsed": round(ratio * 100, 1)})
            except (ValueError, TypeError):
                continue
        return results

    def compliance_report(self, tasks):
        total = len(tasks)
        breached = len(self.breached_tasks(tasks))
        at_risk = len(self.at_risk_tasks(tasks))
        return {"total_tasks": total, "breached": breached, "at_risk": at_risk,
                "compliant": total - breached,
                "compliance_rate": round((total - breached) / max(total, 1) * 100, 1),
                "policies_configured": self.count()}


def default_sla_manager():
    manager = SLAManager()
    manager.set_policy("critical", response_time_hours=2, resolution_time_hours=8,
                       escalation_after_hours=4)
    manager.set_policy("high", response_time_hours=8, resolution_time_hours=24,
                       escalation_after_hours=12)
    manager.set_policy("medium", response_time_hours=24, resolution_time_hours=72,
                       escalation_after_hours=48)
    manager.set_policy("low", response_time_hours=48, resolution_time_hours=168,
                       escalation_after_hours=96)
    return manager
