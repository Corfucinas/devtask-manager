"""Tests for task exporter with multiple formats."""
import json
import pytest
from src.task_exporter_v2 import (
    ExportConfig, TaskExporterV2, export_tasks, export_single, export_report, default_config,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id=1, title="Task", description="Desc", priority="medium",
                 status="todo", tags=None, assignee=None):
        self.id = id
        self.title = title
        self.description = description
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        self.assignee = assignee


@pytest.fixture
def tasks():
    return [FakeTask(1, "Bug", priority="high", tags=["bug"]),
            FakeTask(2, "Feature", priority="low", status="done")]


def test_export_json(tasks):
    data = export_tasks(tasks, ExportConfig(format="json"))
    parsed = json.loads(data)
    assert len(parsed) == 2
    assert parsed[0]["title"] == "Bug"


def test_export_csv(tasks):
    data = export_tasks(tasks, ExportConfig(format="csv"))
    assert "id" in data
    assert "Bug" in data


def test_export_xml(tasks):
    data = export_tasks(tasks, ExportConfig(format="xml"))
    assert "<tasks>" in data
    assert "<title>Bug</title>" in data


def test_export_markdown(tasks):
    data = export_tasks(tasks, ExportConfig(format="markdown"))
    assert "# Task Export" in data
    assert "Bug" in data
    assert "|" in data


def test_export_yaml(tasks):
    data = export_tasks(tasks, ExportConfig(format="yaml"))
    assert "-" in data
    assert "title: Bug" in data


def test_export_single(tasks):
    data = export_single(tasks[0], ExportConfig(format="json"))
    parsed = json.loads(data)
    assert parsed[0]["title"] == "Bug"


def test_export_empty():
    data = export_tasks([], ExportConfig(format="json"))
    assert json.loads(data) == []


def test_export_metadata(tasks):
    config = ExportConfig(format="json", include_metadata=True)
    data = export_tasks(tasks, config)
    parsed = json.loads(data)
    assert "_exported_at" in parsed[0]


def test_export_custom_fields(tasks):
    config = ExportConfig(format="json", fields=["id", "title"])
    data = export_tasks(tasks, config)
    parsed = json.loads(data)
    assert len(parsed[0]) == 2


def test_export_report(tasks):
    report = export_report(tasks, ExportConfig(format="json"))
    assert report["task_count"] == 2
    assert report["format"] == "json"
    assert report["output_size_bytes"] > 0


def test_default_config():
    config = default_config()
    assert config.format == "json"
    assert "id" in config.fields


def test_export_invalid_format(tasks):
    with pytest.raises(ValueError):
        export_tasks(tasks, ExportConfig(format="invalid"))
