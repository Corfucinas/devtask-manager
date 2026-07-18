"""Notification system for task reminders."""
import os, subprocess
from .models import Task, Status
from datetime import datetime, timezone, timedelta

def get_overdue_tasks(tasks):
    overdue = []
    for t in tasks:
        if t.status != Status.DONE and hasattr(t, '_due_date'):
            due = datetime.fromisoformat(t._due_date)
            if datetime.now(timezone.utc) > due:
                overdue.append(t)
    return overdue

def get_due_soon(tasks, hours=24):
    soon = []
    threshold = datetime.now(timezone.utc) + timedelta(hours=hours)
    for t in tasks:
        if t.status != Status.DONE and hasattr(t, '_due_date'):
            due = datetime.fromisoformat(t._due_date)
            if datetime.now(timezone.utc) < due <= threshold:
                soon.append(t)
    return soon

def format_notification(task, type="overdue"):
    icons = {"overdue": "!", "due_soon": "*", "reminder": "@"}
    icon = icons.get(type, "?")
    return f"[{icon}] Task #{task.id}: {task.title} ({task.priority.value})"

def desktop_notify(message):
    try:
        if os.name == "posix":
            subprocess.run(["notify-send", "DevTask", message], timeout=5, capture_output=True)
    except Exception:
        pass

def check_and_notify(tasks):
    notifications = []
    for t in get_overdue_tasks(tasks):
        msg = format_notification(t, "overdue")
        notifications.append(msg)
        desktop_notify(msg)
    for t in get_due_soon(tasks):
        notifications.append(format_notification(t, "due_soon"))
    return notifications
