"""Tests for task batch processor."""
import pytest
from src.task_batch import (
    BatchResult, BatchProcessor, batch_report, batch_summary, default_processor,
)


class FakeTask:
    def __init__(self, id, should_fail=False):
        self.id = id
        self.should_fail = should_fail


@pytest.fixture
def tasks():
    return [FakeTask(i) for i in range(5)]


@pytest.fixture
def processor():
    return BatchProcessor(batch_size=2)


def test_batch_result_success_rate():
    r = BatchResult(total=10, success=7, failed=3)
    assert r.success_rate == 70.0


def test_batch_result_empty():
    r = BatchResult()
    assert r.success_rate == 0.0


def test_process_batch_success(processor, tasks):
    def op(task):
        return task.id
    result = processor.process_batch(tasks, op)
    assert result.success == 5
    assert result.failed == 0


def test_process_batch_with_errors(processor, tasks):
    def op(task):
        if task.id == 2:
            raise ValueError("fail")
        return task.id
    result = processor.process_batch(tasks, op)
    assert result.success == 4
    assert result.failed == 1
    assert len(result.errors) == 1


def test_process_chunks(processor, tasks):
    def op(task):
        return task.id
    results = processor.process_chunks(tasks, op, chunk_size=2)
    assert len(results) == 3  # 5 tasks / 2 = 3 chunks


def test_history(processor, tasks):
    processor.process_batch(tasks, lambda t: t.id)
    assert len(processor.history()) == 1


def test_clear_history(processor, tasks):
    processor.process_batch(tasks, lambda t: t.id)
    processor.clear_history()
    assert len(processor.history()) == 0


def test_total_processed(processor, tasks):
    processor.process_batch(tasks, lambda t: t.id)
    assert processor.total_processed() == 5


def test_total_success(processor, tasks):
    processor.process_batch(tasks, lambda t: t.id)
    assert processor.total_success() == 5


def test_batch_report():
    r = BatchResult(total=10, success=8, failed=2,
                    errors=["err1", "err2"])
    report = batch_report(r)
    assert report["total"] == 10
    assert report["success"] == 8
    assert report["failed"] == 2
    assert report["success_rate"] == 80.0
    assert len(report["errors"]) == 2


def test_batch_summary(processor, tasks):
    processor.process_batch(tasks, lambda t: t.id)
    summary = batch_summary(processor)
    assert summary["total_batches"] == 1
    assert summary["total_processed"] == 5


def test_default_processor():
    p = default_processor()
    assert p._batch_size == 10


def test_batch_result_duration():
    r = BatchResult(total=1, success=1,
                    started_at="2026-01-01T00:00:00+00:00",
                    finished_at="2026-01-01T00:00:01+00:00")
    assert r.duration_seconds == 1.0
