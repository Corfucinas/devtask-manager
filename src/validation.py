"""Cross-field validation rules engine."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional


@dataclass
class ValidationRule:
    """A single validation rule with a check function."""
    id: int
    name: str
    check: Callable
    message: str = "Validation failed"
    severity: str = "error"
    enabled: bool = True


@dataclass
class ValidationResult:
    """Result of running validation rules."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    passed: List[str] = field(default_factory=list)

    def add_error(self, message):
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message):
        self.warnings.append(message)

    def add_pass(self, rule_name):
        self.passed.append(rule_name)


class ValidationEngine:
    """Runs validation rules against tasks."""

    def __init__(self):
        self._rules: Dict[int, ValidationRule] = {}
        self._next_id = 1

    def add_rule(self, name, check, message="Validation failed", severity="error"):
        rule = ValidationRule(id=self._next_id, name=name, check=check,
                              message=message, severity=severity)
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

    def find_by_name(self, name):
        for r in self._rules.values():
            if r.name.lower() == name.lower():
                return r
        return None

    def all_rules(self):
        return list(self._rules.values())

    def enabled_rules(self):
        return [r for r in self._rules.values() if r.enabled]

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

    def count(self):
        return len(self._rules)

    def validate(self, task):
        result = ValidationResult(valid=True)
        for rule in self.enabled_rules():
            try:
                passed = rule.check(task)
            except Exception:
                passed = False
            if passed:
                result.add_pass(rule.name)
            else:
                if rule.severity == "error":
                    result.add_error(f"[{rule.name}] {rule.message}")
                elif rule.severity == "warning":
                    result.add_warning(f"[{rule.name}] {rule.message}")
        return result

    def validate_batch(self, tasks):
        return [self.validate(t) for t in tasks]

    def validate_and_filter(self, tasks):
        valid = []
        invalid = []
        for task in tasks:
            result = self.validate(task)
            if result.valid:
                valid.append(task)
            else:
                invalid.append((task, result))
        return valid, invalid


def default_rules():
    """Create an engine with common default validation rules."""
    engine = ValidationEngine()

    def title_not_empty(task):
        title = getattr(task, "title", "")
        return bool(title and title.strip())

    def title_length(task):
        title = getattr(task, "title", "")
        return len(title) <= 200

    def has_assignee_if_high_priority(task):
        priority = task.priority.value if hasattr(task.priority, "value") else task.priority
        if priority in ("high", "critical"):
            return bool(getattr(task, "assignee", None))
        return True

    def due_date_in_future(task):
        due = getattr(task, "due_date", None)
        if due:
            try:
                dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
                return dt > datetime.now(timezone.utc)
            except (ValueError, TypeError):
                return False
        return True

    def description_present_if_not_trivial(task):
        priority = task.priority.value if hasattr(task.priority, "value") else task.priority
        if priority == "low":
            return True
        desc = getattr(task, "description", "") or ""
        return len(desc.strip()) > 0

    engine.add_rule("title_not_empty", title_not_empty,
                    "Task title must not be empty", "error")
    engine.add_rule("title_length", title_length,
                    "Task title must be 200 characters or less", "error")
    engine.add_rule("has_assignee_if_high_priority", has_assignee_if_high_priority,
                    "High/critical priority tasks must have an assignee", "error")
    engine.add_rule("due_date_in_future", due_date_in_future,
                    "Due date must be in the future", "warning")
    engine.add_rule("description_required", description_present_if_not_trivial,
                    "Non-trivial tasks should have a description", "warning")
    return engine
