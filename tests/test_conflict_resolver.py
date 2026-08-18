"""Tests for conflict resolution."""
import pytest
from src.conflict_resolver import (
    Conflict, detect_conflicts, resolve_conflict,
    ConflictResolver, auto_resolve, conflict_summary,
)


class FakeStatus:
    def __init__(self, value): self.value = value
class FakePriority:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id=1, title="Task", description="Desc", priority="medium",
                 status="todo", tags=None, assignee=None, due_date=None):
        self.id = id
        self.title = title
        self.description = description
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        self.assignee = assignee
        self.due_date = due_date


@pytest.fixture
def three_versions():
    base = FakeTask(1, title="Original", priority="medium")
    ours = FakeTask(1, title="Our Version", priority="high")
    theirs = FakeTask(1, title="Their Version", priority="low")
    return base, ours, theirs


def test_conflict_resolve_ours():
    c = Conflict(field="title", base_value="A", our_value="B", their_value="C")
    result = c.resolve("ours")
    assert result == "B"
    assert c.resolved is True


def test_conflict_resolve_theirs():
    c = Conflict(field="title", base_value="A", our_value="B", their_value="C")
    assert c.resolve("theirs") == "C"


def test_conflict_resolve_base():
    c = Conflict(field="title", base_value="A", our_value="B", their_value="C")
    assert c.resolve("base") == "A"


def test_conflict_resolve_merge():
    c = Conflict(field="tags", base_value=["a"], our_value=["a", "b"], their_value=["a", "c"])
    result = c.resolve("merge")
    assert set(result) == {"a", "b", "c"}


def test_detect_conflicts(three_versions):
    base, ours, theirs = three_versions
    conflicts = detect_conflicts(base, ours, theirs)
    fields = [c.field for c in conflicts]
    assert "title" in fields
    assert "priority" in fields


def test_detect_conflicts_none():
    base = FakeTask(1, title="Same")
    ours = FakeTask(1, title="Same")
    theirs = FakeTask(1, title="Same")
    assert detect_conflicts(base, ours, theirs) == []


def test_detect_conflicts_one_sided():
    base = FakeTask(1, title="Original")
    ours = FakeTask(1, title="Changed")
    theirs = FakeTask(1, title="Original")
    conflicts = detect_conflicts(base, ours, theirs)
    assert len(conflicts) == 0  # only one side changed, no conflict


def test_conflict_resolver_add():
    r = ConflictResolver()
    c = Conflict(field="x", base_value=1, our_value=2, their_value=3)
    r.add_conflict(c)
    assert r.count() == 1


def test_conflict_resolver_resolve_all():
    r = ConflictResolver(default_strategy="ours")
    r.add_conflict(Conflict(field="a", base_value=1, our_value=2, their_value=3))
    r.add_conflict(Conflict(field="b", base_value="x", our_value="y", their_value="z"))
    results = r.resolve_all()
    assert results["a"] == 2
    assert results["b"] == "y"
    assert r.is_fully_resolved() is True


def test_conflict_resolver_resolve_field():
    r = ConflictResolver()
    r.add_conflict(Conflict(field="a", base_value=1, our_value=2, their_value=3))
    result = r.resolve_field("a", strategy="theirs")
    assert result == 3


def test_conflict_resolver_unresolved():
    r = ConflictResolver()
    r.add_conflict(Conflict(field="a", base_value=1, our_value=2, their_value=3))
    assert r.unresolved_count() == 1
    r.resolve_all()
    assert r.unresolved_count() == 0


def test_auto_resolve(three_versions):
    base, ours, theirs = three_versions
    result = auto_resolve(base, ours, theirs, strategy="ours")
    assert result["conflict_count"] > 0
    assert result["unresolved"] == 0


def test_conflict_summary():
    conflicts = [
        Conflict(field="a", base_value=1, our_value=2, their_value=3),
        Conflict(field="b", base_value="x", our_value="y", their_value="z"),
    ]
    conflicts[0].resolve("ours")
    summary = conflict_summary(conflicts)
    assert summary["total"] == 2
    assert summary["resolved"] == 1
    assert summary["unresolved"] == 1
