"""Tests for task import."""
import json, os, tempfile, pytest
from src.storage import TaskStore
from src.importer import import_json, import_csv, import_tasks

@pytest.fixture
def store():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    s = TaskStore(path)
    yield s
    os.remove(path)

class TestImportJSON:
    def test_import_single(self, store):
        tasks = import_json(json.dumps([{"title": "Imported task", "priority": "high"}]), store)
        assert len(tasks) == 1
        assert tasks[0].title == "Imported task"
    def test_import_multiple(self, store):
        tasks = import_json(json.dumps([{"title": "A"}, {"title": "B"}, {"title": "C"}]), store)
        assert len(tasks) == 3

class TestImportCSV:
    def test_import_csv(self, store):
        tasks = import_csv("title,priority,tags\nFix bug,high;backend\nWrite docs,low;docs", store)
        assert len(tasks) == 2
        assert tasks[0].title == "Fix bug"

class TestImportTasks:
    def test_unknown_format(self, store):
        with pytest.raises(ValueError, match="Unknown format"):
            import_tasks("[]", format="xml", store=store)
