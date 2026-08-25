"""Tests for crash recovery manager."""
import pytest
from src.recovery_manager import (
    RecoveryCheckpoint, RecoveryManager, recovery_report, auto_save,
)


@pytest.fixture
def manager():
    m = RecoveryManager(max_checkpoints=5)
    m.save_checkpoint("v1", {"count": 10})
    m.save_checkpoint("v2", {"count": 20})
    m.save_checkpoint("v3", {"count": 30})
    return m


def test_save_checkpoint():
    m = RecoveryManager()
    cp = m.save_checkpoint("test", {"data": 1})
    assert cp.id == 1
    assert cp.name == "test"
    assert cp.state == {"data": 1}


def test_restore_checkpoint(manager):
    state = manager.restore_checkpoint(1)
    assert state == {"count": 10}
    assert manager.restored_count() == 1


def test_restore_nonexistent(manager):
    assert manager.restore_checkpoint(999) is None


def test_restore_latest(manager):
    state = manager.restore_latest()
    assert state == {"count": 30}


def test_restore_latest_empty():
    m = RecoveryManager()
    assert m.restore_latest() is None


def test_get(manager):
    assert manager.get(1) is not None
    assert manager.get(1).name == "v1"
    assert manager.get(999) is None


def test_all_checkpoints(manager):
    cps = manager.all_checkpoints()
    assert len(cps) == 3
    assert cps[0].id < cps[1].id


def test_count(manager):
    assert manager.count() == 3


def test_restored_count(manager):
    manager.restore_checkpoint(1)
    assert manager.restored_count() == 1


def test_remove(manager):
    assert manager.remove(1) is True
    assert manager.get(1) is None
    assert manager.count() == 2
    assert manager.remove(999) is False


def test_clear(manager):
    manager.clear()
    assert manager.count() == 0
    assert manager.restored_count() == 0


def test_latest(manager):
    latest = manager.latest()
    assert latest.name == "v3"


def test_latest_empty():
    m = RecoveryManager()
    assert m.latest() is None


def test_find_by_name(manager):
    cp = manager.find_by_name("v2")
    assert cp is not None
    assert cp.state == {"count": 20}
    assert manager.find_by_name("nonexistent") is None


def test_max_checkpoints():
    m = RecoveryManager(max_checkpoints=2)
    m.save_checkpoint("a", {1: 1})
    m.save_checkpoint("b", {2: 2})
    m.save_checkpoint("c", {3: 3})
    assert m.count() == 2
    assert m.get(1) is None  # oldest removed


def test_recovery_report(manager):
    report = recovery_report(manager)
    assert report["total_checkpoints"] == 3
    assert report["restored_count"] == 0
    assert report["latest_checkpoint"] == "v3"


def test_auto_save():
    m = RecoveryManager()
    class FakeTask:
        def __init__(self, id): self.id = id
    tasks = [FakeTask(1), FakeTask(2), FakeTask(3)]
    cp = auto_save(m, tasks, "auto1")
    assert cp.name == "auto1"
    assert cp.state["task_count"] == 3
