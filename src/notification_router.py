"""Notification router with channel routing."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class NotificationChannel:
    """A delivery channel for notifications."""
    name: str
    channel_type: str  # email, slack, webhook, in_app, sms
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority_levels: List[str] = field(default_factory=lambda: ["low", "normal", "high", "urgent"])

    def accepts_priority(self, priority: str) -> bool:
        return priority in self.priority_levels


@dataclass
class RouteResult:
    """Result of routing a notification."""
    channel_name: str
    delivered: bool
    error: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class NotificationRouter:
    """Routes notifications to appropriate channels."""
    def __init__(self):
        self._channels: Dict[str, NotificationChannel] = {}
        self._results: List[RouteResult] = []

    def add_channel(self, name, channel_type, config=None, priority_levels=None, enabled=True):
        """Register a notification channel."""
        channel = NotificationChannel(
            name=name, channel_type=channel_type, config=config or {},
            priority_levels=priority_levels or ["low", "normal", "high", "urgent"],
            enabled=enabled)
        self._channels[name] = channel
        return channel

    def remove_channel(self, name) -> bool:
        if name in self._channels:
            del self._channels[name]
            return True
        return False

    def get_channel(self, name):
        return self._channels.get(name)

    def all_channels(self):
        return list(self._channels.values())

    def enabled_channels(self):
        return [c for c in self._channels.values() if c.enabled]

    def channel_count(self):
        return len(self._channels)

    def matches_priority(self, channel, priority):
        """Check if a channel accepts a priority level."""
        return channel.enabled and channel.accepts_priority(priority)

    def route(self, notification, preferences=None):
        """Route a notification to all matching channels."""
        if preferences and not preferences.should_deliver(notification):
            return []
        priority = getattr(notification, "priority", "normal")
        results = []
        for channel in self.enabled_channels():
            if not channel.accepts_priority(priority):
                continue
            try:
                # Simulate delivery
                result = RouteResult(channel_name=channel.name, delivered=True)
                results.append(result)
                self._results.append(result)
            except Exception as e:
                result = RouteResult(channel_name=channel.name, delivered=False, error=str(e))
                results.append(result)
                self._results.append(result)
        return results

    def route_to_channel(self, notification, channel_name):
        """Route to a specific channel."""
        channel = self._channels.get(channel_name)
        if not channel or not channel.enabled:
            return None
        if not channel.accepts_priority(getattr(notification, "priority", "normal")):
            return None
        result = RouteResult(channel_name=channel_name, delivered=True)
        self._results.append(result)
        return result

    def results(self):
        return list(self._results)

    def delivered_count(self):
        return sum(1 for r in self._results if r.delivered)

    def failed_count(self):
        return sum(1 for r in self._results if not r.delivered)

    def clear_results(self):
        self._results = []


def routing_report(router):
    """Generate routing statistics."""
    results = router.results()
    return {
        "total_channels": router.channel_count(),
        "enabled_channels": len(router.enabled_channels()),
        "total_deliveries": len(results),
        "delivered": router.delivered_count(),
        "failed": router.failed_count(),
        "delivery_rate": round(router.delivered_count() / max(len(results), 1) * 100, 1),
        "by_channel": {
            c: {
                "delivered": sum(1 for r in results if r.channel_name == c and r.delivered),
                "failed": sum(1 for r in results if r.channel_name == c and not r.delivered),
            }
            for c in {r.channel_name for r in results}
        },
    }


def default_router():
    """Create a router with default channels."""
    r = NotificationRouter()
    r.add_channel("in_app", "in_app", {"show_banner": True})
    r.add_channel("email", "email", priority_levels=["normal", "high", "urgent"])
    r.add_channel("slack", "slack", {"channel": "#tasks"}, priority_levels=["high", "urgent"])
    return r
