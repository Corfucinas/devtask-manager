"""Tests for task linker."""
import pytest
from src.task_linker import TaskLink, TaskLinker, LINK_TYPES, link_summary


@pytest.fixture
def linker():
    l = TaskLinker()
    l.link(1, 2, "blocks")
    l.link(1, 3, "relates_to")
    l.link(2, 4, "blocks")
    l.link(3, 4, "duplicates")
    return l


def test_link():
    l = TaskLinker()
    link = l.link(1, 2, "blocks")
    assert link.id == 1
    assert link.source_id == 1
    assert link.target_id == 2
    assert link.link_type == "blocks"


def test_link_duplicate_prevented():
    l = TaskLinker()
    l.link(1, 2, "blocks")
    l.link(1, 2, "blocks")
    assert l.count() == 1


def test_unlink(linker):
    assert linker.unlink(1) is True
    assert linker.get(1) is None
    assert linker.unlink(999) is False


def test_get(linker):
    assert linker.get(1) is not None
    assert linker.get(999) is None


def test_find_exact(linker):
    link = linker.find_exact(1, 2, "blocks")
    assert link is not None
    assert linker.find_exact(1, 2, "relates_to") is None


def test_links_from(linker):
    links = linker.links_from(1)
    assert len(links) == 2


def test_links_to(linker):
    links = linker.links_to(4)
    assert len(links) == 2


def test_find_linked(linker):
    linked = linker.find_linked(1)
    assert 2 in linked
    assert 3 in linked


def test_find_linked_empty():
    l = TaskLinker()
    assert l.find_linked(999) == []


def test_count(linker):
    assert linker.count() == 4


def test_link_count_for(linker):
    assert linker.link_count_for(1) == 2


def test_by_type(linker):
    blocks = linker.by_type("blocks")
    assert len(blocks) == 2


def test_find_chain(linker):
    chain = linker.find_chain(1)
    assert 1 in chain
    assert 2 in chain
    assert 3 in chain
    assert 4 in chain


def test_find_chain_cycle():
    l = TaskLinker()
    l.link(1, 2)
    l.link(2, 3)
    l.link(3, 1)
    chain = l.find_chain(1)
    assert chain == {1, 2, 3}


def test_clear(linker):
    linker.clear()
    assert linker.count() == 0


def test_link_summary(linker):
    summary = link_summary(linker)
    assert summary["total_links"] == 4
    assert "by_type" in summary
    assert summary["by_type"]["blocks"] == 2


def test_reverse_type():
    link = TaskLink(id=1, source_id=1, target_id=2, link_type="blocks")
    assert link.reverse_type == "blocked_by"
