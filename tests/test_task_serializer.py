"""Tests for task serializer."""
import json, pytest
from src.task_serializer import (
    task_to_dict, serialize_tasks, deserialize_tasks,
    serialize_single, serialization_report, compact_serialize,
    SerializerConfig, default_config,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id=1, title="Task", description="Desc", priority="medium",
                 status="todo", tags=None, assignee=None, due_date=None,
                 created_at="2026-01-01", updated_at="2026-01-02"):
        self.id = id
        self.title = title
        self.description = description
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        self.assignee = assignee
        self.due_date = due_date
        self.created_at = created_at
        self.updated_at = updated_at


@pytest.fixture
def tasks():
    return [FakeTask(1, "Bug", priority="high", tags=["bug"]),
            FakeTask(2, "Feature", priority="low", status="done")]


def test_task_to_dict(tasks):
    d = task_to_dict(tasks[0])
    assert d["id"] == 1
    assert d["priority"] == "high"
    assert d["status"] == "todo"
    assert d["tags"] == ["bug"]


def test_task_to_dict_exclude_none():
    task = FakeTask(1, assignee=None)
    config = SerializerConfig(include_none=False)
    d = task_to_dict(task, config)
    assert "assignee" not in d


def test_serialize_json(tasks):
    data = serialize_tasks(tasks, "json")
    parsed = json.loads(data)
    assert len(parsed) == 2
    assert parsed[0]["title"] == "Bug"


def test_serialize_csv(tasks):
    data = serialize_tasks(tasks, "csv")
    assert "id" in data
    assert "title" in data
    assert "Bug" in data


def test_serialize_dict(tasks):
    dicts = serialize_tasks(tasks, "dict")
    assert len(dicts) == 2
    assert dicts[0]["title"] == "Bug"


def test_deserialize_json(tasks):
    data = serialize_tasks(tasks, "json")
    result = deserialize_tasks(data, "json")
    assert len(result) == 2


def test_deserialize_csv(tasks):
    data = serialize_tasks(tasks, "csv")
    result = deserialize_tasks(data, "csv")
    assert len(result) == 2


def test_serialize_single(tasks):
    data = serialize_single(tasks[0], "json")
    parsed = json.loads(data)
    assert parsed["title"] == "Bug"


def test_serialization_report(tasks):
    report = serialization_report(tasks, "json")
    assert report["task_count"] == 2
    assert report["format"] == "json"
    assert report["output_size_bytes"] > 0


def test_compact_serialize(tasks):
    data = compact_serialize(tasks)
    parsed = json.loads(data)
    assert len(parsed) == 2
    assert "\n" not in data  # compact = no newlines


def test_default_config():
    config = default_config()
    assert "id" in config.fields
    assert "title" in config.fields


def test_serialize_empty():
    data = serialize_tasks([], "json")
    assert json.loads(data) == []
