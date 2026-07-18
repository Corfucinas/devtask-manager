"""Recurring task support."""
from datetime import datetime, timezone, timedelta
from .models import Task, Status

RECURRING_TYPES = {"daily": 1, "weekly": 7, "monthly": 30, "quarterly": 90}

def generate_recurring(base_task, recurrence_type, count=10):
    if recurrence_type not in RECURRING_TYPES:
        raise ValueError(f"Unknown recurrence: {recurrence_type}")
    days = RECURRING_TYPES[recurrence_type]
    instances = []
    base_date = datetime.now(timezone.utc)
    for i in range(1, count + 1):
        due_date = base_date + timedelta(days=days * i)
        task = Task(id=0, title=f"{base_task.title} (#{i})", description=base_task.description, priority=base_task.priority, tags=base_task.tags + [recurrence_type])
        task._due_date = due_date.isoformat()
        instances.append(task)
    return instances

def get_recurring_tag(task):
    for tag in task.tags:
        if tag in RECURRING_TYPES:
            return tag
    return None
