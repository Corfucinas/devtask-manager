"""Tests for task warden."""
import pytest
from src.task_warden import QualityCheck, TaskWarden, warden_report, default_warden


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id=1, title="Task", description="Desc", priority="medium",
                 status="todo", assignee=None):
        self.id = id
        self.title = title
        self.description = description
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.assignee = assignee


@pytest.fixture
def warden():
    w = TaskWarden()
    w.add_check("Has title", lambda t: bool((t.title or "").strip()), "error", "No title")
    w.add_check("Has assignee", lambda t: bool(t.assignee), "error", "No assignee")
    w.add_check("Has description", lambda t: bool((t.description or "").strip()), "warning", "No desc")
    return w


def test_quality_check_pass():
    qc = QualityCheck(id=1, name="test", check=lambda t: True)
    assert qc.run(FakeTask()) is True


def test_quality_check_fail():
    qc = QualityCheck(id=1, name="test", check=lambda t: False)
    assert qc.run(FakeTask()) is False


def test_quality_check_disabled():
    qc = QualityCheck(id=1, name="test", check=lambda t: False)
    qc.enabled = False
    assert qc.run(FakeTask()) is True


def test_warden_add():
    w = TaskWarden()
    qc = w.add_check("test", lambda t: True)
    assert qc.id == 1


def test_warden_remove(warden):
    assert warden.remove_check(1) is True
    assert warden.get_check(1) is None
    assert warden.remove_check(999) is False


def test_warden_count(warden):
    assert warden.count() == 3


def test_check_task_pass(warden):
    task = FakeTask(1, title="Task", description="Desc", assignee="alice")
    results = warden.check_task(task)
    assert all(r["passed"] for r in results)


def test_check_task_fail_title(warden):
    task = FakeTask(1, title="")
    results = warden.check_task(task)
    assert any(not r["passed"] for r in results)


def test_check_batch(warden):
    tasks = [FakeTask(1, title="OK", assignee="alice"),
             FakeTask(2, title="", assignee=None)]
    results = warden.check_batch(tasks)
    assert len(results) == 6  # 3 checks x 2 tasks


def test_failing_checks(warden):
    task = FakeTask(1, title="", assignee=None)
    failing = warden.failing_checks(task)
    assert len(failing) >= 2


def test_blocking_checks(warden):
    task = FakeTask(1, title="", assignee=None)
    blocking = warden.blocking_checks(task)
    assert all(r["severity"] == "error" for r in blocking)


def test_can_complete(warden):
    task = FakeTask(1, title="OK", assignee="alice", description="Desc")
    assert warden.can_complete(task) is True


def test_cannot_complete(warden):
    task = FakeTask(1, title="", assignee=None)
    assert warden.can_complete(task) is False


def test_enable_disable(warden):
    assert warden.disable(1) is True
    task = FakeTask(1, title="")
    results = warden.check_task(task)
    # Title check disabled, should pass
    title_results = [r for r in results if r["check_name"] == "Has title"]
    assert len(title_results) == 0


def test_clear_results(warden):
    warden.check_task(FakeTask(1, title="OK", assignee="alice"))
    warden.clear_results()
    assert len(warden.results()) == 0


def test_warden_report(warden):
    tasks = [FakeTask(1, title="OK", assignee="alice"),
             FakeTask(2, title="", assignee=None)]
    report = warden_report(warden, tasks)
    assert report["total_tasks"] == 2
    assert "pass_rate" in report
    assert "compliant_tasks" in report


def test_default_warden():
    w = default_warden()
    assert w.count() == 4
    task = FakeTask(1, title="", priority="critical")
    assert w.can_complete(task) is False
    task2 = FakeTask(1, title="OK", description="Desc", priority="high", assignee="alice")
    assert w.can_complete(task2) is True
