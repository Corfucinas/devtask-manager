"""Tests for Kanban board view."""
import pytest
from src.kanban import render_board, column_summary, progress_percentage


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, title, status="todo"):
        self.title = title
        self.status = FakeStatus(status)


@pytest.fixture
def tasks():
    return [
        FakeTask("Fix bug", "todo"),
        FakeTask("Add feature", "in-progress"),
        FakeTask("Write docs", "done"),
        FakeTask("Refactor", "todo"),
    ]


def test_render_board_has_columns(tasks):
    board = render_board(tasks)
    assert "TODO" in board
    assert "IN-PROGRESS" in board
    assert "DONE" in board


def test_column_summary(tasks):
    summary = column_summary(tasks)
    assert summary == {"todo": 2, "in-progress": 1, "done": 1}


def test_progress_percentage(tasks):
    pct = progress_percentage(tasks)
    assert pct == 25.0


def test_progress_empty():
    assert progress_percentage([]) == 0.0


def test_progress_all_done():
    tasks = [FakeTask("a", "done"), FakeTask("b", "done")]
    assert progress_percentage(tasks) == 100.0
