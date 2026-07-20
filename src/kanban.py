"""Kanban board view for task visualization."""


def render_board(tasks, column_width=20):
    """Render tasks as a Kanban board with status columns."""
    columns = {"todo": [], "in-progress": [], "done": []}
    for t in tasks:
        key = t.status.value if hasattr(t.status, "value") else t.status
        if key in columns:
            columns[key].append(t)

    header = f"{'TODO':^{column_width}}|{'IN-PROGRESS':^{column_width}}|{'DONE':^{column_width}}"
    separator = "-" * column_width + "|" + "-" * column_width + "|" + "-" * column_width

    rows = max(len(c) for c in columns.values())
    lines = [header, separator]
    for i in range(rows):
        cells = []
        for col in ("todo", "in-progress", "done"):
            if i < len(columns[col]):
                t = columns[col][i]
                title = t.title[:column_width - 2]
                cells.append(f"{title:^{column_width}}")
            else:
                cells.append(" " * column_width)
        lines.append("|".join(cells))
    return "\n".join(lines)


def column_summary(tasks):
    """Return counts per Kanban column."""
    counts = {"todo": 0, "in-progress": 0, "done": 0}
    for t in tasks:
        key = t.status.value if hasattr(t.status, "value") else t.status
        if key in counts:
            counts[key] += 1
    return counts


def progress_percentage(tasks):
    """Calculate completion percentage."""
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks if (t.status.value if hasattr(t.status, "value") else t.status) == "done")
    return (done / len(tasks)) * 100
