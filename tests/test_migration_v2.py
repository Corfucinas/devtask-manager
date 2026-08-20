"""Tests for migration framework."""
import pytest
from src.migration_v2 import Migration, MigrationRunner, migration_report


@pytest.fixture
def runner():
    r = MigrationRunner()
    state = {"value": 0}
    r.register(1, "Add field", lambda ctx: ctx.update({"value": 1}) if ctx else None,
               down=lambda ctx: ctx.update({"value": 0}) if ctx else None)
    r.register(2, "Update field", lambda ctx: ctx.update({"value": 2}) if ctx else None,
               down=lambda ctx: ctx.update({"value": 1}) if ctx else None)
    r.register(3, "Add index", lambda ctx: ctx.update({"value": 3}) if ctx else None)
    return r, state


def test_register():
    r = MigrationRunner()
    m = r.register(1, "test", lambda ctx: None)
    assert m.version == 1
    assert r.count() == 1


def test_get(runner):
    r, _ = runner
    assert r.get(1) is not None
    assert r.get(1).name == "Add field"
    assert r.get(999) is None


def test_all_migrations_sorted(runner):
    r, _ = runner
    migrations = r.all_migrations()
    assert migrations[0].version < migrations[1].version


def test_pending(runner):
    r, _ = runner
    assert len(r.pending()) == 3


def test_migrate(runner):
    r, state = runner
    results = r.migrate(state)
    assert len(results) == 3
    assert all(res["success"] for res in results)
    assert r.current_version() == 3
    assert len(r.pending()) == 0


def test_migrate_partial(runner):
    r, state = runner
    r._current_version = 1
    r._migrations[1].applied_at = "2026-01-01T00:00:00+00:00"
    results = r.migrate(state)
    assert len(results) == 2


def test_rollback(runner):
    r, state = runner
    r.migrate(state)
    results = r.rollback(1, state)
    assert r.current_version() == 1


def test_rollback_no_down():
    r = MigrationRunner()
    r.register(1, "no down", lambda ctx: None)
    r.migrate({})
    results = r.rollback(0, {})
    assert results[0]["success"] is False


def test_applied(runner):
    r, state = runner
    r.migrate(state)
    assert len(r.applied()) == 3


def test_is_up_to_date(runner):
    r, state = runner
    assert not r.is_up_to_date()
    r.migrate(state)
    assert r.is_up_to_date()


def test_history(runner):
    r, state = runner
    r.migrate(state)
    assert len(r.history()) == 3
    assert r.history()[0]["action"] == "up"


def test_migration_report(runner):
    r, state = runner
    r.migrate(state)
    report = migration_report(r)
    assert report["current_version"] == 3
    assert report["applied"] == 3
    assert report["up_to_date"] is True
