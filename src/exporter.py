"""Export tasks to different formats."""
import json
import csv
import io
from .models import Task

def export_json(tasks):
    return json.dumps([t.to_dict() for t in tasks], indent=2)

def export_csv(tasks):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "title", "description", "priority", "status", "tags", "created_at", "updated_at"])
    for t in tasks:
        writer.writerow([t.id, t.title, t.description, t.priority.value, t.status.value, ";".join(t.tags), t.created_at, t.updated_at])
    return output.getvalue()

def export_markdown(tasks):
    lines = ["| ID | Title | Priority | Status | Tags |", "|----|-------|----------|--------|------|"]
    for t in tasks:
        tags = ", ".join(t.tags) if t.tags else "-"
        lines.append(f"| {t.id} | {t.title} | {t.priority.value} | {t.status.value} | {tags} |")
    return "\n".join(lines)

def export_tasks(tasks, format="json"):
    exporters = {"json": export_json, "csv": export_csv, "markdown": export_markdown}
    if format not in exporters:
        raise ValueError(f"Unknown format: {format}. Use: {', '.join(exporters.keys())}")
    return exporters[format](tasks)
