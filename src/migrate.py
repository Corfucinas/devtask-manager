"""Migration utilities for task data format changes."""
import json
from .models import Task, Priority, Status

MIGRATIONS = [{"version": 1, "description": "Initial schema"}, {"version": 2, "description": "Add tags field"}, {"version": 3, "description": "Add priority enum"}, {"version": 4, "description": "Add updated_at timestamp"}]

def get_current_version(data):
    if not data: return 4
    first = data[0] if isinstance(data, list) else data
    if "tags" not in first: return 1
    if "priority" not in first: return 2
    if "updated_at" not in first: return 3
    return 4

def migrate_v1_to_v2(data):
    for t in data:
        if "tags" not in t: t["tags"] = []
    return data

def migrate_v2_to_v3(data):
    priority_map = {"0": "low", "1": "medium", "2": "high", "3": "critical"}
    for t in data:
        if "priority" not in t: t["priority"] = "medium"
        elif t["priority"] in priority_map: t["priority"] = priority_map[t["priority"]]
    return data

def migrate_v3_to_v4(data):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    for t in data:
        if "updated_at" not in t: t["updated_at"] = t.get("created_at", now)
    return data

def migrate(data, target_version=4):
    current = get_current_version(data)
    while current < target_version:
        if current == 1: data = migrate_v1_to_v2(data)
        elif current == 2: data = migrate_v2_to_v3(data)
        elif current == 3: data = migrate_v3_to_v4(data)
        current += 1
    return data

def needs_migration(data, target_version=4):
    return get_current_version(data) < target_version
