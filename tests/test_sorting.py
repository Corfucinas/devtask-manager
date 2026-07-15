"""Tests for sorting utilities."""
import pytest
from src.models import Task, Priority
from src.sorting import sort_by_priority, sort_by_created

class TestSortByPriority:
    def test_sort_critical_first(self):
        tasks = [Task(id=1, title="Low", priority=Priority.LOW), Task(id=2, title="Critical", priority=Priority.CRITICAL), Task(id=3, title="Medium", priority=Priority.MEDIUM)]
        s = sort_by_priority(tasks)
        assert s[0].title == "Critical"
        assert s[2].title == "Low"

    def test_empty_list(self):
        assert sort_by_priority([]) == []

class TestSortByCreated:
    def test_newest_first(self):
        t1 = Task(id=1, title="Old", created_at="2026-01-01T00:00:00+00:00")
        t2 = Task(id=2, title="New", created_at="2026-06-01T00:00:00+00:00")
        r = sort_by_created([t1, t2])
        assert r[0].title == "New"
