"""Output formatting for task display."""
from .models import Task

COLORS = {"red": "\033[91m", "yellow": "\033[93m", "green": "\033[92m", "blue": "\033[94m", "gray": "\033[90m", "bold": "\033[1m", "reset": "\033[0m"}
PRIORITY_COLORS = {"critical": "red", "high": "yellow", "medium": "green", "low": "blue"}
STATUS_ICONS = {"todo": "[ ]", "in-progress": "[~]", "done": "[x]"}

def colorize(text, color):
    c = COLORS.get(color, "")
    r = COLORS["reset"]
    return f"{c}{text}{r}"

def format_task_line(task):
    icon = STATUS_ICONS.get(task.status.value, "[?]")
    color = PRIORITY_COLORS.get(task.priority.value, "gray")
    colored_title = colorize(task.title, color)
    tags = colorize(f" #{' #'.join(task.tags)}", "gray") if task.tags else ""
    return f"  #{task.id} {icon} {colored_title}{tags}"

def format_task_detail(task):
    lines = [f"  {colorize('ID:', 'bold')} #{task.id}", f"  {colorize('Title:', 'bold')} {task.title}", f"  {colorize('Status:', 'bold')} {task.status.value}", f"  {colorize('Priority:', 'bold')} {colorize(task.priority.value, PRIORITY_COLORS.get(task.priority.value, 'gray'))}", f"  {colorize('Tags:', 'bold')} {', '.join(task.tags) if task.tags else 'none'}", f"  {colorize('Description:', 'bold')} {task.description or 'none'}", f"  {colorize('Created:', 'bold')} {task.created_at}", f"  {colorize('Updated:', 'bold')} {task.updated_at}"]
    return "\n".join(lines)

def format_task_table(tasks):
    if not tasks:
        return "No tasks found."
    lines = [f"  {'ID':<5} {'Status':<12} {'Priority':<10} {'Title':<30} Tags", f"  {'-'*5} {'-'*12} {'-'*10} {'-'*30} ----"]
    for t in tasks:
        tags = ", ".join(t.tags) if t.tags else "-"
        lines.append(f"  #{t.id:<4} {t.status.value:<12} {t.priority.value:<10} {t.title[:30]:<30} {tags}")
    return "\n".join(lines)
