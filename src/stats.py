"""Statistics and analytics for tasks."""
from .models import Task, Status, Priority
from .search import count_by_priority, group_by_status

def task_summary(tasks):
    total = len(tasks)
    by_status = group_by_status(tasks)
    by_priority = count_by_priority(tasks)
    completed = len(by_status.get("done", []))
    completion_rate = (completed / total * 100) if total > 0 else 0
    return {"total": total, "todo": len(by_status.get("todo", [])), "in_progress": len(by_status.get("in-progress", [])), "done": completed, "completion_rate": round(completion_rate, 1), "by_priority": by_priority}

def productivity_score(tasks):
    weights = {Priority.CRITICAL: 4, Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}
    return sum(weights.get(t.priority, 0) for t in tasks if t.status == Status.DONE)

def streak_info(tasks):
    done_tasks = [t for t in tasks if t.status == Status.DONE]
    if not done_tasks:
        return {"current_streak": 0, "total_completed": 0}
    dates = sorted(set(t.updated_at[:10] for t in done_tasks))
    current_streak = 1
    for i in range(len(dates) - 1, 0, -1):
        from datetime import datetime as dt
        d1 = dt.fromisoformat(dates[i-1])
        d2 = dt.fromisoformat(dates[i])
        if (d2 - d1).days == 1:
            current_streak += 1
        else:
            break
    return {"current_streak": current_streak, "total_completed": len(done_tasks)}
