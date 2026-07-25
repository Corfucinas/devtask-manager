"""Tests for webhook management."""
import pytest
from src.webhooks import WebhookRegistry, Webhook, WebhookEvent


@pytest.fixture
def registry():
    r = WebhookRegistry()
    r.register("https://example.com/hook1", ["task.created", "task.completed"])
    r.register("https://example.com/hook2", ["*"])
    r.register("https://example.com/hook3", ["task.updated"])
    return r


def test_register_webhook():
    r = WebhookRegistry()
    hook = r.register("https://example.com/hook", ["task.created"])
    assert hook.id == 1
    assert hook.url == "https://example.com/hook"
    assert hook.events == ["task.created"]
    assert hook.active is True


def test_unregister_webhook(registry):
    assert registry.unregister(1) is True
    assert registry.get(1) is None
    assert registry.unregister(999) is False


def test_get_webhook(registry):
    hook = registry.get(1)
    assert hook is not None
    assert hook.url == "https://example.com/hook1"
    assert registry.get(999) is None


def test_list_webhooks(registry):
    hooks = registry.list_webhooks()
    assert len(hooks) == 3


def test_dispatch_matching(registry):
    events = registry.dispatch("task.created", {"id": 1})
    assert len(events) == 2
    webhook_ids = {e.webhook_id for e in events}
    assert webhook_ids == {1, 2}


def test_dispatch_no_match(registry):
    events = registry.dispatch("issue.opened", {"id": 1})
    assert len(events) == 1
    assert events[0].webhook_id == 2


def test_mark_delivered(registry):
    events = registry.dispatch("task.created", {"id": 1})
    event_id = events[0].id
    assert registry.mark_delivered(event_id) is True
    assert events[0].status == "delivered"
    assert events[0].delivered_at is not None
    assert registry.mark_delivered(999) is False


def test_mark_failed(registry):
    events = registry.dispatch("task.created", {"id": 1})
    event_id = events[0].id
    assert registry.mark_failed(event_id) is True
    assert events[0].status == "failed"
    assert events[0].attempts == 1


def test_event_history(registry):
    registry.dispatch("task.created", {"id": 1})
    registry.dispatch("task.updated", {"id": 2})
    history = registry.event_history()
    assert len(history) >= 2


def test_event_history_filtered(registry):
    registry.dispatch("task.created", {"id": 1})
    history = registry.event_history(webhook_id=1)
    assert all(e.webhook_id == 1 for e in history)


def test_pending_events(registry):
    registry.dispatch("task.created", {"id": 1})
    pending = registry.pending_events()
    assert len(pending) >= 1
    for e in pending:
        registry.mark_delivered(e.id)
    assert len(registry.pending_events()) == 0


def test_webhook_matches():
    hook = Webhook(id=1, url="https://example.com", events=["task.created"])
    assert hook.matches("task.created") is True
    assert hook.matches("task.updated") is False
    hook.active = False
    assert hook.matches("task.created") is False


def test_webhook_wildcard():
    hook = Webhook(id=1, url="https://example.com", events=["*"])
    assert hook.matches("anything") is True
