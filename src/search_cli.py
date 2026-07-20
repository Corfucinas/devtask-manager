"""CLI commands for task search and filtering."""

from .storage import TaskStore
from .search import (
    search_by_text,
    filter_by_priority_range,
    group_by_status,
    count_by_priority,
)


def cmd_search(args, store: TaskStore) -> None:
    """Search tasks by text query with optional filters."""
    tasks = store.list()
    if args.query:
        tasks = search_by_text(tasks, args.query)
    if args.priority:
        tasks = filter_by_priority_range(tasks, min_priority=args.priority)
    if args.status:
        tasks = [t for t in tasks if t.status.value == args.status]
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.tags]

    if not tasks:
        print("No matching tasks found.")
        return

    for t in tasks:
        tags_str = f" #{' #'.join(t.tags)}" if t.tags else ""
        print(f"  #{t.id} [{t.status.value}] {t.title}{tags_str}")


def cmd_stats(args, store: TaskStore) -> None:
    """Display task statistics and priority breakdown."""
    tasks = store.list()
    total = len(tasks)
    by_status = group_by_status(tasks)
    by_priority = count_by_priority(tasks)

    print(f"Total tasks: {total}")
    print(f"  Todo:        {len(by_status.get('todo', []))}")
    print(f"  In Progress: {len(by_status.get('in-progress', []))}")
    print(f"  Done:        {len(by_status.get('done', []))}")
    print()
    print("By Priority:")
    for level in ("critical", "high", "medium", "low"):
        count = by_priority.get(level, 0)
        bar = "#" * min(count, 40)
        print(f"  {level:10s} {count:3d} {bar}")


def register_search_commands(subparsers) -> None:
    """Register search and stats subcommands on the given subparsers."""
    p_search = subparsers.add_parser("search", help="Search tasks by text or filters")
    p_search.add_argument(
        "query", nargs="?", help="Text to search in title/description"
    )
    p_search.add_argument(
        "-p", "--priority", choices=["low", "medium", "high", "critical"]
    )
    p_search.add_argument("-s", "--status", choices=["todo", "in-progress", "done"])
    p_search.add_argument("-t", "--tag", help="Filter by tag")

    p_stats = subparsers.add_parser("stats", help="Show task statistics")
    p_stats.set_defaults(func=cmd_stats)
