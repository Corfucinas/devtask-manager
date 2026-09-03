"""Enhanced task importer with validation."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


PRIORITY_MAP = {
    "urgent": "critical", "blocker": "critical", "p0": "critical",
    "important": "high", "p1": "high",
    "normal": "medium", "p2": "medium",
    "minor": "low", "p3": "low", "trivial": "low",
}

STATUS_MAP = {
    "open": "todo", "new": "todo", "pending": "todo",
    "working": "in-progress", "wip": "in-progress", "started": "in-progress",
    "resolved": "done", "closed": "done", "complete": "done", "completed": "done",
    "waiting": "review", "qa": "review",
}


@dataclass
class ImportConfig:
    """Configuration for task import."""
    field_mapping: Dict[str, str] = field(default_factory=lambda: {
        "id": "id", "title": "title", "name": "title",
        "description": "description", "body": "description",
        "priority": "priority", "status": "status", "state": "status",
        "tags": "tags", "labels": "tags",
        "assignee": "assignee", "owner": "assignee",
    })
    validate_fields: bool = True
    normalize_values: bool = True
    skip_invalid: bool = True
    dry_run: bool = False


@dataclass
class ImportResult:
    """Result of importing a task."""
    task_data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


class TaskImporterV2:
    """Imports and validates task data."""
    def __init__(self, config=None):
        self._config = config or ImportConfig()
        self._imported: List[Dict] = []
        self._rejected: List[Dict] = []

    def validate(self, raw_task: Dict) -> ImportResult:
        """Validate and transform a raw task."""
        result = ImportResult()
        mapping = self._config.field_mapping
        transformed = {}

        for raw_key, value in raw_task.items():
            field_name = mapping.get(raw_key, raw_key)
            transformed[field_name] = value

        if self._config.validate_fields:
            if not transformed.get("title"):
                result.errors.append("Missing required field: title")
            if transformed.get("priority") and transformed["priority"] not in                 ("critical", "high", "medium", "low"):
                if self._config.normalize_values:
                    transformed["priority"] = PRIORITY_MAP.get(
                        str(transformed["priority"]).lower(), "medium")
                else:
                    result.errors.append(f"Invalid priority: {transformed['priority']}")
            if transformed.get("status") and transformed["status"] not in                 ("todo", "in-progress", "review", "done"):
                if self._config.normalize_values:
                    transformed["status"] = STATUS_MAP.get(
                        str(transformed["status"]).lower(), "todo")
                else:
                    result.errors.append(f"Invalid status: {transformed['status']}")

        result.task_data = transformed if result.is_valid else None
        return result

    def import_tasks(self, raw_tasks: List[Dict]) -> List[ImportResult]:
        """Import a batch of raw tasks."""
        results = []
        for raw in raw_tasks:
            result = self.validate(raw_task=raw_task)
            if result.is_valid:
                if not self._config.dry_run:
                    self._imported.append(result.task_data)
            else:
                if self._config.skip_invalid:
                    self._rejected.append({"task": raw_task, "errors": result.errors})
                results.append(result)
        return results

    def imported(self):
        return list(self._imported)

    def rejected(self):
        return list(self._rejected)

    def imported_count(self):
        return len(self._imported)

    def rejected_count(self):
        return len(self._rejected)

    def clear(self):
        self._imported = []
        self._rejected = []


def import_report(importer: TaskImporterV2) -> Dict:
    """Generate an import summary report."""
    total = importer.imported_count() + importer.rejected_count()
    return {
        "total_processed": total,
        "imported": importer.imported_count(),
        "rejected": importer.rejected_count(),
        "success_rate": round(importer.imported_count() / max(total, 1) * 100, 1),
        "dry_run": importer._config.dry_run,
    }


def default_importer():
    """Create an importer with default config."""
    return TaskImporterV2(ImportConfig())
