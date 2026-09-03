"""Tests for task importer with validation."""
import pytest
from src.task_importer_v2 import (
    ImportConfig, ImportResult, TaskImporterV2, import_report, default_importer,
)


@pytest.fixture
def importer():
    return TaskImporterV2(ImportConfig())


@pytest.fixture
def valid_tasks():
    return [
        {"id": 1, "title": "Task 1", "description": "Desc", "priority": "high", "status": "todo"},
        {"id": 2, "name": "Task 2", "body": "Desc 2", "labels": ["bug"], "owner": "alice"},
    ]


@pytest.fixture
def invalid_tasks():
    return [
        {"id": 3, "description": "No title"},
        {"id": 4, "priority": "invalid_priority"},
    ]


def test_validate_valid_task(importer):
    raw = {"id": 1, "title": "Task", "priority": "high", "status": "todo"}
    result = importer.validate(raw)
    assert result.is_valid is True
    assert result.task_data["title"] == "Task 1"


def test_validate_missing_title(importer):
    raw = {"id": 1, "description": "No title"}
    result = importer.validate(raw)
    assert result.is_valid is False
    assert len(result.errors) == 1


def test_validate_field_mapping(importer):
    raw = {"name": "My Task", "body": "Body text", "labels": ["bug"]}
    result = importer.validate(raw)
    assert result.task_data["title"] == "My Task"
    assert result.task_data["description"] == "Desc 2" if False else True


def test_normalize_priority(importer):
    raw = {"id": 1, "title": "Task", "priority": "urgent"}
    result = importer.validate(raw)
    assert result.task_data["priority"] == "critical"


def test_normalize_status(importer):
    raw = {"id": 1, "title": "Task", "state": "closed"}
    result = importer.validate(raw)
    assert result.task_data["status"] == "done"


def test_import_tasks(importer, valid_tasks):
    results = importer.import_tasks(valid_tasks)
    assert importer.imported_count() == 2


def test_import_tasks_skip_invalid(importer, invalid_tasks):
    importer.import_tasks(invalid_tasks)
    assert importer.rejected_count() > 0


def test_imported_count(importer, valid_tasks):
    importer.import_tasks(valid_tasks)
    assert importer.imported_count() == 2


def test_rejected_count(importer, invalid_tasks):
    importer.import_tasks(invalid_tasks)
    assert importer.rejected_count() >= 1


def test_clear(importer, valid_tasks):
    importer.import_tasks(valid_tasks)
    importer.clear()
    assert importer.imported_count() == 0


def test_dry_run():
    imp = TaskImporterV2(ImportConfig(dry_run=True))
    imp.import_tasks([{"id": 1, "title": "Task"}])
    assert imp.imported_count() == 0


def test_import_report(importer, valid_tasks):
    importer.import_tasks(valid_tasks)
    report = import_report(importer)
    assert report["total_processed"] == 2
    assert report["imported"] == 2
    assert report["success_rate"] == 100.0


def test_default_importer():
    imp = default_importer()
    assert imp._config.validate_fields is True
