"""Tests for TaskStore."""

import os
import tempfile
import pytest
from src.storage import TaskStore
from src.models import Status, Priority


@pytest.fixture
def store():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    s = TaskStore(path)
    yield s
    os.remove(path)


class TestTaskStore:
    def test_create(self, store):
        task = store.create("Fix bug", description="login issue", priority="high")
        assert task.id == 1
        assert task.title == "Fix bug"

    def test_list(self, store):
        store.create("Task 1")
        store.create("Task 2")
        assert len(store.list()) == 2

    def test_list_by_status(self, store):
        store.create("Task 1")
        store.create("Task 2")
        store.update(1, status="done")
        assert len(store.list(status="done")) == 1
        assert len(store.list(status="todo")) == 1

    def test_list_by_tag(self, store):
        store.create("Task 1", tags=["backend"])
        store.create("Task 2", tags=["frontend"])
        assert len(store.list(tag="backend")) == 1

    def test_get(self, store):
        store.create("Find me")
        task = store.get(1)
        assert task.title == "Find me"

    def test_get_not_found(self, store):
        assert store.get(999) is None

    def test_update(self, store):
        store.create("Original")
        task = store.update(1, title="Updated", status="in-progress")
        assert task.title == "Updated"

    def test_delete(self, store):
        store.create("Delete me")
        assert store.delete(1) is True
        assert store.get(1) is None

    def test_delete_not_found(self, store):
        assert store.delete(999) is False
