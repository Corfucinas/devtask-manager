"""Tests for batch operations."""
import os, tempfile, pytest
from src.storage import TaskStore
from src.batch import BatchOperations

@pytest.fixture
def batch():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = TaskStore(path)
    b = BatchOperations(store)
    store.create("Task A", priority="high")
    store.create("Task B", priority="low")
    store.create("Task C", priority="medium")
    yield b
    os.remove(path)

class TestBatchUpdateStatus:
    def test_bulk_complete(self, batch):
        result = batch.bulk_complete([1, 2])
        assert len(result) == 2
        assert all(t.status.value == "done" for t in result)

class TestBulkAddTag:
    def test_adds_tag(self, batch):
        result = batch.bulk_add_tag([1, 2], "sprint-1")
        assert len(result) == 2
        assert all("sprint-1" in t.tags for t in result)

class TestBulkSetPriority:
    def test_sets_priority(self, batch):
        result = batch.bulk_set_priority([1, 2], "critical")
        assert all(t.priority.value == "critical" for t in result)

class TestBulkDelete:
    def test_deletes(self, batch):
        result = batch.bulk_delete([1, 3])
        assert result == [1, 3]

class TestArchiveCompleted:
    def test_archives(self, batch):
        batch.bulk_complete([1])
        deleted = batch.archive_completed()
        assert 1 in deleted
