"""Tests for keyboard shortcuts."""
import pytest
from src.shortcuts import (
    Shortcut, ShortcutMap, default_shortcuts, merge_maps, conflicts,
)


@pytest.fixture
def sm():
    s = ShortcutMap()
    s.bind("n", "new_task", "Create new", "task_list")
    s.bind("s", "search", "Search", "global")
    s.bind("q", "quit", "Quit", "global")
    return s


def test_bind(sm):
    assert sm.has_key("n")
    assert sm.lookup("n").action == "new_task"


def test_unbind(sm):
    assert sm.unbind("n") is True
    assert not sm.has_key("n")
    assert sm.unbind("n") is False


def test_lookup_missing(sm):
    assert sm.lookup("z") is None


def test_action_for_key(sm):
    assert sm.action_for_key("s") == "search"
    assert sm.action_for_key("z") is None


def test_keys_for_action(sm):
    sm.bind("S", "search", "Search (shift)", "global")
    keys = sm.keys_for_action("search")
    assert "s" in keys
    assert "S" in keys


def test_all_bindings(sm):
    bindings = sm.all_bindings()
    assert len(bindings) == 3


def test_by_context(sm):
    task_list = sm.by_context("task_list")
    assert len(task_list) == 1
    global_keys = sm.by_context("global")
    assert len(global_keys) == 2


def test_rebind(sm):
    assert sm.rebind("n", "N") is True
    assert sm.has_key("N")
    assert not sm.has_key("n")
    assert sm.lookup("N").action == "new_task"


def test_rebind_target_exists(sm):
    assert sm.rebind("n", "s") is False


def test_rebind_source_missing(sm):
    assert sm.rebind("z", "y") is False


def test_count(sm):
    assert sm.count() == 3


def test_default_shortcuts():
    sm = default_shortcuts()
    assert sm.count() == 12
    assert sm.action_for_key("n") == "new_task"
    assert sm.action_for_key("q") == "quit"
    assert sm.action_for_key("?") == "help"


def test_merge_maps():
    m1 = ShortcutMap()
    m1.bind("a", "action_a", "A")
    m2 = ShortcutMap()
    m2.bind("b", "action_b", "B")
    merged = merge_maps(m1, m2)
    assert merged.count() == 2
    assert merged.has_key("a")
    assert merged.has_key("b")


def test_merge_override():
    m1 = ShortcutMap()
    m1.bind("a", "action_a", "Original")
    m2 = ShortcutMap()
    m2.bind("a", "action_b", "Override")
    merged = merge_maps(m1, m2)
    assert merged.action_for_key("a") == "action_b"


def test_conflicts():
    m1 = ShortcutMap()
    m1.bind("a", "action_a")
    m1.bind("b", "action_b")
    m2 = ShortcutMap()
    m2.bind("b", "action_x")
    m2.bind("c", "action_c")
    c = conflicts(m1, m2)
    assert c == ["b"]
