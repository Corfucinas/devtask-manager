"""Notification center and preferences."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Notification:
    """A single notification event."""
    id: int
    notification_type: str
    title: str
    message: str
    priority: str = "normal"
    read: bool = False
    created_at: str = ""
    target_user: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class NotificationCenter:
    """Collects and manages notifications."""

    def __init__(self):
        self._notifications: List[Notification] = []
        self._next_id = 1

    def create(self, notification_type, title, message, priority="normal",
               target_user=None, metadata=None):
        notification = Notification(
            id=self._next_id, notification_type=notification_type,
            title=title, message=message, priority=priority,
            target_user=target_user, metadata=metadata or {},
        )
        self._notifications.append(notification)
        self._next_id += 1
        return notification

    def get(self, notification_id):
        for n in self._notifications:
            if n.id == notification_id:
                return n
        return None

    def mark_read(self, notification_id):
        n = self.get(notification_id)
        if n:
            n.read = True
            return True
        return False

    def mark_all_read(self, user=None):
        count = 0
        for n in self._notifications:
            if user is None or n.target_user == user:
                if not n.read:
                    n.read = True
                    count += 1
        return count

    def unread(self, user=None):
        return [n for n in self._notifications
                if not n.read and (user is None or n.target_user == user)]

    def all_notifications(self, user=None):
        if user is None:
            return list(self._notifications)
        return [n for n in self._notifications if n.target_user == user]

    def by_type(self, notification_type):
        return [n for n in self._notifications if n.notification_type == notification_type]

    def by_priority(self, priority):
        return [n for n in self._notifications if n.priority == priority]

    def recent(self, limit=10, user=None):
        filtered = self.all_notifications(user)
        return filtered[-limit:] if limit > 0 else []

    def count(self):
        return len(self._notifications)

    def unread_count(self, user=None):
        return len(self.unread(user))

    def clear(self, user=None):
        if user is None:
            self._notifications = []
        else:
            self._notifications = [n for n in self._notifications if n.target_user != user]
        return True

    def clear_read(self, user=None):
        before = len(self._notifications)
        self._notifications = [
            n for n in self._notifications
            if not n.read or (user is not None and n.target_user != user)
        ]
        return before - len(self._notifications)


@dataclass
class NotificationPreferences:
    """Per-user notification preferences."""
    user: str
    channels: Dict[str, bool] = field(default_factory=lambda: {
        "email": True, "desktop": True, "mobile": False, "webhook": False
    })
    muted_types: List[str] = field(default_factory=list)
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    min_priority: str = "low"

    def is_muted(self, notification_type):
        return notification_type in self.muted_types

    def channel_enabled(self, channel):
        return self.channels.get(channel, False)

    def should_deliver(self, notification):
        if self.is_muted(notification.notification_type):
            return False
        priority_order = {"low": 0, "normal": 1, "high": 2, "urgent": 3}
        if priority_order.get(notification.priority, 1) < priority_order.get(self.min_priority, 0):
            return False
        return True


def dispatch_notification(center, notification, preferences=None):
    if preferences and not preferences.should_deliver(notification):
        return {"delivered": False, "reason": "muted or below min priority"}
    channels_used = []
    if preferences:
        for channel, enabled in preferences.channels.items():
            if enabled:
                channels_used.append(channel)
    else:
        channels_used = ["web"]
    return {"notification_id": notification.id, "delivered": True, "channels": channels_used}


def notification_summary(center, user=None):
    return {
        "total": center.count(),
        "unread": center.unread_count(user),
        "by_type": {t: len(center.by_type(t)) for t in set(n.notification_type for n in center.all_notifications(user))},
        "by_priority": {p: len(center.by_priority(p)) for p in ("low", "normal", "high", "urgent")},
    }
