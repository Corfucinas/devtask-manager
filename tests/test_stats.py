"""Tests for statistics module."""
import pytest
from src.models import Task, Priority, Status
from src.stats import task_summary, productivity_score, streak_info

class TestTaskSummary:
    def test_empty(self):
        s = task_summary([])
        assert s["total"] == 0
    def test_mixed(self):
        tasks = [Task(id=1, title="A", status=Status.DONE, priority=Priority.HIGH), Task(id=2, title="B", status=Status.TODO), Task(id=3, title="C", status=Status.IN_PROGRESS)]
        s = task_summary(tasks)
        assert s["total"] == 3
        assert s["done"] == 1

class TestProductivityScore:
    def test_empty(self):
        assert productivity_score([]) == 0
    def test_done_high(self):
        assert productivity_score([Task(id=1, title="X", status=Status.DONE, priority=Priority.HIGH)]) == 3
    def test_undone_no_score(self):
        assert productivity_score([Task(id=1, title="X", status=Status.TODO, priority=Priority.CRITICAL)]) == 0

class TestStreakInfo:
    def test_no_completed(self):
        assert streak_info([])["current_streak"] == 0
