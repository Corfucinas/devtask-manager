"""Custom field definitions for tasks."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class CustomField:
    """A custom field definition."""
    id: int
    name: str
    field_type: str
    description: str = ""
    default: Any = None
    choices: List[str] = field(default_factory=list)
    required: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def validate(self, value):
        if value is None:
            return not self.required
        if self.field_type == "string":
            return isinstance(value, str)
        elif self.field_type == "int":
            return isinstance(value, int) and not isinstance(value, bool)
        elif self.field_type == "float":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif self.field_type == "bool":
            return isinstance(value, bool)
        elif self.field_type == "choice":
            return value in self.choices
        elif self.field_type == "date":
            if not isinstance(value, str):
                return False
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
                return True
            except (ValueError, TypeError):
                return False
        return True


class CustomFieldRegistry:
    """Manages custom field definitions."""

    def __init__(self):
        self._fields: Dict[int, CustomField] = {}
        self._by_name: Dict[str, int] = {}
        self._next_id = 1

    def register(self, name, field_type, description="", default=None,
                 choices=None, required=False):
        cf = CustomField(id=self._next_id, name=name, field_type=field_type,
                         description=description, default=default,
                         choices=choices or [], required=required)
        self._fields[self._next_id] = cf
        self._by_name[name] = self._next_id
        self._next_id += 1
        return cf

    def get(self, field_id):
        return self._fields.get(field_id)

    def get_by_name(self, name):
        fid = self._by_name.get(name)
        return self._fields.get(fid) if fid else None

    def remove(self, field_id):
        if field_id in self._fields:
            name = self._fields[field_id].name
            del self._fields[field_id]
            self._by_name.pop(name, None)
            return True
        return False

    def all_fields(self):
        return sorted(self._fields.values(), key=lambda f: f.name)

    def count(self):
        return len(self._fields)

    def required_fields(self):
        return [f.name for f in self._fields.values() if f.required]

    def validate_all(self, values):
        errors = []
        for cf in self._fields.values():
            value = values.get(cf.name)
            if value is None and cf.required:
                errors.append(f"Missing required field: {cf.name}")
            elif value is not None and not cf.validate(value):
                errors.append(f"Invalid value for field '{cf.name}'")
        return errors


def set_field(task, name, value, registry=None):
    if registry:
        field_def = registry.get_by_name(name)
        if field_def and not field_def.validate(value):
            return False
    if not hasattr(task, "custom_fields") or task.custom_fields is None:
        task.custom_fields = {}
    task.custom_fields[name] = value
    return True


def get_field(task, name, default=None):
    if not hasattr(task, "custom_fields") or not task.custom_fields:
        return default
    return task.custom_fields.get(name, default)


def remove_field(task, name):
    if hasattr(task, "custom_fields") and task.custom_fields and name in task.custom_fields:
        del task.custom_fields[name]
        return True
    return False


def has_field(task, name):
    if not hasattr(task, "custom_fields") or not task.custom_fields:
        return False
    return name in task.custom_fields


def apply_defaults(task, registry):
    if not hasattr(task, "custom_fields") or task.custom_fields is None:
        task.custom_fields = {}
    for cf in registry.all_fields():
        if cf.name not in task.custom_fields and cf.default is not None:
            task.custom_fields[cf.name] = cf.default


def field_summary(task, registry=None):
    fields = getattr(task, "custom_fields", None) or {}
    result = {"count": len(fields), "fields": dict(fields)}
    if registry:
        result["registered"] = registry.count()
        result["missing_required"] = [
            f.name for f in registry.all_fields()
            if f.required and f.name not in fields
        ]
    return result
