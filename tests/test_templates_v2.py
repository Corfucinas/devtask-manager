"""Tests for enhanced task templates."""
import pytest
from src.templates_v2 import (
    FieldDefinition, TaskTemplate, TemplateEngine,
    validate_template, default_templates,
)


@pytest.fixture
def engine():
    e = TemplateEngine()
    e.create("Bug", "Fix: {title}",
             fields=[
                 FieldDefinition("severity", "choice", required=True, choices=["low", "high"]),
                 FieldDefinition("steps", "string", required=True),
             ],
             default_tags=["bug"], default_priority="high")
    e.create("Feature", "Feature: {title}",
             fields=[FieldDefinition("effort", "choice", choices=["S", "M", "L"])],
             default_tags=["feature"])
    return e


def test_field_definition_validate_string():
    fd = FieldDefinition("name", "string", required=True)
    assert fd.validate("hello") is True
    assert fd.validate(123) is False
    assert fd.validate(None) is False


def test_field_definition_validate_optional():
    fd = FieldDefinition("name", "string", required=False)
    assert fd.validate(None) is True


def test_field_definition_validate_int():
    fd = FieldDefinition("age", "int", min_value=0, max_value=120)
    assert fd.validate(25) is True
    assert fd.validate(-1) is False
    assert fd.validate(150) is False
    assert fd.validate("25") is False


def test_field_definition_validate_choice():
    fd = FieldDefinition("priority", "choice", choices=["low", "high"])
    assert fd.validate("low") is True
    assert fd.validate("high") is True
    assert fd.validate("critical") is False


def test_field_definition_validate_bool():
    fd = FieldDefinition("active", "bool")
    assert fd.validate(True) is True
    assert fd.validate(False) is True
    assert fd.validate("yes") is False


def test_task_template_field_names(engine):
    template = engine.get(1)
    assert "severity" in template.field_names()
    assert "steps" in template.field_names()


def test_task_template_required_fields(engine):
    template = engine.get(1)
    required = template.required_fields()
    assert "severity" in required
    assert "steps" in required


def test_task_template_get_field(engine):
    template = engine.get(1)
    field = template.get_field("severity")
    assert field is not None
    assert field.field_type == "choice"
    assert template.get_field("nonexistent") is None


def test_engine_create():
    e = TemplateEngine()
    t = e.create("Test", "Test: {title}")
    assert t.id == 1
    assert t.name == "Test"


def test_engine_get(engine):
    assert engine.get(1) is not None
    assert engine.get(999) is None


def test_engine_find_by_name(engine):
    assert engine.find_by_name("Bug") is not None
    assert engine.find_by_name("BUG") is not None
    assert engine.find_by_name("nonexistent") is None


def test_engine_remove(engine):
    assert engine.remove(1) is True
    assert engine.get(1) is None
    assert engine.count() == 1
    assert engine.remove(999) is False


def test_engine_all_templates(engine):
    templates = engine.all_templates()
    assert len(templates) == 2


def test_engine_render(engine):
    result = engine.render(1, title="login bug", severity="high", steps="1. Click login")
    assert result is not None
    assert result["title"] == "Fix: login bug"
    assert result["priority"] == "high"
    assert "bug" in result["tags"]
    assert result["severity"] == "high"


def test_engine_render_missing_template(engine):
    assert engine.render(999) is None


def test_validate_template_valid(engine):
    template = engine.get(1)
    result = validate_template(template, {"severity": "high", "steps": "step1"})
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_template_missing_required(engine):
    template = engine.get(1)
    result = validate_template(template, {"severity": "high"})
    assert result["valid"] is False
    assert any("steps" in e for e in result["errors"])


def test_validate_template_invalid_choice(engine):
    template = engine.get(1)
    result = validate_template(template, {"severity": "critical", "steps": "step1"})
    assert result["valid"] is False


def test_default_templates():
    e = default_templates()
    assert e.count() == 2
    assert e.find_by_name("Bug Report") is not None
    assert e.find_by_name("Feature Request") is not None
