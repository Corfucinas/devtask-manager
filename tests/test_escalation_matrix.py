"""Tests for escalation matrix."""
import pytest
from src.escalation_matrix import (
    EscalationLevel, EscalationRecord, EscalationMatrix,
    escalation_report, default_escalation_matrix,
)


class FakeTask:
    def __init__(self, id):
        self.id = id


@pytest.fixture
def matrix():
    m = EscalationMatrix()
    m.add_level(1, "Team Lead", "lead", response_time_hours=8)
    m.add_level(2, "Manager", "mgr", response_time_hours=4)
    m.add_level(3, "VP", "vp", response_time_hours=2)
    return m


def test_add_level():
    m = EscalationMatrix()
    level = m.add_level(1, "Test", "contact")
    assert level.level == 1
    assert level.name == "Test"


def test_get_level(matrix):
    level = matrix.get_level(1)
    assert level is not None
    assert level.name == "Team Lead"
    assert matrix.get_level(999) is None


def test_all_levels(matrix):
    levels = matrix.all_levels()
    assert len(levels) == 3
    assert levels[0].level <= levels[1].level


def test_level_count(matrix):
    assert matrix.level_count() == 3


def test_escalate(matrix):
    record = matrix.escalate(task_id=1, level=2, reason="Stuck")
    assert record is not None
    assert record.task_id == 1
    assert record.level == 2
    assert record.contact == "mgr"


def test_escalate_invalid_level(matrix):
    assert matrix.escalate(task_id=1, level=999) is None


def test_auto_escalate(matrix):
    task = FakeTask(1)
    record = matrix.auto_escalate(task, severity="critical")
    assert record is not None
    assert record.level == 3


def test_auto_escalate_low(matrix):
    task = FakeTask(1)
    assert matrix.auto_escalate(task, severity="low") is None


def test_records(matrix):
    matrix.escalate(1, level=1)
    matrix.escalate(2, level=2)
    assert len(matrix.records()) == 2


def test_records_for_task(matrix):
    matrix.escalate(1, level=1)
    matrix.escalate(1, level=2)
    matrix.escalate(2, level=1)
    assert len(matrix.records_for_task(1)) == 2


def test_acknowledge(matrix):
    r = matrix.escalate(1, level=1)
    assert matrix.acknowledge(r.id) is True
    assert r.acknowledged is True
    assert matrix.acknowledge(999) is False


def test_unacknowledged(matrix):
    matrix.escalate(1, level=1)
    matrix.escalate(2, level=1)
    assert len(matrix.unacknowledged()) == 2
    matrix.acknowledge(1)
    assert len(matrix.unacknowledged()) == 1


def test_record_count(matrix):
    matrix.escalate(1, level=1)
    assert matrix.record_count() == 1


def test_clear_records(matrix):
    matrix.escalate(1, level=1)
    matrix.clear_records()
    assert matrix.record_count() == 0


def test_escalation_report(matrix):
    matrix.escalate(1, level=1)
    matrix.escalate(2, level=2)
    report = escalation_report(matrix)
    assert report["total_levels"] == 3
    assert report["total_escalations"] == 2
    assert "by_level" in report


def test_default_escalation_matrix():
    m = default_escalation_matrix()
    assert m.level_count() == 3
    assert m.get_level(3).contact == "vp_eng"
