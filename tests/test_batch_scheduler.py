"""Tests for batch scheduler."""
import pytest
from src.batch_scheduler import ScheduledOp, BatchScheduler, scheduler_report


@pytest.fixture
def scheduler():
    s = BatchScheduler()
    s.schedule("update", task_ids=[1, 2], delay_seconds=0)
    s.schedule("notify", task_ids=[3], delay_seconds=3600)
    return s


def test_schedule():
    s = BatchScheduler()
    op = s.schedule("update", task_ids=[1, 2])
    assert op.id == 1
    assert op.operation == "update"
    assert op.task_ids == [1, 2]


def test_schedule_with_delay():
    s = BatchScheduler()
    op = s.schedule("notify", delay_seconds=60)
    assert op.scheduled_time != ""
    assert op.is_due is False


def test_schedule_no_delay():
    s = BatchScheduler()
    op = s.schedule("update")
    assert op.scheduled_time == ""
    assert op.is_due is True


def test_cancel(scheduler):
    assert scheduler.cancel(1) is True
    assert scheduler.get(1) is None
    assert scheduler.cancel(999) is False


def test_get(scheduler):
    assert scheduler.get(1) is not None
    assert scheduler.get(999) is None


def test_all_ops(scheduler):
    assert len(scheduler.all_ops()) == 2


def test_pending(scheduler):
    assert len(scheduler.pending()) == 2


def test_due(scheduler):
    due = scheduler.due()
    assert len(due) == 1  # only the immediate one


def test_count(scheduler):
    assert scheduler.count() == 2


def test_process_due(scheduler):
    results = scheduler.process_due()
    assert len(results) == 1
    assert results[0]["operation"] == "update"
    assert scheduler.get(1) is None  # executed and removed


def test_process_due_with_callback():
    s = BatchScheduler()
    callback_result = {"status": "done"}
    s.schedule("update", task_ids=[1], callback=lambda ids, **kw: callback_result)
    results = s.process_due()
    assert results[0]["result"] == callback_result


def test_process_due_nothing():
    s = BatchScheduler()
    s.schedule("notify", delay_seconds=3600)
    results = s.process_due()
    assert len(results) == 0


def test_history(scheduler):
    scheduler.process_due()
    assert len(scheduler.history()) == 1


def test_clear_history(scheduler):
    scheduler.process_due()
    scheduler.clear_history()
    assert len(scheduler.history()) == 0


def test_clear_all(scheduler):
    scheduler.clear_all()
    assert scheduler.count() == 0
    assert len(scheduler.history()) == 0


def test_scheduler_report(scheduler):
    report = scheduler_report(scheduler)
    assert report["total_scheduled"] == 2
    assert report["pending"] == 2
    assert report["due"] == 1


def test_scheduled_op_is_due_executed():
    op = ScheduledOp(id=1, operation="test", executed=True)
    assert op.is_due is False
