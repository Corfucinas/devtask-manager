"""Tests for lifecycle hooks."""
import pytest
from src.hooks import Hook, HookManager, default_hooks, hook_summary


class FakeTask:
    def __init__(self, id=1, assignee=None, updated_at=None):
        self.id = id
        self.assignee = assignee
        self.updated_at = updated_at


@pytest.fixture
def manager():
    m = HookManager()
    m.register("task.created", lambda t, c: {"created": True}, priority=10)
    m.register("task.created", lambda t, c: {"logged": True}, priority=5)
    m.register("task.assigned", lambda t, c: {"assigned": True}, priority=3)
    return m


def test_register():
    m = HookManager()
    h = m.register("test.event", lambda t, c: None)
    assert h.id == 1
    assert h.event == "test.event"
    assert h.enabled is True


def test_unregister(manager):
    assert manager.unregister(1) is True
    assert manager.get(1) is None


def test_get(manager):
    assert manager.get(1) is not None
    assert manager.get(1).event == "task.created"
    assert manager.get(999) is None


def test_hooks_for_event(manager):
    hooks = manager.hooks_for_event("task.created")
    assert len(hooks) == 2
    assert hooks[0].priority >= hooks[1].priority


def test_fire_hooks(manager):
    task = FakeTask(1)
    results = manager.fire_hooks("task.created", task)
    assert len(results) == 2
    assert results[0]["fired"] is True


def test_fire_hooks_empty(manager):
    task = FakeTask(1)
    assert manager.fire_hooks("nonexistent", task) == []


def test_enable_disable(manager):
    assert manager.disable(1) is True
    assert manager.get(1).enabled is False
    hooks = manager.hooks_for_event("task.created")
    assert len(hooks) == 1
    assert manager.enable(1) is True
    assert len(manager.hooks_for_event("task.created")) == 2


def test_priority_order(manager):
    hooks = manager.hooks_for_event("task.created")
    assert hooks[0].priority == 10
    assert hooks[1].priority == 5


def test_count(manager):
    assert manager.count() == 3


def test_events(manager):
    events = manager.events()
    assert "task.created" in events
    assert "task.assigned" in events


def test_hook_count_for(manager):
    assert manager.hook_count_for("task.created") == 2
    assert manager.hook_count_for("task.assigned") == 1


def test_clear(manager):
    manager.clear()
    assert manager.count() == 0


def test_fire_count_increments(manager):
    task = FakeTask(1)
    manager.fire_hooks("task.created", task)
    assert manager.get(1).fired_count == 1


def test_default_hooks():
    m = default_hooks()
    assert m.count() == 3
    assert m.hook_count_for("task.created") == 1


def test_default_hooks_fire():
    m = default_hooks()
    task = FakeTask(1, assignee="alice")
    results = m.fire_hooks("task.assigned", task)
    assert len(results) == 1
    assert results[0]["result"]["assignee"] == "alice"


def test_hook_summary(manager):
    summary = hook_summary(manager)
    assert summary["total_hooks"] == 3
    assert summary["event_count"] == 2


def test_hook_error_handling():
    m = HookManager()
    def failing_hook(task, context):
        raise ValueError("hook failed")
    m.register("test.event", failing_hook)
    task = FakeTask(1)
    results = m.fire_hooks("test.event", task)
    assert "error" in results[0]["result"]
