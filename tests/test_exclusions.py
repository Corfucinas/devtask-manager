"""Tests for task exclusion filters."""
import pytest
from src.exclusions import (
    ExclusionFilter, ExclusionRule, ExclusionEngine,
    default_exclusions, exclusion_summary,
)


class FakeStatus:
    def __init__(self, value): self.value = value
class FakePriority:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, status="todo", priority="medium", tags=None):
        self.id = id
        self.status = FakeStatus(status)
        self.priority = FakePriority(priority)
        self.tags = tags or []


@pytest.fixture
def engine():
    e = ExclusionEngine()
    e.add_rule("Done tasks", [ExclusionFilter(id=0, field="status", operator="eq", value="done")])
    e.add_rule("Archived", [ExclusionFilter(id=0, field="tags", operator="contains", value="archived")])
    return e


@pytest.fixture
def tasks():
    return [FakeTask(1, "todo", "high", ["bug"]), FakeTask(2, "done", "medium", ["archived"]),
            FakeTask(3, "done", "low", ["docs"]), FakeTask(4, "in-progress", "critical", ["bug"])]


def test_exclusion_filter_eq():
    f = ExclusionFilter(id=1, field="status", operator="eq", value="done")
    assert f.matches(FakeTask(1, "done")) is True
    assert f.matches(FakeTask(2, "todo")) is False


def test_exclusion_filter_contains():
    f = ExclusionFilter(id=1, field="tags", operator="contains", value="bug")
    assert f.matches(FakeTask(1, tags=["bug"])) is True
    assert f.matches(FakeTask(2, tags=["docs"])) is False


def test_exclusion_filter_ne():
    f = ExclusionFilter(id=1, field="status", operator="ne", value="done")
    assert f.matches(FakeTask(1, "todo")) is True
    assert f.matches(FakeTask(2, "done")) is False


def test_exclusion_rule_match_all():
    rule = ExclusionRule(id=1, name="test", match_all=True, filters=[
        ExclusionFilter(id=0, field="status", operator="eq", value="done"),
        ExclusionFilter(id=0, field="tags", operator="contains", value="archived"),
    ])
    assert rule.matches(FakeTask(1, "done", tags=["archived"])) is True
    assert rule.matches(FakeTask(2, "done", tags=["bug"])) is False


def test_exclusion_rule_match_any():
    rule = ExclusionRule(id=1, name="test", match_all=False, filters=[
        ExclusionFilter(id=0, field="status", operator="eq", value="done"),
        ExclusionFilter(id=0, field="tags", operator="contains", value="archived"),
    ])
    assert rule.matches(FakeTask(1, "done")) is True
    assert rule.matches(FakeTask(2, "todo", tags=["archived"])) is True


def test_engine_add_rule():
    e = ExclusionEngine()
    r = e.add_rule("test", [ExclusionFilter(id=0, field="status", operator="eq", value="done")])
    assert r.id == 1


def test_engine_remove(engine):
    assert engine.remove_rule(1) is True
    assert engine.get(1) is None


def test_engine_count(engine):
    assert engine.count() == 2


def test_engine_should_exclude(engine, tasks):
    assert engine.should_exclude(tasks[1]) is True  # done + archived
    assert engine.should_exclude(tasks[2]) is True  # done
    assert engine.should_exclude(tasks[0]) is False


def test_engine_apply(engine, tasks):
    included = engine.apply(tasks)
    assert len(included) == 2  # todo + in-progress
    assert {t.id for t in included} == {1, 4}


def test_engine_excluded(engine, tasks):
    excluded = engine.excluded(tasks)
    assert len(excluded) == 2


def test_default_exclusions():
    e = default_exclusions()
    assert e.count() == 2


def test_exclusion_summary(engine, tasks):
    s = exclusion_summary(engine, tasks)
    assert s["total"] == 4
    assert s["included"] == 2
    assert s["excluded"] == 2
