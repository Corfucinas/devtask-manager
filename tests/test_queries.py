"""Tests for saved query management."""
import pytest
from src.queries import SavedQuery, QueryLibrary, execute_query, default_queries


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, title="task", status="todo", priority="medium",
                 tags=None, assignee=None, created_at="2026-01-01T00:00:00+00:00",
                 updated_at="2026-01-02T00:00:00+00:00"):
        self.id = id
        self.title = title
        self.status = FakeStatus(status)
        self.priority = FakePriority(priority)
        self.tags = tags or []
        self.assignee = assignee
        self.created_at = created_at
        self.updated_at = updated_at


@pytest.fixture
def library():
    lib = QueryLibrary()
    lib.save("High Priority", {"priority": "high"}, "created_at", False, "High pri tasks")
    lib.save("My Tasks", {"assignee": "alice"}, "updated_at", True, "Alice's tasks")
    return lib


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "Fix bug", "todo", "high", ["bug"], "alice"),
        FakeTask(2, "Add feature", "in-progress", "medium", ["feature"], "bob"),
        FakeTask(3, "Write docs", "done", "low", ["docs"], "alice"),
        FakeTask(4, "Critical fix", "todo", "critical", ["bug", "urgent"], "charlie"),
    ]


def test_save(library):
    assert library.count() == 2
    q = library.save("New Query", {"status": "done"})
    assert q.id == 3


def test_get(library):
    q = library.get(1)
    assert q is not None
    assert q.name == "High Priority"
    assert library.get(999) is None


def test_find_by_name(library):
    q = library.find_by_name("My Tasks")
    assert q is not None
    assert q.sort_by == "updated_at"


def test_find_by_name_case_insensitive(library):
    assert library.find_by_name("HIGH PRIORITY") is not None


def test_remove(library):
    assert library.remove(1) is True
    assert library.get(1) is None
    assert library.count() == 1
    assert library.remove(999) is False


def test_all_queries(library):
    queries = library.all_queries()
    assert len(queries) == 2


def test_update(library):
    assert library.update(1, description="Updated desc") is True
    assert library.get(1).description == "Updated desc"
    assert library.update(999, description="x") is False


def test_execute_query_status(tasks):
    q = SavedQuery(id=1, name="Done", filters={"status": "done"})
    results = execute_query(q, tasks)
    assert len(results) == 1
    assert results[0].id == 3


def test_execute_query_priority(tasks):
    q = SavedQuery(id=1, name="High", filters={"priority": "high"})
    results = execute_query(q, tasks)
    assert len(results) == 1
    assert results[0].id == 1


def test_execute_query_tags_any(tasks):
    q = SavedQuery(id=1, name="Bugs", filters={"tags": ["bug"], "tag_mode": "any"})
    results = execute_query(q, tasks)
    assert len(results) == 2


def test_execute_query_tags_all(tasks):
    q = SavedQuery(id=1, name="Bug+Urgent", filters={"tags": ["bug", "urgent"], "tag_mode": "all"})
    results = execute_query(q, tasks)
    assert len(results) == 1
    assert results[0].id == 4


def test_execute_query_assignee(tasks):
    q = SavedQuery(id=1, name="Alice", filters={"assignee": "alice"})
    results = execute_query(q, tasks)
    assert len(results) == 2


def test_execute_query_text(tasks):
    q = SavedQuery(id=1, name="Search", filters={"text": "fix"})
    results = execute_query(q, tasks)
    assert len(results) == 2


def test_execute_query_sort(tasks):
    q = SavedQuery(id=1, name="Sorted", filters={}, sort_by="created_at", sort_desc=True)
    results = execute_query(q, tasks)
    assert len(results) == 4


def test_default_queries():
    lib = default_queries()
    assert lib.count() == 6
    assert lib.find_by_name("High Priority") is not None
    assert lib.find_by_name("Bugs") is not None
