"""Tests for @mention parsing."""
import pytest
from src.mention import (
    parse_mentions, extract_mentions_from_task, unique_users,
    route_mentions, mention_count, is_mentioned, mention_summary,
    replace_mentions, Mention,
)


class FakeComment:
    def __init__(self, text):
        self.text = text


class FakeTask:
    def __init__(self, id=1, title="", description="", comments=None):
        self.id = id
        self.title = title
        self.description = description
        self.comments = comments or []


def test_parse_mentions_basic():
    mentions = parse_mentions("Hello @alice and @bob")
    assert len(mentions) == 2
    assert mentions[0].user == "alice"


def test_parse_mentions_empty():
    assert parse_mentions("") == []
    assert parse_mentions("No mentions here") == []


def test_parse_mentions_position():
    mentions = parse_mentions("Hi @alice")
    assert mentions[0].position == 3


def test_parse_mentions_context():
    mentions = parse_mentions("Hello @alice how are you doing today")
    assert "@alice" in mentions[0].context


def test_extract_mentions_from_task():
    task = FakeTask(1, title="Review @alice", description="cc @bob",
                    comments=[FakeComment("Thanks @charlie")])
    mentions = extract_mentions_from_task(task)
    assert len(mentions) == 3
    users = {m.user for m in mentions}
    assert users == {"alice", "bob", "charlie"}


def test_unique_users():
    mentions = [Mention(user="alice", field="title", position=0),
                Mention(user="alice", field="desc", position=5),
                Mention(user="bob", field="title", position=10)]
    assert unique_users(mentions) == ["alice", "bob"]


def test_route_mentions():
    task = FakeTask(1, title="@alice @bob")
    mentions = extract_mentions_from_task(task)
    results = route_mentions(mentions, task)
    assert len(results) == 2
    assert results[0]["user"] == "alice"


def test_route_mentions_with_notifications():
    from src.notifications import NotificationCenter
    center = NotificationCenter()
    task = FakeTask(1, title="@alice please review")
    mentions = extract_mentions_from_task(task)
    results = route_mentions(mentions, task, center)
    assert results[0]["notified"] is True
    assert center.count() == 1


def test_mention_count():
    task = FakeTask(1, title="@alice", description="@bob @charlie")
    assert mention_count(task) == 3


def test_is_mentioned():
    task = FakeTask(1, title="@alice")
    assert is_mentioned(task, "alice") is True
    assert is_mentioned(task, "bob") is False


def test_mention_summary():
    tasks = [FakeTask(1, title="@alice @bob"), FakeTask(2, description="@alice"),
             FakeTask(3, title="No mentions")]
    summary = mention_summary(tasks)
    assert summary["total_mentions"] == 3
    assert summary["unique_users"] == 2
    assert summary["tasks_with_mentions"] == 2


def test_replace_mentions():
    assert replace_mentions("Hi @alice", {"alice": "@bob"}) == "Hi @bob"


def test_replace_mentions_no_match():
    assert replace_mentions("Hi @alice", {"bob": "@charlie"}) == "Hi @alice"
