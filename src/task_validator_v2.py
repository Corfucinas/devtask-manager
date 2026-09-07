"""Task validator v2 with comprehensive rules."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ValidationRule:
    """A validation rule."""
    id: int
    name: str
    check: Callable
    severity: str = "error"  # error, warning, info
    message: str = ""
    enabled: bool = True

    def run(self, task) -> bool:
        """Returns True if check passes."""
        if not self.enabled:
            return True
        try:
            return self.check(task)
        except Exception:
            return False


@dataclass
class ValidationResult:
    """Result of a validation run."""
    task_id: int
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    passed: List[str] = field(default_factory=list)


class ValidatorV2:
    """Validates tasks against rules."""
    def __init__(self):
        self._rules: Dict[int, ValidationRule] = {}
        self._next_id = 1

    def add_rule(self, name: str, check: Callable, severity: str = "error",
                 message: str = "") -> ValidationRule:
        rule = ValidationRule(id=self._next_id, name=name, check=check,
                               severity=severity, message=message)
        self._rules[self._next_id] = rule
        self._next_id += 1
        return rule

    def remove_rule(self, rule_id: int) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_rule(self, rule_id: int) -> Optional[ValidationRule]:
        return self._rules.get(rule_id)

    def all_rules(self) -> List[ValidationRule]:
        return list(self._rules.values())

    def enabled_rules(self) -> List[ValidationRule]:
        return [r for r in self._rules.values() if r.enabled]

    def enable(self, rule_id: int) -> bool:
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            return True
        return False

    def disable(self, rule_id: int) -> bool:
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            return True
        return False

    def count(self) -> int:
        return len(self._rules)

    def validate(self, task) -> ValidationResult:
        """Run all rules against a task."""
        result = ValidationResult(task_id=getattr(task, "id", 0))
        for rule in self.enabled_rules():
            passed = rule.run(task)
            if passed:
                result.passed.append(rule.name)
            elif rule.severity == "error":
                result.errors.append(f"[{rule.name}] {rule.message}")
                result.valid = False
            elif rule.severity == "warning":
                result.warnings.append(f"[{rule.name}] {rule.message}")
        return result

    def validate_batch(self, tasks) -> List[ValidationResult]:
        """Validate multiple tasks."""
        return [self.validate(t) for t in tasks]

    def is_valid(self, task) -> bool:
        """Check if task passes all error rules."""
        return self.validate(task).valid

    def failing_rules(self, task) -> List[ValidationRule]:
        """Return rules that failed for a task."""
        failing = []
        for rule in self.enabled_rules():
            if not rule.run(task):
                failing.append(rule)
        return failing


def validation_summary(validator: ValidatorV2, tasks) -> Dict:
    """Generate validation summary for multiple tasks."""
    results = validator.validate_batch(tasks)
    total_checks = sum(len(r.passed) + len(r.errors) + len(r.warnings) for r in results)
    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    valid_count = sum(1 for r in results if r.valid)
    return {
        "total_tasks": len(tasks),
        "valid_tasks": valid_count,
        "invalid_tasks": len(tasks) - valid_count,
        "total_checks": total_checks,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "pass_rate": round(valid_count / max(len(tasks), 1) * 100, 1),
        "rules_enabled": len(validator.enabled_rules()),
    }


def default_validator() -> ValidatorV2:
    """Create a validator with default rules."""
    v = ValidatorV2()
    v.add_rule("Has title", lambda t: bool((getattr(t, "title", "") or "").strip()),
               "error", "Task must have a title")
    v.add_rule("Has description",
               lambda t: bool((getattr(t, "description", "") or "").strip()),
               "warning", "Task should have a description")
    v.add_rule("Has assignee", lambda t: bool(getattr(t, "assignee", None)),
               "warning", "Task should have an assignee")
    v.add_rule("Title length", lambda t: len(getattr(t, "title", "")) <= 200,
               "error", "Title must be 200 chars or less")
    v.add_rule("Has tags", lambda t: bool(getattr(t, "tags", None)),
               "info", "Task should have tags")
    return v
