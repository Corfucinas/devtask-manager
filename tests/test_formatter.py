"""Tests for output formatting."""
from src.models import Task, Priority, Status
from src.formatter import format_task_line, format_task_detail, format_task_table, colorize

class TestColorize:
    def test_basic_color(self):
        result = colorize("hello", "red")
        assert "hello" in result
        assert "\033[91m" in result
    def test_unknown_color(self):
        assert colorize("hello", "nonexistent") == "hello"

class TestFormatTaskLine:
    def test_basic_task(self):
        task = Task(id=1, title="Fix bug", priority=Priority.HIGH)
        line = format_task_line(task)
        assert "#1" in line
        assert "Fix bug" in line
    def test_done_task(self):
        task = Task(id=2, title="Done", status=Status.DONE)
        assert "[x]" in format_task_line(task)
    def test_with_tags(self):
        task = Task(id=3, title="Tagged", tags=["backend"])
        assert "#backend" in format_task_line(task)

class TestFormatTaskTable:
    def test_empty(self):
        assert format_task_table([]) == "No tasks found."
    def test_multiple(self):
        tasks = [Task(id=1, title="First"), Task(id=2, title="Second")]
        table = format_task_table(tasks)
        assert "First" in table
        assert "Second" in table
