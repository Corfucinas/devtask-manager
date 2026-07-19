"""Tests for snapshot functionality."""
import os, tempfile, pytest
from src.storage import TaskStore
from src.snapshot import TaskSnapshot

@pytest.fixture
def setup():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = TaskStore(path)
    snap = TaskSnapshot()
    store.create("Task A", priority="high")
    store.create("Task B", priority="low")
    yield store, snap
    os.remove(path)

class TestCapture:
    def test_captures(self, setup):
        store, snap = setup
        s = snap.capture("v1", store.list())
        assert s["name"] == "v1"
        assert s["task_count"] == 2

class TestListSnapshots:
    def test_lists(self, setup):
        store, snap = setup
        snap.capture("v1", store.list())
        snap.capture("v2", store.list())
        assert len(snap.list_snapshots()) == 2

class TestCompare:
    def test_compares(self, setup):
        store, snap = setup
        snap.capture("before", store.list())
        store.create("Task C")
        snap.capture("after", store.list())
        diff = snap.compare("before", "after")
        assert "Task C" in diff["added"]

class TestDeleteSnapshot:
    def test_deletes(self, setup):
        store, snap = setup
        snap.capture("v1", store.list())
        assert snap.delete_snapshot("v1") is True
        assert snap.delete_snapshot("nonexistent") is False
