"""CLI interface for DevTask Manager."""

import argparse
import sys
from .storage import TaskStore
from .models import Status, Priority


def format_task(task, index=None):
    priority_colors = {
        "critical": "\033[91m",
        "high": "\033[93m",
        "medium": "\033[92m",
        "low": "\033[94m",
    }
    status_icons = {"todo": "[ ]", "in-progress": "[~]", "done": "[x]"}
    color = priority_colors.get(task.priority.value, "")
    reset = "\033[0m"
    icon = status_icons.get(task.status.value, "[?]")
    tags_str = f" #{' #'.join(task.tags)}" if task.tags else ""
    idx = f"#{task.id}" if index is None else f"#{index}"
    return f"  {idx} {icon} {color}{task.title}{reset}{tags_str}"


def cmd_add(args, store):
    task = store.create(
        title=args.title,
        description=args.description or "",
        priority=args.priority,
        tags=args.tags or [],
    )
    print(f"Added task #{task.id}: {task.title}")


def cmd_list(args, store):
    tasks = store.list(status=args.status, priority=args.priority, tag=args.tag)
    if not tasks:
        print("No tasks found.")
        return
    for t in tasks:
        print(format_task(t))


def cmd_update(args, store):
    kwargs = {}
    if args.title:
        kwargs["title"] = args.title
    if args.description is not None:
        kwargs["description"] = args.description
    if args.priority:
        kwargs["priority"] = args.priority
    if args.status:
        kwargs["status"] = args.status
    if args.tags is not None:
        kwargs["tags"] = args.tags
    task = store.update(args.id, **kwargs)
    if not task:
        print(f"Task #{args.id} not found.")
        sys.exit(1)
    print(f"Updated task #{task.id}: {task.title}")


def cmd_done(args, store):
    task = store.update(args.id, status="done")
    if not task:
        print(f"Task #{args.id} not found.")
        sys.exit(1)
    print(f"Completed: {task.title}")


def cmd_delete(args, store):
    if store.delete(args.id):
        print(f"Deleted task #{args.id}.")
    else:
        print(f"Task #{args.id} not found.")
        sys.exit(1)


def cmd_show(args, store):
    task = store.get(args.id)
    if not task:
        print(f"Task #{args.id} not found.")
        sys.exit(1)
    print(f"  ID: #{task.id}")
    print(f"  Title: {task.title}")
    print(f"  Status: {task.status.value}")
    print(f"  Priority: {task.priority.value}")
    print(f"  Tags: {', '.join(task.tags) if task.tags else 'none'}")
    print(f"  Description: {task.description or 'none'}")
    print(f"  Created: {task.created_at}")
    print(f"  Updated: {task.updated_at}")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="devtask", description="Developer task manager"
    )
    parser.add_argument("--storage", help="Path to tasks.json", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_add = subparsers.add_parser("add", help="Add a new task")
    p_add.add_argument("title", help="Task title")
    p_add.add_argument("-d", "--description", help="Task description")
    p_add.add_argument(
        "-p",
        "--priority",
        choices=["low", "medium", "high", "critical"],
        default="medium",
    )
    p_add.add_argument("-t", "--tags", nargs="*", help="Tags for the task")

    p_list = subparsers.add_parser("list", help="List tasks")
    p_list.add_argument("-s", "--status", choices=["todo", "in-progress", "done"])
    p_list.add_argument(
        "-p", "--priority", choices=["low", "medium", "high", "critical"]
    )
    p_list.add_argument("-t", "--tag", help="Filter by tag")

    p_update = subparsers.add_parser("update", help="Update a task")
    p_update.add_argument("id", type=int)
    p_update.add_argument("--title")
    p_update.add_argument("-d", "--description")
    p_update.add_argument(
        "-p", "--priority", choices=["low", "medium", "high", "critical"]
    )
    p_update.add_argument("-s", "--status", choices=["todo", "in-progress", "done"])
    p_update.add_argument("-t", "--tags", nargs="*")

    p_done = subparsers.add_parser("done", help="Mark task as done")
    p_done.add_argument("id", type=int)

    p_del = subparsers.add_parser("delete", help="Delete a task")
    p_del.add_argument("id", type=int)

    p_show = subparsers.add_parser("show", help="Show task details")
    p_show.add_argument("id", type=int)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    store = TaskStore(args.storage)
    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "update": cmd_update,
        "done": cmd_done,
        "delete": cmd_delete,
        "show": cmd_show,
    }
    commands[args.command](args, store)


if __name__ == "__main__":
    main()
