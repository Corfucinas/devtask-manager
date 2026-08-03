"""External integration registry and sync."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Integration:
    """An external system integration."""
    id: int
    name: str
    integration_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    status: str = "disconnected"
    last_sync: Optional[str] = None
    sync_count: int = 0
    error_message: Optional[str] = None
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class IntegrationRegistry:
    """Manages external integrations."""

    def __init__(self):
        self._integrations: Dict[int, Integration] = {}
        self._next_id = 1

    def register(self, name, integration_type, config=None):
        integration = Integration(id=self._next_id, name=name,
                                   integration_type=integration_type, config=config or {})
        self._integrations[self._next_id] = integration
        self._next_id += 1
        return integration

    def get(self, integration_id):
        return self._integrations.get(integration_id)

    def find_by_name(self, name):
        for i in self._integrations.values():
            if i.name.lower() == name.lower():
                return i
        return None

    def find_by_type(self, integration_type):
        return [i for i in self._integrations.values() if i.integration_type == integration_type]

    def remove(self, integration_id):
        if integration_id in self._integrations:
            del self._integrations[integration_id]
            return True
        return False

    def all_integrations(self):
        return list(self._integrations.values())

    def connected(self):
        return [i for i in self._integrations.values() if i.status == "connected"]

    def disconnected(self):
        return [i for i in self._integrations.values() if i.status == "disconnected"]

    def errored(self):
        return [i for i in self._integrations.values() if i.status == "error"]

    def connect(self, integration_id):
        i = self._integrations.get(integration_id)
        if i:
            i.status = "connected"
            i.error_message = None
            return True
        return False

    def disconnect(self, integration_id):
        i = self._integrations.get(integration_id)
        if i:
            i.status = "disconnected"
            return True
        return False

    def sync_integration(self, integration_id):
        i = self._integrations.get(integration_id)
        if not i or i.status != "connected":
            return False
        i.status = "syncing"
        i.sync_count += 1
        i.last_sync = datetime.now(timezone.utc).isoformat()
        i.status = "connected"
        return True

    def mark_error(self, integration_id, error):
        i = self._integrations.get(integration_id)
        if i:
            i.status = "error"
            i.error_message = error
            return True
        return False

    def count(self):
        return len(self._integrations)

    def update_config(self, integration_id, config):
        i = self._integrations.get(integration_id)
        if i:
            i.config.update(config)
            return True
        return False


def default_integrations():
    registry = IntegrationRegistry()
    defaults = [
        ("Jira", "jira", {"base_url": "", "project_key": "", "api_token": ""}),
        ("Slack", "slack", {"webhook_url": "", "channel": "#tasks"}),
        ("GitHub", "github", {"repo": "", "token": "", "label_mapping": {}}),
        ("Linear", "linear", {"api_key": "", "team_id": ""}),
    ]
    for name, itype, config in defaults:
        registry.register(name, itype, config)
    return registry


def integration_summary(registry):
    return {
        "total": registry.count(),
        "connected": len(registry.connected()),
        "disconnected": len(registry.disconnected()),
        "errored": len(registry.errored()),
    }


def sync_all(registry):
    results = []
    for integration in registry.connected():
        success = registry.sync_integration(integration.id)
        results.append({"integration_id": integration.id, "name": integration.name, "synced": success})
    return results
