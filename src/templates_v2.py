"""Enhanced task templates with custom fields."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class FieldDefinition:
    """A custom field definition for a task template."""
    name: str
    field_type: str
    required: bool = False
    default: Any = None
    choices: List[str] = field(default_factory=list)
    description: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    def validate(self, value):
        if value is None:
            return not self.required
        if self.field_type == "string":
            if not isinstance(value, str):
                return False
        elif self.field_type == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                return False
        elif self.field_type == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False
        elif self.field_type == "bool":
            if not isinstance(value, bool):
                return False
        elif self.field_type == "list":
            if not isinstance(value, list):
                return False
        elif self.field_type == "choice":
            if value not in self.choices:
                return False
        if self.min_value is not None and isinstance(value, (int, float)):
            if value < self.min_value:
                return False
        if self.max_value is not None and isinstance(value, (int, float)):
            if value > self.max_value:
                return False
        return True


@dataclass
class TaskTemplate:
    """An enhanced task template with custom field definitions."""
    id: int
    name: str
    title_pattern: str = ""
    description_pattern: str = ""
    fields: List[FieldDefinition] = field(default_factory=list)
    default_tags: List[str] = field(default_factory=list)
    default_priority: str = "medium"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def field_names(self):
        return [f.name for f in self.fields]

    def required_fields(self):
        return [f.name for f in self.fields if f.required]

    def get_field(self, name):
        for f in self.fields:
            if f.name == name:
                return f
        return None


class TemplateEngine:
    """Manages and renders task templates."""

    def __init__(self):
        self._templates: Dict[int, TaskTemplate] = {}
        self._next_id = 1

    def create(self, name, title_pattern="", fields=None,
               default_tags=None, default_priority="medium"):
        template = TaskTemplate(
            id=self._next_id, name=name, title_pattern=title_pattern,
            fields=fields or [], default_tags=default_tags or [],
            default_priority=default_priority,
        )
        self._templates[self._next_id] = template
        self._next_id += 1
        return template

    def get(self, template_id):
        return self._templates.get(template_id)

    def find_by_name(self, name):
        for t in self._templates.values():
            if t.name.lower() == name.lower():
                return t
        return None

    def remove(self, template_id):
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False

    def all_templates(self):
        return sorted(self._templates.values(), key=lambda t: t.name)

    def count(self):
        return len(self._templates)

    def render(self, template_id, **values):
        template = self.get(template_id)
        if not template:
            return None
        result = {
            "title": template.title_pattern.format(**values) if template.title_pattern else values.get("title", ""),
            "priority": template.default_priority,
            "tags": list(template.default_tags),
        }
        for field_def in template.fields:
            if field_def.name in values:
                result[field_def.name] = values[field_def.name]
            elif field_def.default is not None:
                result[field_def.name] = field_def.default
        return result


def validate_template(template, values):
    errors = []
    for field_def in template.fields:
        value = values.get(field_def.name)
        if value is None and field_def.required:
            errors.append(f"Missing required field: {field_def.name}")
            continue
        if value is not None and not field_def.validate(value):
            errors.append(f"Invalid value for field '{field_def.name}'")
    return {"valid": len(errors) == 0, "errors": errors}


def default_templates():
    engine = TemplateEngine()
    engine.create(
        "Bug Report", "Fix: {title}",
        fields=[
            FieldDefinition("severity", "choice", required=True, choices=["low", "medium", "high", "critical"]),
            FieldDefinition("steps_to_reproduce", "string", required=True),
            FieldDefinition("actual_behavior", "string", required=True),
        ],
        default_tags=["bug"], default_priority="high",
    )
    engine.create(
        "Feature Request", "Feature: {title}",
        fields=[
            FieldDefinition("user_story", "string", required=True),
            FieldDefinition("estimated_effort", "choice", choices=["S", "M", "L", "XL"]),
        ],
        default_tags=["feature"], default_priority="medium",
    )
    return engine
