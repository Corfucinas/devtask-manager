"""Typed store layer with validation over raw dicts."""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class FieldSpec:
    """Specification for one field."""
    name: str
    ftype: str  # int, float, str, bool, list, dict
    required: bool = True
    default: Any = None


VALIDATORS = {
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "str": lambda v: isinstance(v, str),
    "bool": lambda v: isinstance(v, bool),
    "list": lambda v: isinstance(v, list),
    "dict": lambda v: isinstance(v, dict),
}


class TypedStore:
    """Validated, typed access over raw record dicts."""
    def __init__(self, specs: List[FieldSpec], strict: bool = True):
        self._specs = {s.name: s for s in specs}
        self._strict = strict
        self._records: Dict[int, Dict] = {}
        self._validation_errors: List[str] = []

    def validate(self, record: Dict) -> List[str]:
        """Validate a record against the specs; returns error strings."""
        errors = []
        for name, spec in self._specs.items():
            value = record.get(name)
            if value is None:
                if spec.required:
                    errors.append(f"missing required field: {name}")
                continue
            validator = VALIDATORS.get(spec.ftype)
            if validator and not validator(value):
                errors.append(f"field {name}: expected {spec.ftype}, got {type(value).__name__}")
        return errors

    def put(self, key: int, record: Dict) -> bool:
        """Store a record if valid; returns False (and records error) if not."""
        errors = self.validate(record)
        if errors:
            self._validation_errors.extend(errors)
            return False
        # Fill defaults for optional fields
        filled = dict(record)
        for name, spec in self._specs.items():
            if name not in filled and not spec.required:
                filled[name] = spec.default
        self._records[key] = filled
        return True

    def get(self, key: int) -> Optional[Dict]:
        return self._records.get(key)

    def get_field(self, key: int, name: str, default=None) -> Any:
        rec = self._records.get(key)
        if rec is None:
            return default
        return rec.get(name, default)

    def has(self, key: int) -> bool:
        return key in self._records

    def delete(self, key: int) -> bool:
        if key in self._records:
            del self._records[key]
            return True
        return False

    def keys(self) -> List[int]:
        return sorted(self._records.keys())

    def all_records(self) -> List[Dict]:
        return [self._records[k] for k in sorted(self._records.keys())]

    def count(self) -> int:
        return len(self._records)

    def errors(self) -> List[str]:
        return list(self._validation_errors)

    def clear_errors(self):
        self._validation_errors = []

    def clear(self):
        self._records.clear()
        self._validation_errors = []


def default_specs() -> List[FieldSpec]:
    return [
        FieldSpec("id", "int", required=True),
        FieldSpec("title", "str", required=True),
        FieldSpec("priority", "str", required=False, default="medium"),
        FieldSpec("status", "str", required=False, default="todo"),
        FieldSpec("tags", "list", required=False, default=[]),
        FieldSpec("assignee", "str", required=False, default=None),
    ]
