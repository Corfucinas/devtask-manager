"""Tests for task export."""
import json
import pytest
from src.models import Task, Priority, Status
from src.exporter import export_json, export_csv, export_markdown, export_tasks

@pytest.fixture
def sample_tasks():
    return [Task(id=1, title="Fix bug", priority=Priority.HIGH, tags=["backend"]), Task(id=2, title="Write docs", status=Status.DONE, tags=["docs"])]

class TestExportJSON:
    def test_valid_json(self, sample_tasks):
        data = json.loads(export_json(sample_tasks))
        assert len(data) == 2
        assert data[0]["title"] == "Fix bug"
    def test_empty(self):
        assert json.loads(export_json([])) == []

class TestExportCSV:
    def test_has_header(self, sample_tasks):
        lines = export_csv(sample_tasks).strip().split("\n")
        assert "id" in lines[0]
    def test_data_rows(self, sample_tasks):
        lines = export_csv(sample_tasks).strip().split("\n")
        assert len(lines) == 3
        assert "Fix bug" in lines[1]

class TestExportMarkdown:
    def test_has_table_header(self, sample_tasks):
        result = export_markdown(sample_tasks)
        assert "| ID |" in result

class TestExportTasks:
    def test_unknown_format_raises(self, sample_tasks):
        with pytest.raises(ValueError, match="Unknown format"):
            export_tasks(sample_tasks, format="xml")
    def test_json_via_dispatcher(self, sample_tasks):
        assert json.loads(export_tasks(sample_tasks, format="json"))
