"""Import tasks from external formats."""
import json
import csv
import io
from .models import Task, Priority, Status

def import_json(data, store):
    """Import tasks from JSON string into store."""
    tasks = json.loads(data)
    imported = []
    for t in tasks:
        task = store.create(title=t.get("title", "Imported task"), description=t.get("description", ""), priority=t.get("priority", "medium"), tags=t.get("tags", []))
        if t.get("status") == "done":
            store.update(task.id, status="done")
        imported.append(task)
    return imported

def import_csv(data, store):
    """Import tasks from CSV string into store."""
    reader = csv.DictReader(io.StringIO(data))
    imported = []
    for row in reader:
        tags = [t.strip() for t in row.get("tags", "").split(";") if t.strip()]
        task = store.create(title=row.get("title", "Imported"), description=row.get("description", ""), priority=row.get("priority", "medium"), tags=tags)
        if row.get("status") == "done":
            store.update(task.id, status="done")
        imported.append(task)
    return imported

def import_tasks(data, format="json", store=None):
    importers = {"json": import_json, "csv": import_csv}
    if format not in importers:
        raise ValueError(f"Unknown format: {format}")
    if store is None:
        raise ValueError("Store is required")
    return importers[format](data, store)
