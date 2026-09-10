"""Tests for task pipeline."""
import pytest
from src.task_pipeline import (
    PipelineStep, TaskPipeline, pipeline_report, default_pipeline,
)


class FakeTask:
    def __init__(self, id, title="Task", priority="medium", status="todo"):
        self.id = id
        self.title = title
        self.priority = priority
        self.status = status


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "A", "high", "todo"),
        FakeTask(2, "B", "low", "done"),
        FakeTask(3, "C", "critical", "in-progress"),
        FakeTask(4, "D", "medium", "todo"),
    ]


@pytest.fixture
def pipeline():
    p = TaskPipeline()
    return p


def test_pipe_add(pipeline):
    pipeline.pipe("identity", lambda t: t)
    assert pipeline.step_count() == 1


def test_execute_identity(pipeline, tasks):
    pipeline.pipe("identity", lambda t: t)
    result = pipeline.execute(tasks)
    assert len(result) == 4


def test_filter(pipeline, tasks):
    pipeline.filter(lambda t: t.status == "todo")
    result = pipeline.execute(tasks)
    assert len(result) == 2


def test_sort(pipeline, tasks):
    pipeline.sort(lambda t: t.id, reverse=True)
    result = pipeline.execute(tasks)
    assert result[0].id == 4


def test_limit(pipeline, tasks):
    pipeline.limit(2)
    result = pipeline.execute(tasks)
    assert len(result) == 2


def test_map(pipeline, tasks):
    pipeline.map(lambda t: t.id)
    result = pipeline.execute(tasks)
    assert result == [1, 2, 3, 4]


def test_deduplicate():
    p = TaskPipeline()
    p.deduplicate(key=lambda t: t.id)
    tasks = [FakeTask(1), FakeTask(1), FakeTask(2)]
    result = p.execute(tasks)
    assert len(result) == 2


def test_chained_operations(pipeline, tasks):
    pipeline.filter(lambda t: t.status != "done")
    pipeline.sort(lambda t: t.id, reverse=True)
    pipeline.limit(2)
    result = pipeline.execute(tasks)
    assert len(result) == 2
    assert result[0].id == 4


def test_had_errors(pipeline, tasks):
    pipeline.pipe("fail", lambda t: (_ for _ in ()).throw(ValueError("fail")))
    pipeline.execute(tasks)
    assert pipeline.had_errors() is True


def test_error_steps(pipeline, tasks):
    pipeline.pipe("fail", lambda t: (_ for _ in ()).throw(ValueError("fail")))
    pipeline.execute(tasks)
    assert len(pipeline.error_steps()) == 1


def test_clear(pipeline):
    pipeline.pipe("test", lambda t: t)
    pipeline.clear()
    assert pipeline.step_count() == 0


def test_reset_execution(pipeline, tasks):
    pipeline.pipe("identity", lambda t: t)
    pipeline.execute(tasks)
    assert pipeline.executed_steps()
    pipeline.reset_execution()
    assert len(pipeline.executed_steps()) == 0


def test_total_time(pipeline, tasks):
    pipeline.pipe("identity", lambda t: t)
    pipeline.execute(tasks)
    assert pipeline.total_time_ms() >= 0


def test_pipeline_report(pipeline, tasks):
    pipeline.filter(lambda t: t.status == "todo")
    pipeline.execute(tasks)
    report = pipeline_report(pipeline)
    assert report["total_steps"] == 1
    assert report["total_time_ms"] >= 0


def test_default_pipeline():
    p = default_pipeline()
    assert p.step_count() == 0
