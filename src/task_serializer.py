"""Task serializer for JSON and CSV export."""
import json, csv, io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


@dataclass
class SerializerConfig:
    fields: List[str] = field(default_factory=lambda: [
        "id", "title", "description", "priority", "status",
        "tags", "assignee", "due_date", "created_at", "updated_at"
    ])
    include_none: bool = True
    date_format: str = "iso"


def task_to_dict(task, config=None):
    if config is None:
        config = SerializerConfig()
    result = {}
    for field_name in config.fields:
        if field_name == "priority":
            val = _get_priority(task)
        elif field_name == "status":
            val = _get_status(task)
        else:
            val = getattr(task, field_name, None)
        if val is None and not config.include_none:
            continue
        if isinstance(val, list):
            val = list(val)
        result[field_name] = val
    return result


def serialize_tasks(tasks, fmt="json", config=None):
    if config is None:
        config = SerializerConfig()
    dicts = [task_to_dict(t, config) for t in tasks]
    if fmt == "json":
        return json.dumps(dicts, indent=2, default=str)
    elif fmt == "csv":
        output = io.StringIO()
        if dicts:
            writer = csv.DictWriter(output, fieldnames=config.fields, extrasaction="ignore")
            writer.writeheader()
            for d in dicts:
                row = {k: json.dumps(v) if isinstance(v, (list, dict)) else v
                       for k, v in d.items()}
                writer.writerow(row)
        return output.getvalue()
    elif fmt == "dict":
        return dicts
    raise ValueError(f"Unsupported format: {fmt}")


def deserialize_tasks(data, fmt="json"):
    if fmt == "json":
        return json.loads(data)
    elif fmt == "csv":
        reader = csv.DictReader(io.StringIO(data))
        results = []
        for row in reader:
            parsed = {}
            for k, v in row.items():
                try:
                    parsed[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    parsed[k] = v
            results.append(parsed)
        return results
    raise ValueError(f"Unsupported format: {fmt}")


def serialize_single(task, fmt="json", config=None):
    if fmt == "json":
        return json.dumps(task_to_dict(task, config), indent=2, default=str)
    return serialize_tasks([task], fmt, config)


def serialization_report(tasks, fmt="json"):
    config = SerializerConfig()
    data = serialize_tasks(tasks, fmt, config)
    return {
        "format": fmt,
        "task_count": len(tasks),
        "field_count": len(config.fields),
        "output_size_bytes": len(data),
        "output_size_kb": round(len(data) / 1024, 2),
        "avg_task_size": round(len(data) / max(len(tasks), 1), 1),
        "fields": config.fields,
    }


def compact_serialize(tasks):
    dicts = [task_to_dict(t) for t in tasks]
    return json.dumps(dicts, default=str, separators=(",", ":"))


def default_config():
    return SerializerConfig()
