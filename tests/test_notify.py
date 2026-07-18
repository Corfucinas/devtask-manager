"""Tests for notification system."""
import pytest
from src.models import Task, Priority
from src.notify import format_notification, get_due_soon, get_overdue_tasks

class TestFormatNotification:
    def test_overdue(self):
        task = Task(id=1, title="Fix bug", priority=Priority.HIGH)
        msg = format_notification(task, "overdue")
        assert "[!]" in msg
        assert "Fix bug" in msg
    def test_due_soon(self):
        task = Task(id=2, title="Write docs", priority=Priority.LOW)
        msg = format_notification(task, "due_soon")
        assert "[*]" in msg
    def test_reminder(self):
        task = Task(id=3, title="Review PR", priority=Priority.MEDIUM)
        msg = format_notification(task, "reminder")
        assert "[@]" in msg

class TestGetOverdueTasks:
    def test_empty(self):
        assert get_overdue_tasks([]) == []

class TestGetDueSoon:
    def test_empty(self):
        assert get_due_soon([]) == []
