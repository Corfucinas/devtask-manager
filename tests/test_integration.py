"""Tests for integration registry."""
import pytest
from src.integration import (
    Integration, IntegrationRegistry, default_integrations,
    integration_summary, sync_all,
)


@pytest.fixture
def registry():
    r = IntegrationRegistry()
    r.register("Jira", "jira", {"base_url": "https://jira.example.com"})
    r.register("Slack", "slack", {"webhook_url": "https://hooks.slack.com/xxx"})
    return r


def test_register():
    r = IntegrationRegistry()
    i = r.register("Test", "github", {"token": "xxx"})
    assert i.id == 1
    assert i.name == "Test"
    assert i.integration_type == "github"
    assert i.status == "disconnected"


def test_get(registry):
    assert registry.get(1) is not None
    assert registry.get(1).name == "Jira"
    assert registry.get(999) is None


def test_find_by_name(registry):
    assert registry.find_by_name("Jira") is not None
    assert registry.find_by_name("JIRA") is not None
    assert registry.find_by_name("nonexistent") is None


def test_find_by_type(registry):
    jira = registry.find_by_type("jira")
    assert len(jira) == 1


def test_remove(registry):
    assert registry.remove(1) is True
    assert registry.get(1) is None
    assert registry.count() == 1
    assert registry.remove(999) is False


def test_connect(registry):
    assert registry.connect(1) is True
    assert registry.get(1).status == "connected"
    assert registry.connect(999) is False


def test_disconnect(registry):
    registry.connect(1)
    assert registry.disconnect(1) is True
    assert registry.get(1).status == "disconnected"


def test_sync_integration(registry):
    registry.connect(1)
    assert registry.sync_integration(1) is True
    assert registry.get(1).sync_count == 1
    assert registry.get(1).last_sync is not None


def test_sync_not_connected(registry):
    assert registry.sync_integration(1) is False
    assert registry.get(1).sync_count == 0


def test_mark_error(registry):
    assert registry.mark_error(1, "Auth failed") is True
    assert registry.get(1).status == "error"
    assert registry.get(1).error_message == "Auth failed"


def test_update_config(registry):
    assert registry.update_config(1, {"project_key": "PROJ"}) is True
    assert registry.get(1).config["project_key"] == "PROJ"


def test_connected_disconnected(registry):
    registry.connect(1)
    assert len(registry.connected()) == 1
    assert len(registry.disconnected()) == 1


def test_errored(registry):
    registry.mark_error(1, "fail")
    assert len(registry.errored()) == 1


def test_count(registry):
    assert registry.count() == 2


def test_default_integrations():
    r = default_integrations()
    assert r.count() == 4
    assert r.find_by_name("Jira") is not None


def test_integration_summary(registry):
    registry.connect(1)
    summary = integration_summary(registry)
    assert summary["total"] == 2
    assert summary["connected"] == 1


def test_sync_all(registry):
    registry.connect(1)
    registry.connect(2)
    results = sync_all(registry)
    assert len(results) == 2
    assert all(r["synced"] for r in results)
