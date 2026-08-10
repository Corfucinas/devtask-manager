"""Task delegation and escalation rules."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class DelegationRule:
    """A rule for automatic task delegation."""
    id: int
    name: str
    condition: Callable
    target_assignee: str
    priority: int = 0
    enabled: bool = True
    fired_count: int = 0

    def matches(self, task):
        if not self.enabled:
            return False
        try:
            return self.condition(task)
        except Exception:
            return False


@dataclass
class Escalation:
    """A task escalation record."""
    id: int
    task_id: int
    level: int
    from_user: Optional[str]
    to_user: str
    reason: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class DelegationEngine:
    """Manages delegation rules and automatic assignment."""

    def __init__(self):
        self._rules = {}
        self._escalations = {}
        self._next_id = 1
        self._esc_id = 1

    def add_rule(self, name, condition, target_assignee, priority=0):
        rule = DelegationRule(id=self._next_id, name=name, condition=condition,
                              target_assignee=target_assignee, priority=priority)
        self._rules[self._next_id] = rule
        self._next_id += 1
        return rule

    def remove_rule(self, rule_id):
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_rule(self, rule_id):
        return self._rules.get(rule_id)

    def all_rules(self):
        return sorted(self._rules.values(), key=lambda r: -r.priority)

    def enabled_rules(self):
        return [r for r in self.all_rules() if r.enabled]

    def enable_rule(self, rule_id):
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            return True
        return False

    def disable_rule(self, rule_id):
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            return True
        return False

    def delegate(self, task):
        for rule in self.enabled_rules():
            if rule.matches(task):
                old_assignee = getattr(task, "assignee", None)
                task.assignee = rule.target_assignee
                rule.fired_count += 1
                return {"delegated": True, "rule": rule.name,
                        "from": old_assignee, "to": rule.target_assignee}
        return {"delegated": False}

    def escalate(self, task, level=1, reason=""):
        old_assignee = getattr(task, "assignee", None)
        escalation = Escalation(
            id=self._esc_id, task_id=getattr(task, "id", 0), level=level,
            from_user=old_assignee, to_user=f"manager_l{level}", reason=reason)
        self._escalations[self._esc_id] = escalation
        self._esc_id += 1
        task.assignee = escalation.to_user
        task.escalation_level = level
        return escalation

    def escalations_for_task(self, task_id):
        return [e for e in self._escalations.values() if e.task_id == task_id]

    def all_escalations(self):
        return list(self._escalations.values())

    def rule_count(self):
        return len(self._rules)

    def escalation_count(self):
        return len(self._escalations)


def delegation_report(engine, tasks):
    return {"total_rules": engine.rule_count(),
            "enabled_rules": len(engine.enabled_rules()),
            "total_escalations": engine.escalation_count(),
            "fired_rules": sum(r.fired_count for r in engine.all_rules()),
            "rules_fired": [{"name": r.name, "fired_count": r.fired_count,
                             "target": r.target_assignee}
                            for r in engine.all_rules() if r.fired_count > 0]}


def default_delegation_engine():
    engine = DelegationEngine()
    def is_critical(task, context=None):
        p = task.priority.value if hasattr(task.priority, "value") else task.priority
        return p == "critical"
    def is_bug(task, context=None):
        return "bug" in (getattr(task, "tags", []) or [])
    def is_unassigned(task, context=None):
        return not getattr(task, "assignee", None)
    engine.add_rule("Critical to lead", is_critical, "tech_lead", priority=10)
    engine.add_rule("Bugs to QA", is_bug, "qa_team", priority=5)
    engine.add_rule("Unassigned to pool", is_unassigned, "backlog_pool", priority=1)
    return engine
