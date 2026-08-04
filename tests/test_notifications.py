"""Tests for notification center."""
import pytest
from src.notifications import (
    Notification, NotificationCenter, NotificationPreferences,
    dispatch_notification, notification_summary,
)


@pytest.fixture
def center():
    c = NotificationCenter()
    c.create("task_assigned", "New Task", "You have been assigned a task", "high", "alice")
    c.create("task_due", "Due Soon", "Task due in 1 hour", "urgent", "alice")
    c.create("system", "Welcome", "Welcome to DevTask", "low", "bob")
    return c


def test_create():
    c = NotificationCenter()
    n = c.create("task_assigned", "Title", "Message", "high", "alice")
    assert n.id == 1
    assert n.notification_type == "task_assigned"
    assert n.read is False


def test_get(center):
    assert center.get(1) is not None
    assert center.get(1).title == "New Task"
    assert center.get(999) is None


def test_mark_read(center):
    assert center.mark_read(1) is True
    assert center.get(1).read is True
    assert center.mark_read(999) is False


def test_mark_all_read(center):
    count = center.mark_all_read("alice")
    assert count == 2
    assert center.unread_count("alice") == 0
    assert center.unread_count("bob") == 1


def test_unread(center):
    assert len(center.unread()) == 3
    assert len(center.unread("alice")) == 2


def test_all_notifications(center):
    assert len(center.all_notifications()) == 3
    assert len(center.all_notifications("alice")) == 2


def test_by_type(center):
    assert len(center.by_type("task_assigned")) == 1


def test_by_priority(center):
    assert len(center.by_priority("urgent")) == 1


def test_recent(center):
    assert len(center.recent(limit=2)) == 2


def test_count(center):
    assert center.count() == 3


def test_unread_count(center):
    assert center.unread_count() == 3
    center.mark_read(1)
    assert center.unread_count() == 2


def test_clear(center):
    center.clear("alice")
    assert len(center.all_notifications("alice")) == 0
    assert center.count() == 1


def test_clear_all(center):
    center.clear()
    assert center.count() == 0


def test_clear_read(center):
    center.mark_read(1)
    center.mark_read(2)
    removed = center.clear_read()
    assert removed == 2
    assert center.count() == 1


def test_notification_preferences():
    prefs = NotificationPreferences(user="alice")
    assert prefs.channel_enabled("email") is True
    assert prefs.channel_enabled("mobile") is False


def test_preferences_is_muted():
    prefs = NotificationPreferences(user="alice", muted_types=["system"])
    assert prefs.is_muted("system") is True
    assert prefs.is_muted("task_assigned") is False


def test_preferences_should_deliver():
    prefs = NotificationPreferences(user="alice", min_priority="high")
    high_notif = Notification(id=1, notification_type="task", title="t", message="m", priority="high")
    low_notif = Notification(id=2, notification_type="task", title="t", message="m", priority="low")
    assert prefs.should_deliver(high_notif) is True
    assert prefs.should_deliver(low_notif) is False


def test_dispatch_notification():
    c = NotificationCenter()
    n = c.create("task_assigned", "Title", "Msg", "high", "alice")
    result = dispatch_notification(c, n)
    assert result["delivered"] is True
    assert "web" in result["channels"]


def test_dispatch_with_preferences():
    c = NotificationCenter()
    n = c.create("system", "Title", "Msg", "low", "alice")
    prefs = NotificationPreferences(user="alice", min_priority="high")
    result = dispatch_notification(c, n, prefs)
    assert result["delivered"] is False


def test_notification_summary(center):
    summary = notification_summary(center)
    assert summary["total"] == 3
    assert summary["unread"] == 3
    assert "task_assigned" in summary["by_type"]
