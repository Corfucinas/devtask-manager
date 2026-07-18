"""Tests for tag management."""
import pytest
from src.models import Task, Priority
from src.tags import get_all_tags, count_tags, filter_by_tag, tag_stats

class TestGetAllTags:
    def test_unique(self):
        tasks = [Task(id=1, title="A", tags=["backend", "api"]), Task(id=2, title="B", tags=["backend", "frontend"])]
        assert get_all_tags(tasks) == ["api", "backend", "frontend"]
    def test_empty(self):
        assert get_all_tags([Task(id=1, title="A")]) == []

class TestCountTags:
    def test_counts(self):
        tasks = [Task(id=1, title="A", tags=["backend"]), Task(id=2, title="B", tags=["backend", "api"])]
        counts = count_tags(tasks)
        assert counts["backend"] == 2
        assert counts["api"] == 1

class TestFilterByTag:
    def test_filters(self):
        tasks = [Task(id=1, title="A", tags=["backend"]), Task(id=2, title="B", tags=["frontend"])]
        result = filter_by_tag(tasks, "backend")
        assert len(result) == 1

class TestTagStats:
    def test_stats(self):
        tasks = [Task(id=1, title="A", tags=["backend", "api"]), Task(id=2, title="B"), Task(id=3, title="C", tags=["backend"])]
        stats = tag_stats(tasks)
        assert stats["total_tags"] == 2
        assert stats["tagged_tasks"] == 2
        assert stats["untagged_tasks"] == 1
