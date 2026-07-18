"""Tests for recurring tasks."""
import pytest
from src.models import Task, Priority
from src.recurring import generate_recurring, get_recurring_tag

class TestGenerateRecurring:
    def test_daily(self):
        base = Task(id=1, title="Daily standup", priority=Priority.MEDIUM)
        instances = generate_recurring(base, "daily", count=5)
        assert len(instances) == 5
        assert instances[0].title == "Daily standup (#1)"
    def test_weekly(self):
        base = Task(id=1, title="Weekly review")
        instances = generate_recurring(base, "weekly", count=3)
        assert "weekly" in instances[0].tags
    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Unknown recurrence"):
            generate_recurring(Task(id=1, title="Test"), "hourly")

class TestGetRecurringTag:
    def test_finds_tag(self):
        task = Task(id=1, title="Test", tags=["backend", "daily"])
        assert get_recurring_tag(task) == "daily"
    def test_no_tag(self):
        task = Task(id=1, title="Test", tags=["backend"])
        assert get_recurring_tag(task) is None
