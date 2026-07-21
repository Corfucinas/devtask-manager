"""Board column configuration with WIP limits."""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class BoardColumn:
    """A board column with optional WIP limit."""
    name: str
    status: str
    wip_limit: int = 0
    order: int = 0


class Board:
    """Manages board columns and their configuration."""

    def __init__(self, name: str = "Default"):
        self.name = name
        self._columns: Dict[str, BoardColumn] = {}

    def add_column(self, column: BoardColumn) -> None:
        self._columns[column.name] = column

    def get_column(self, name: str) -> Optional[BoardColumn]:
        return self._columns.get(name)

    def columns_in_order(self) -> List[BoardColumn]:
        return sorted(self._columns.values(), key=lambda c: c.order)

    def remove_column(self, name: str) -> bool:
        if name in self._columns:
            del self._columns[name]
            return True
        return False

    def reorder_columns(self, order: List[str]) -> None:
        for i, name in enumerate(order):
            if name in self._columns:
                self._columns[name].order = i


def wip_status(tasks, board: Board) -> Dict[str, dict]:
    """Check WIP limit violations for each column."""
    result = {}
    for column in board.columns_in_order():
        count = sum(
            1 for t in tasks
            if (t.status.value if hasattr(t.status, "value") else t.status) == column.status
        )
        result[column.name] = {
            "count": count,
            "limit": column.wip_limit,
            "over_limit": column.wip_limit > 0 and count > column.wip_limit,
        }
    return result


def default_board() -> Board:
    """Create a board with default columns."""
    board = Board("Default")
    board.add_column(BoardColumn("Backlog", "todo", wip_limit=0, order=0))
    board.add_column(BoardColumn("In Progress", "in-progress", wip_limit=5, order=1))
    board.add_column(BoardColumn("Review", "review", wip_limit=3, order=2))
    board.add_column(BoardColumn("Done", "done", wip_limit=0, order=3))
    return board


def column_for_status(board: Board, status: str) -> Optional[BoardColumn]:
    """Find which column a given status maps to."""
    for column in board._columns.values():
        if column.status == status:
            return column
    return None
