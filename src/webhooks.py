"""Webhook event management and dispatch."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Webhook:
    """A registered webhook endpoint."""
    id: int
    url: str
    events: List[str] = field(default_factory=list)
    secret: str = ""
    active: bool = True
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def matches(self, event_type: str) -> bool:
        """Check if this webhook should receive an event type."""
        if not self.active:
            return False
        if "*" in self.events:
            return True
        return event_type in self.events


@dataclass
class WebhookEvent:
    """A dispatched webhook event with delivery tracking."""
    id: int
    webhook_id: int
    event_type: str
    payload: dict
    status: str = "pending"
    attempts: int = 0
    delivered_at: Optional[str] = None


class WebhookRegistry:
    """Manages webhook registrations and event dispatch."""

    def __init__(self):
        self._webhooks: Dict[int, Webhook] = {}
        self._events: List[WebhookEvent] = []
        self._next_id = 1
        self._event_id = 1

    def register(self, url: str, events: List[str], secret: str = "") -> Webhook:
        hook = Webhook(id=self._next_id, url=url, events=list(events), secret=secret)
        self._webhooks[self._next_id] = hook
        self._next_id += 1
        return hook

    def unregister(self, webhook_id: int) -> bool:
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            return True
        return False

    def get(self, webhook_id: int) -> Optional[Webhook]:
        return self._webhooks.get(webhook_id)

    def list_webhooks(self) -> List[Webhook]:
        return list(self._webhooks.values())

    def dispatch(self, event_type: str, payload: dict) -> List[WebhookEvent]:
        dispatched = []
        for hook in self._webhooks.values():
            if hook.matches(event_type):
                event = WebhookEvent(
                    id=self._event_id,
                    webhook_id=hook.id,
                    event_type=event_type,
                    payload=payload,
                )
                self._events.append(event)
                self._event_id += 1
                dispatched.append(event)
        return dispatched

    def mark_delivered(self, event_id: int) -> bool:
        for event in self._events:
            if event.id == event_id:
                event.status = "delivered"
                event.delivered_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def mark_failed(self, event_id: int) -> bool:
        for event in self._events:
            if event.id == event_id:
                event.status = "failed"
                event.attempts += 1
                return True
        return False

    def event_history(self, webhook_id: Optional[int] = None) -> List[WebhookEvent]:
        if webhook_id is None:
            return list(self._events)
        return [e for e in self._events if e.webhook_id == webhook_id]

    def pending_events(self) -> List[WebhookEvent]:
        return [e for e in self._events if e.status == "pending"]
