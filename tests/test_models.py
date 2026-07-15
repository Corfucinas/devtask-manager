"""Tests for Task model."""

import pytest
from src.models import Task, Priority, Status


class TestPriority:
    def test_from_string_valid(self):
        assert Priority.from_string("high") == Priority.HIGH
        assert Priority.from_string("LOW") == Priority.LOW

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            Priority.from_string("urgent")


class TestStatus:
    def test_from_string_valid(self):
        assert Status.from_string("todo") == Status.TODO
        assert Status.from_string("IN-PROGRESS") == Status.IN_PROGRESS

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            Status.from_string("pending")


class TestTask:
    def test_create_task(self):
        task = Task(id=1, title="Test task")
        assert task.id == 1
        assert task.title == "Test task"
        assert task.priority == Priority.MEDIUM
        assert task.status == Status.TODO
        assert task.tags == []

    def test_to_dict(self):
        task = Task(id=1, title="Test", description="desc", tags=["backend"])
        d = task.to_dict()
        assert d["id"] == 1
        assert d["title"] == "Test"
        assert d["priority"] == "medium"
        assert d["status"] == "todo"
        assert d["tags"] == ["backend"]

    def test_from_dict(self):
        data = {
            "id": 1,
            "title": "Test",
            "priority": "high",
            "status": "done",
            "tags": ["frontend"],
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        task = Task.from_dict(data)
        assert task.priority == Priority.HIGH
        assert task.status == Status.DONE

    def test_update_task(self):
        task = Task(id=1, title="Original")
        task.update(title="Updated", status="in-progress", priority="critical")
        assert task.title == "Updated"
        assert task.status == Status.IN_PROGRESS
        assert task.priority == Priority.CRITICAL
