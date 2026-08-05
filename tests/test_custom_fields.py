"""Tests for custom field definitions."""
import pytest
from src.custom_fields import (
    CustomField, CustomFieldRegistry, set_field, get_field,
    remove_field, has_field, apply_defaults, field_summary,
)


class FakeTask:
    def __init__(self):
        self.custom_fields = None


@pytest.fixture
def registry():
    r = CustomFieldRegistry()
    r.register("estimated_cost", "float", "Cost in USD", default=0.0)
    r.register("component", "choice", "Component", choices=["frontend", "backend", "infra"])
    r.register("blocked_by", "string", "Blocking dependency", required=False)
    return r


def test_custom_field_validate_string():
    cf = CustomField(id=1, name="note", field_type="string")
    assert cf.validate("hello") is True
    assert cf.validate(123) is False


def test_custom_field_validate_int():
    cf = CustomField(id=1, name="count", field_type="int")
    assert cf.validate(5) is True
    assert cf.validate("5") is False


def test_custom_field_validate_choice():
    cf = CustomField(id=1, name="level", field_type="choice", choices=["low", "high"])
    assert cf.validate("low") is True
    assert cf.validate("medium") is False


def test_custom_field_validate_required():
    cf = CustomField(id=1, name="req", field_type="string", required=True)
    assert cf.validate(None) is False


def test_registry_register():
    r = CustomFieldRegistry()
    cf = r.register("test", "string")
    assert cf.id == 1
    assert cf.name == "test"


def test_registry_get(registry):
    assert registry.get(1) is not None
    assert registry.get(1).name == "estimated_cost"
    assert registry.get(999) is None


def test_registry_get_by_name(registry):
    cf = registry.get_by_name("component")
    assert cf is not None
    assert cf.field_type == "choice"


def test_registry_remove(registry):
    assert registry.remove(1) is True
    assert registry.get(1) is None
    assert registry.get_by_name("estimated_cost") is None


def test_registry_all_fields(registry):
    fields = registry.all_fields()
    assert len(fields) == 3


def test_registry_count(registry):
    assert registry.count() == 3


def test_registry_required_fields():
    r = CustomFieldRegistry()
    r.register("optional", "string", required=False)
    r.register("mandatory", "string", required=True)
    assert r.required_fields() == ["mandatory"]


def test_validate_all(registry):
    values = {"estimated_cost": "not_a_float", "component": "unknown"}
    errors = registry.validate_all(values)
    assert len(errors) == 2


def test_set_field():
    task = FakeTask()
    assert set_field(task, "cost", 50.0) is True
    assert task.custom_fields["cost"] == 50.0


def test_set_field_with_registry(registry):
    task = FakeTask()
    assert set_field(task, "estimated_cost", 100.0, registry) is True
    assert set_field(task, "estimated_cost", "bad", registry) is False


def test_get_field():
    task = FakeTask()
    task.custom_fields = {"cost": 50.0}
    assert get_field(task, "cost") == 50.0
    assert get_field(task, "missing", "default") == "default"


def test_remove_field():
    task = FakeTask()
    task.custom_fields = {"cost": 50.0}
    assert remove_field(task, "cost") is True
    assert "cost" not in task.custom_fields


def test_has_field():
    task = FakeTask()
    task.custom_fields = {"cost": 50.0}
    assert has_field(task, "cost") is True
    assert has_field(task, "missing") is False


def test_apply_defaults(registry):
    task = FakeTask()
    apply_defaults(task, registry)
    assert task.custom_fields["estimated_cost"] == 0.0


def test_apply_defaults_preserves_existing(registry):
    task = FakeTask()
    task.custom_fields = {"estimated_cost": 500.0}
    apply_defaults(task, registry)
    assert task.custom_fields["estimated_cost"] == 500.0


def test_field_summary(registry):
    task = FakeTask()
    task.custom_fields = {"estimated_cost": 100.0, "component": "backend"}
    summary = field_summary(task, registry)
    assert summary["count"] == 2
    assert summary["registered"] == 3
