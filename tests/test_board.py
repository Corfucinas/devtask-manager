"""Tests for board configuration."""
import pytest
from src.board import (
    BoardColumn, Board, wip_status, default_board, column_for_status,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, status):
        self.status = FakeStatus(status)


@pytest.fixture
def board():
    b = Board("Test")
    b.add_column(BoardColumn("Backlog", "todo", order=0))
    b.add_column(BoardColumn("WIP", "in-progress", wip_limit=3, order=1))
    b.add_column(BoardColumn("Done", "done", order=2))
    return b


def test_add_and_get_column(board):
    assert board.get_column("WIP") is not None
    assert board.get_column("WIP").wip_limit == 3
    assert board.get_column("nonexistent") is None


def test_columns_in_order(board):
    cols = board.columns_in_order()
    assert [c.name for c in cols] == ["Backlog", "WIP", "Done"]


def test_remove_column(board):
    assert board.remove_column("WIP") is True
    assert board.get_column("WIP") is None
    assert board.remove_column("WIP") is False


def test_reorder_columns(board):
    board.reorder_columns(["Done", "Backlog", "WIP"])
    cols = board.columns_in_order()
    assert [c.name for c in cols] == ["Done", "Backlog", "WIP"]


def test_wip_status_ok(board):
    tasks = [FakeTask("in-progress") for _ in range(3)]
    status = wip_status(tasks, board)
    assert status["WIP"]["count"] == 3
    assert status["WIP"]["over_limit"] is False


def test_wip_status_over(board):
    tasks = [FakeTask("in-progress") for _ in range(5)]
    status = wip_status(tasks, board)
    assert status["WIP"]["count"] == 5
    assert status["WIP"]["over_limit"] is True


def test_wip_status_unlimited(board):
    tasks = [FakeTask("todo") for _ in range(100)]
    status = wip_status(tasks, board)
    assert status["Backlog"]["over_limit"] is False


def test_default_board():
    board = default_board()
    cols = board.columns_in_order()
    assert len(cols) == 4
    assert cols[0].name == "Backlog"
    assert cols[1].wip_limit == 5


def test_column_for_status(board):
    col = column_for_status(board, "in-progress")
    assert col is not None
    assert col.name == "WIP"
    assert column_for_status(board, "nonexistent") is None
