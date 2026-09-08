"""Tests for task validator v2."""
import pytest
from src.task_validator_v2 import (
    ValidationRule, ValidationResult, ValidatorV2,
    validation_summary, default_validator,
)


class FakeTask:
    def __init__(self, id=1, title="Task", description="Desc", assignee=None, tags=None):
        self.id = id
        self.title = title
        self.description = description
        self.assignee = assignee
        self.tags = tags or []


@pytest.fixture
def validator():
    v = ValidatorV2()
    v.add_rule("Has title", lambda t: bool((t.title or "").strip()), "error", "No title")
    v.add_rule("Has assignee", lambda t: bool(t.assignee), "warning", "No assignee")
    v.add_rule("Has tags", lambda t: bool(t.tags), "info", "No tags")
    return v


def test_add_rule():
    v = ValidatorV2()
    rule = v.add_rule("test", lambda t: True)
    assert rule.id == 1
    assert v.count() == 1


def test_remove_rule(validator):
    assert validator.remove_rule(1) is True
    assert validator.get_rule(1) is None
    assert validator.remove_rule(999) is False


def test_get_rule(validator):
    rule = validator.get_rule(1)
    assert rule is not None
    assert rule.name == "Has title"


def test_count(validator):
    assert validator.count() == 3


def test_validate_valid(validator):
    task = FakeTask(1, title="OK", assignee="alice", tags=["bug"])
    result = validator.validate(task)
    assert result.valid is True
    assert len(result.errors) == 0


def test_validate_missing_title(validator):
    task = FakeTask(1, title="")
    result = validator.validate(task)
    assert result.valid is False
    assert len(result.errors) == 1
    assert "Has title" in result.errors[0]


def test_validate_warnings(validator):
    task = FakeTask(1, title="OK")
    result = validator.validate(task)
    assert result.valid is True  # warnings don't make invalid
    assert len(result.warnings) >= 1


def test_validate_batch(validator):
    tasks = [FakeTask(1, title="OK", assignee="a", tags=["t"]), FakeTask(2, title="")]
    results = validator.validate_batch(tasks)
    assert len(results) == 2
    assert results[0].valid is True
    assert results[1].valid is False


def test_is_valid(validator):
    assert validator.is_valid(FakeTask(1, title="OK", assignee="a", tags=["t"])) is True
    assert validator.is_valid(FakeTask(2, title="")) is False


def test_failing_rules(validator):
    task = FakeTask(1, title="")
    failing = validator.failing_rules(task)
    assert len(failing) >= 1


def test_enable_disable(validator):
    assert validator.disable(1) is True
    task = FakeTask(1, title="")
    result = validator.validate(task)
    assert result.valid is True  # title check disabled
    assert validator.enable(1) is True


def test_default_validator():
    v = default_validator()
    assert v.count() == 5
    task = FakeTask(1, title="", assignee=None)
    assert v.is_valid(task) is False


def test_default_validator_valid():
    v = default_validator()
    task = FakeTask(1, title="OK", description="Desc", assignee="alice", tags=["bug"])
    assert v.is_valid(task) is True


def test_validation_summary(validator):
    tasks = [FakeTask(1, title="OK", assignee="a", tags=["t"]), FakeTask(2, title="")]
    summary = validation_summary(validator, tasks)
    assert summary["total_tasks"] == 2
    assert summary["valid_tasks"] == 1
    assert summary["pass_rate"] == 50.0


def test_validation_summary_empty():
    v = default_validator()
    summary = validation_summary(v, [])
    assert summary["total_tasks"] == 0


def test_validation_result_defaults():
    result = ValidationResult(task_id=1)
    assert result.valid is True
    assert len(result.errors) == 0
