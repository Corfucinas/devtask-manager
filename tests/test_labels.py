"""Tests for label management."""
import pytest
from src.labels import Label, LabelRegistry, apply_label, filter_by_label, default_registry


class FakeTask:
    def __init__(self):
        self.labels = None


def test_label_is_frozen():
    label = Label("bug", "#d73a4a", "type")
    assert label.name == "bug"
    with pytest.raises(Exception):
        label.name = "feature"


def test_registry_register_and_get():
    registry = LabelRegistry()
    label = Label("bug", "#d73a4a", "type")
    registry.register(label)
    assert registry.get("bug") == label


def test_registry_get_missing():
    registry = LabelRegistry()
    assert registry.get("nonexistent") is None


def test_registry_list_sorted():
    registry = LabelRegistry()
    registry.register(Label("zebra", "#000000"))
    registry.register(Label("alpha", "#ffffff"))
    labels = registry.list_labels()
    assert [l.name for l in labels] == ["alpha", "zebra"]


def test_registry_by_category():
    registry = LabelRegistry()
    registry.register(Label("bug", "#d73a4a", "type"))
    registry.register(Label("urgent", "#e99695", "priority"))
    types = registry.by_category("type")
    assert len(types) == 1
    assert types[0].name == "bug"


def test_registry_remove():
    registry = LabelRegistry()
    registry.register(Label("bug", "#d73a4a"))
    assert registry.remove("bug") is True
    assert registry.get("bug") is None
    assert registry.remove("bug") is False


def test_apply_label():
    task = FakeTask()
    label = Label("bug", "#d73a4a")
    apply_label(task, label)
    assert len(task.labels) == 1
    assert task.labels[0].name == "bug"


def test_apply_label_no_duplicate():
    task = FakeTask()
    label = Label("bug", "#d73a4a")
    apply_label(task, label)
    apply_label(task, label)
    assert len(task.labels) == 1


def test_filter_by_label():
    task1 = FakeTask()
    task2 = FakeTask()
    apply_label(task1, Label("bug", "#d73a4a"))
    apply_label(task2, Label("feature", "#a2eeef"))
    results = filter_by_label([task1, task2], "bug")
    assert len(results) == 1
    assert results[0] == task1


def test_default_registry():
    registry = default_registry()
    assert registry.get("bug") is not None
    assert registry.get("feature") is not None
    assert registry.get("urgent") is not None
    assert len(registry.list_labels()) == 6
