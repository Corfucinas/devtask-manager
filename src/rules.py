"""Automation rules engine for task lifecycle events."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional


@dataclass
class Rule:
    """An automation rule with trigger, condition, and action."""
    id: int
    name: str
    trigger: str
    condition: Optional[Callable] = None
    action: Optional[Callable] = None
    enabled: bool = True
    fired_count: int = 0
    last_fired: Optional[str] = None


class RuleEngine:
    """Evaluates and fires automation rules."""

    def __init__(self):
        self._rules: Dict[int, Rule] = {}
        self._next_id = 1

    def add_rule(self, name: str, trigger: str,
                 condition: Callable = None, action: Callable = None) -> Rule:
        rule = Rule(id=self._next_id, name=name, trigger=trigger,
                    condition=condition, action=action)
        self._rules[self._next_id] = rule
        self._next_id += 1
        return rule

    def remove_rule(self, rule_id: int) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_rule(self, rule_id: int) -> Optional[Rule]:
        return self._rules.get(rule_id)

    def all_rules(self) -> List[Rule]:
        return list(self._rules.values())

    def rules_for_trigger(self, trigger: str) -> List[Rule]:
        return [r for r in self._rules.values() if r.trigger == trigger and r.enabled]

    def enable_rule(self, rule_id: int) -> bool:
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            return True
        return False

    def disable_rule(self, rule_id: int) -> bool:
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            return True
        return False

    def evaluate(self, trigger: str, task, context: dict = None) -> List[Rule]:
        context = context or {}
        fired = []
        for rule in self.rules_for_trigger(trigger):
            condition_met = True
            if rule.condition:
                try:
                    condition_met = rule.condition(task, context)
                except Exception:
                    condition_met = False
            if condition_met and rule.action:
                try:
                    rule.action(task, context)
                except Exception:
                    continue
                rule.fired_count += 1
                rule.last_fired = datetime.now(timezone.utc).isoformat()
                fired.append(rule)
        return fired

    def rule_count(self) -> int:
        return len(self._rules)

    def enabled_count(self) -> int:
        return sum(1 for r in self._rules.values() if r.enabled)

    def fired_rules(self) -> List[Rule]:
        return [r for r in self._rules.values() if r.fired_count > 0]


def make_condition_priority_high():
    def condition(task, context):
        priority = task.priority.value if hasattr(task.priority, "value") else task.priority
        return priority == "high"
    return condition


def make_action_set_tag(tag: str):
    def action(task, context):
        if not hasattr(task, "tags"):
            task.tags = []
        if tag not in task.tags:
            task.tags.append(tag)
    return action


def make_action_notify(channel: str):
    def action(task, context):
        if not hasattr(task, "notifications"):
            task.notifications = []
        task.notifications.append({
            "channel": channel,
            "task_id": getattr(task, "id", None),
            "sent_at": datetime.now(timezone.utc).isoformat(),
        })
    return action
