"""Tests for sprint retrospective."""
import pytest
from src.retro import (
    Retro, ActionItem, add_action_item, resolve_item,
    unresolved_items, items_by_owner, items_by_category,
    retro_summary, add_participant,
)


@pytest.fixture
def retro():
    r = Retro(id=1, sprint_id=5)
    add_participant(r, "alice")
    add_participant(r, "bob")
    add_action_item(r, "Improve code review process", "alice", "process")
    add_action_item(r, "Fix CI pipeline", "bob", "technical")
    add_action_item(r, "Better sprint planning", "alice", "planning")
    return r


def test_retro_creation():
    r = Retro(id=1, sprint_id=5)
    assert r.id == 1
    assert r.sprint_id == 5
    assert len(r.items) == 0
    assert r.date != ""


def test_add_action_item(retro):
    item = add_action_item(retro, "New item", "charlie")
    assert item.id == 4
    assert item.text == "New item"
    assert item.owner == "charlie"
    assert item.resolved is False


def test_resolve_item(retro):
    assert resolve_item(retro, 1) is True
    assert retro.items[0].resolved is True
    assert retro.items[0].resolved_at is not None
    assert resolve_item(retro, 999) is False


def test_unresolved_items(retro):
    resolve_item(retro, 1)
    unresolved = unresolved_items(retro)
    assert len(unresolved) == 2
    ids = {i.id for i in unresolved}
    assert ids == {2, 3}


def test_items_by_owner(retro):
    alice_items = items_by_owner(retro, "alice")
    assert len(alice_items) == 2
    bob_items = items_by_owner(retro, "bob")
    assert len(bob_items) == 1


def test_items_by_category(retro):
    process_items = items_by_category(retro, "process")
    assert len(process_items) == 1
    assert process_items[0].text == "Improve code review process"


def test_retro_summary(retro):
    resolve_item(retro, 1)
    summary = retro_summary(retro)
    assert summary["retro_id"] == 1
    assert summary["sprint_id"] == 5
    assert summary["participants"] == 2
    assert summary["total_items"] == 3
    assert summary["resolved"] == 1
    assert summary["unresolved"] == 2
    assert summary["resolution_rate"] == pytest.approx(33.3, abs=0.1)


def test_retro_summary_empty():
    r = Retro(id=1, sprint_id=1)
    summary = retro_summary(r)
    assert summary["total_items"] == 0
    assert summary["resolution_rate"] == 0.0


def test_add_participant_no_duplicate(retro):
    add_participant(retro, "alice")
    assert retro.participants.count("alice") == 1
    add_participant(retro, "charlie")
    assert "charlie" in retro.participants
    assert len(retro.participants) == 3
