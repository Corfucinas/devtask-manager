"""Tests for event bus."""
import pytest
from src.event_bus import EventBus, Event, Subscription, event_summary


@pytest.fixture
def bus():
    b = EventBus()
    b.subscribe("task.created", lambda e: {"created": True}, priority=10)
    b.subscribe("task.created", lambda e: {"logged": True}, priority=5)
    b.subscribe("task.updated", lambda e: {"updated": True}, priority=1)
    return b


def test_subscribe():
    b = EventBus()
    sub = b.subscribe("test.event", lambda e: None)
    assert sub.id == 1
    assert sub.event_type == "test.event"


def test_unsubscribe(bus):
    assert bus.unsubscribe(1) is True
    assert bus.get(1) is None
    assert bus.unsubscribe(999) is False


def test_publish(bus):
    results = bus.publish("task.created", payload={"id": 1})
    assert len(results) == 2
    assert results[0]["result"]["created"] is True  # higher priority first
    assert results[1]["result"]["logged"] is True


def test_publish_no_subs(bus):
    results = bus.publish("nonexistent", payload=None)
    assert results == []


def test_publish_error_handling(bus):
    bus.subscribe("error.event", lambda e: (_ for _ in ()).throw(ValueError("fail")))
    results = bus.publish("error.event")
    assert results[0]["error"] is not None


def test_get(bus):
    assert bus.get(1) is not None
    assert bus.get(1).event_type == "task.created"
    assert bus.get(999) is None


def test_subscriptions_for(bus):
    subs = bus.subscriptions_for("task.created")
    assert len(subs) == 2


def test_all_subscriptions(bus):
    assert len(bus.all_subscriptions()) == 3


def test_event_types(bus):
    types = bus.event_types()
    assert "task.created" in types
    assert "task.updated" in types


def test_subscription_count(bus):
    assert bus.subscription_count() == 3


def test_history(bus):
    bus.publish("task.created", payload={"id": 1})
    assert len(bus.history()) == 1


def test_clear_history(bus):
    bus.publish("task.created")
    bus.clear_history()
    assert len(bus.history()) == 0


def test_deactivate(bus):
    assert bus.deactivate(1) is True
    results = bus.publish("task.created")
    assert len(results) == 1  # one deactivated


def test_activate(bus):
    bus.deactivate(1)
    bus.activate(1)
    results = bus.publish("task.created")
    assert len(results) == 2


def test_call_count(bus):
    bus.publish("task.created")
    assert bus.get(1).call_count == 1


def test_event_summary(bus):
    summary = event_summary(bus)
    assert summary["total_subscriptions"] == 3
    assert summary["event_types"] == 2
    assert "by_type" in summary
