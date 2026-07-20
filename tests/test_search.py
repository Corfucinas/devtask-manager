"""Tests for search functionality."""

import pytest
from src.storage import TaskStore
from src.search import TaskSearch


@pytest.fixture
def store():
    s = TaskStore()
    s.create(title="Fix login bug", tags=["bug", "auth"], priority="high")
    s.create(title="Add dark mode", tags=["feature", "ui"], priority="medium")
    s.create(title="Update docs", tags=["docs"], priority="low")
    s.create(title="Refactor auth module", tags=["refactor", "auth"], priority="high")
    return s


class TestTaskSearch:
    def test_search_by_query(self, store):
        searcher = TaskSearch(store)
        results = searcher.search(query="auth")
        assert len(results) == 2
        titles = {t.title for t in results}
        assert "Fix login bug" in titles
        assert "Refactor auth module" in titles

    def test_search_by_tag(self, store):
        searcher = TaskSearch(store)
        results = searcher.search(tag="bug")
        assert len(results) == 1
        assert results[0].title == "Fix login bug"

    def test_search_by_priority(self, store):
        searcher = TaskSearch(store)
        results = searcher.search(priority="high")
        assert len(results) == 2

    def test_search_by_status(self, store):
        searcher = TaskSearch(store)
        results = searcher.search(status="todo")
        assert len(results) == 4

    def test_search_combined_filters(self, store):
        searcher = TaskSearch(store)
        results = searcher.search(query="auth", priority="high")
        assert len(results) == 2

    def test_search_no_results(self, store):
        searcher = TaskSearch(store)
        results = searcher.search(query="nonexistent")
        assert len(results) == 0

    def test_search_case_sensitive(self, store):
        searcher = TaskSearch(store)
        results = searcher.search(query="Auth", case_sensitive=True)
        assert len(results) == 0
        results = searcher.search(query="auth", case_sensitive=True)
        assert len(results) == 2
