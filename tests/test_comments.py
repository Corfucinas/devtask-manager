"""Tests for threaded comments."""
import pytest
from src.comments import (
    add_comment, edit_comment, delete_comment, get_comments,
    comment_thread, flatten_comments, reply_count,
    top_level_comments, comments_by_author, comment_count, build_tree,
)


class FakeTask:
    def __init__(self):
        self.comments = None


@pytest.fixture
def task():
    t = FakeTask()
    add_comment(t, "alice", "First comment")
    add_comment(t, "bob", "Reply to first", parent_id=1)
    add_comment(t, "charlie", "Another reply", parent_id=1)
    add_comment(t, "alice", "Second top-level")
    return t


def test_add_comment():
    t = FakeTask()
    c = add_comment(t, "alice", "Hello")
    assert c.id == 1
    assert c.author == "alice"
    assert c.text == "Hello"
    assert c.parent_id is None


def test_add_reply(task):
    c = add_comment(task, "bob", "Deep reply", parent_id=2)
    assert c.id == 5
    assert c.parent_id == 2


def test_edit_comment(task):
    assert edit_comment(task, 1, "Edited text") is True
    assert task.comments[0].text == "Edited text"
    assert task.comments[0].edited is True
    assert task.comments[0].edited_at is not None
    assert edit_comment(task, 999, "x") is False


def test_delete_comment_cascading(task):
    assert delete_comment(task, 1) is True
    remaining = get_comments(task)
    ids = {c.id for c in remaining}
    assert 1 not in ids
    assert 2 not in ids
    assert 3 not in ids
    assert 4 in ids


def test_delete_comment_no_replies():
    t = FakeTask()
    add_comment(t, "alice", "Solo")
    assert delete_comment(t, 1) is True
    assert get_comments(t) == []


def test_delete_nonexistent(task):
    assert delete_comment(task, 999) is False


def test_comment_thread(task):
    thread = comment_thread(task, 1)
    ids = {c.id for c in thread}
    assert 1 in ids
    assert 2 in ids
    assert 3 in ids
    assert 4 not in ids


def test_flatten_comments(task):
    flat = flatten_comments(task)
    assert len(flat) == 4


def test_reply_count(task):
    assert reply_count(task, 1) == 2
    assert reply_count(task, 4) == 0


def test_top_level_comments(task):
    top = top_level_comments(task)
    assert len(top) == 2
    assert {c.id for c in top} == {1, 4}


def test_comments_by_author(task):
    alice = comments_by_author(task, "alice")
    assert len(alice) == 2
    assert all(c.author == "alice" for c in alice)


def test_comment_count(task):
    assert comment_count(task) == 4


def test_build_tree(task):
    tree = build_tree(task)
    assert len(tree) == 2
    root1 = next(n for n in tree if n["comment"].id == 1)
    assert len(root1["replies"]) == 2
