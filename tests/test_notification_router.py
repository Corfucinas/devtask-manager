"""Tests for notification router."""
import pytest
from src.notification_router import (
    NotificationChannel, NotificationRouter, RouteResult,
    routing_report, default_router,
)


class FakeNotification:
    def __init__(self, id=1, title="Test", message="msg", priority="normal"):
        self.id = id
        self.title = title
        self.message = message
        self.priority = priority


@pytest.fixture
def router():
    r = NotificationRouter()
    r.add_channel("in_app", "in_app", priority_levels=["urgent"])
    r.add_channel("email", "email", priority_levels=["normal", "high", "urgent"])
    r.add_channel("slack", "slack", priority_levels=["high", "urgent"], enabled=False)
    return r


def test_add_channel():
    r = NotificationRouter()
    ch = r.add_channel("test", "email")
    assert ch.name == "test"
    assert ch.channel_type == "email"


def test_remove_channel(router):
    assert router.remove_channel("in_app") is True
    assert router.get_channel("in_app") is None
    assert router.remove_channel("nonexistent") is False


def test_get_channel(router):
    assert router.get_channel("email") is not None
    assert router.get_channel("nonexistent") is None


def test_all_channels(router):
    assert len(router.all_channels()) == 3


def test_enabled_channels(router):
    assert len(router.enabled_channels()) == 2


def test_channel_count(router):
    assert router.channel_count() == 3


def test_matches_priority(router):
    ch = router.get_channel("email")
    assert router.matches_priority(ch, "high") is True
    assert router.matches_priority(ch, "low") is False


def test_route_in_app_only_urgent(router):
    notif = FakeNotification(priority="urgent")
    results = router.route(notif)
    assert len(results) == 1
    assert results[0].channel_name == "in_app"


def test_route_normal(router):
    notif = FakeNotification(priority="normal")
    results = router.route(notif)
    assert len(results) == 1  # only email
    assert results[0].channel_name == "email"


def test_route_no_channel(router):
    notif = FakeNotification(priority="low")
    results = router.route(notif)
    assert len(results) == 0


def test_route_to_channel(router):
    notif = FakeNotification(priority="high")
    result = router.route_to_channel(notif, "email")
    assert result is not None
    assert result.delivered is True


def test_route_to_invalid_channel(router):
    notif = FakeNotification(priority="high")
    result = router.route_to_channel(notif, "nonexistent")
    assert result is None


def test_route_to_disabled_channel(router):
    notif = FakeNotification(priority="high")
    result = router.route_to_channel(notif, "slack")
    assert result is None


def test_results(router):
    notif = FakeNotification(priority="high")
    router.route(notif)
    assert len(router.results()) == 2


def test_delivered_failed_counts(router):
    router.route(FakeNotification(priority="high"))
    assert router.delivered_count() == 2
    assert router.failed_count() == 0


def test_clear_results(router):
    router.route(FakeNotification(priority="high"))
    router.clear_results()
    assert len(router.results()) == 0


def test_routing_report(router):
    router.route(FakeNotification(priority="high"))
    report = routing_report(router)
    assert report["total_channels"] == 3
    assert report["delivered"] == 2
    assert "by_channel" in report


def test_default_router():
    r = default_router()
    assert r.channel_count() == 3
    assert r.get_channel("in_app") is not None
    assert r.get_channel("email") is not None
