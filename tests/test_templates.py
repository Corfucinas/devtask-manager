"""Tests for task templates."""
import os, tempfile, pytest
from src.storage import TaskStore
from src.templates import get_template, list_templates, apply_template

@pytest.fixture
def store():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    s = TaskStore(path)
    yield s
    os.remove(path)

class TestGetTemplate:
    def test_bug(self):
        t = get_template("bug")
        assert t["priority"] == "high"
        assert "bug" in t["tags"]
    def test_unknown(self):
        with pytest.raises(ValueError, match="Unknown template"):
            get_template("nonexistent")

class TestListTemplates:
    def test_lists_all(self):
        templates = list_templates()
        assert "bug" in templates
        assert "feature" in templates

class TestApplyTemplate:
    def test_creates(self, store):
        task = apply_template(store, "bug", "login crash")
        assert "Fix:" in task.title
        assert "login crash" in task.title
        assert task.priority.value == "high"
    def test_docs(self, store):
        task = apply_template(store, "docs", "API reference")
        assert "Docs:" in task.title
