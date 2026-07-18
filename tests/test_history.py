"""Tests for task history."""
import pytest
from src.models import Task, Priority
from src.history import TaskHistory

@pytest.fixture
def history():
    return TaskHistory()

@pytest.fixture
def task():
    return Task(id=1, title="Test task", priority=Priority.HIGH)

class TestTaskHistory:
    def test_record_create(self, history, task):
        entry = history.record_create(task)
        assert entry["action"] == "created"
        assert entry["task_id"] == 1
    def test_record_update(self, history, task):
        entry = history.record_update(task, "title", "Old", "New")
        assert entry["action"] == "updated_title"
    def test_record_delete(self, history, task):
        entry = history.record_delete(task)
        assert entry["action"] == "deleted"
    def test_record_status_change(self, history, task):
        entry = history.record_status_change(task, "todo", "done")
        assert entry["old_value"] == "todo"
    def test_get_history_by_task(self, history, task):
        history.record_create(task)
        history.record_create(Task(id=2, title="Other"))
        result = history.get_history(task_id=1)
        assert len(result) == 1
    def test_get_recent(self, history, task):
        for i in range(15):
            history.record_create(Task(id=i, title=f"Task {i}"))
        assert len(history.get_recent(5)) == 5
    def test_get_stats(self, history, task):
        history.record_create(task)
        history.record_update(task, "title", "Old", "New")
        stats = history.get_stats()
        assert stats["total_entries"] == 2
    def test_clear(self, history, task):
        history.record_create(task)
        history.clear()
        assert len(history.get_history()) == 0
