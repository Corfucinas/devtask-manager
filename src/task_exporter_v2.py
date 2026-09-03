"""Task exporter with multiple output formats."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import io, json, csv


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


@dataclass
class ExportConfig:
    """Configuration for task export."""
    format: str = "json"
    fields: List[str] = field(default_factory=lambda: [
        "id", "title", "description", "priority", "status", "tags", "assignee"
    ])
    include_header: bool = True
    include_metadata: bool = False
    indent: int = 2
    pretty: bool = True


def _task_to_dict(task, config):
    result = {}
    for f in config.fields:
        if f == "priority":
            result[f] = _get_priority(task)
        elif f == "status":
            result[f] = _get_status(task)
        else:
            val = getattr(task, f, None)
            if isinstance(val, list):
                val = list(val)
            result[f] = val
    if config.include_metadata:
        result["_exported_at"] = datetime.now(timezone.utc).isoformat()
    return result


def _export_json(tasks, config):
    dicts = [_task_to_dict(t, config) for t in tasks]
    return json.dumps(dicts, indent=config.indent, default=str)


def _export_csv(tasks, config):
    output = io.StringIO()
    if tasks:
        writer = csv.DictWriter(output, fieldnames=config.fields, extrasaction="ignore")
        if config.include_header:
            writer.writeheader()
        for t in tasks:
            d = _task_to_dict(t, config)
            row = {k: json.dumps(v) if isinstance(v, (list, dict)) else str(v)
                   for k, v in d.items()}
            writer.writerow(row)
    return output.getvalue()


def _export_xml(tasks, config):
    lines = ["<?xml version='1.0' encoding='UTF-8'?>", "<tasks>"]
    for t in tasks:
        d = _task_to_dict(t, config)
        lines.append("  <task>")
        for k, v in d.items():
            lines.append(f"    <{k}>{v if v is not None else ''}</{k}>")
        lines.append("  </task>")
    lines.append("</tasks>")
    return "\n".join(lines)


def _export_markdown(tasks, config):
    lines = []
    if config.include_header:
        lines.append("# Task Export")
        lines.append("")
        lines.append(f"Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Count: {len(tasks)}")
        lines.append("")
    headers = config.fields
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for t in tasks:
        d = _task_to_dict(t, config)
        vals = [str(d.get(h, "")) for h in headers]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _export_yaml(tasks, config):
    """Simple YAML-like output."""
    lines = []
    for t in tasks:
        d = _task_to_dict(t, config)
        lines.append("-")
        for k, v in d.items():
            if isinstance(v, list):
                lines.append(f"  {k}:")
                for item in v:
                    lines.append(f"    - {item}")
            else:
                lines.append(f"  {k}: {v if v is not None else ''}")
    return "\n".join(lines)


def export_tasks(tasks, config=None):
    """Export tasks to the specified format."""
    if config is None:
        config = ExportConfig()
    fmt = config.format.lower()
    if fmt == "json":
        return _export_json(tasks, config)
    elif fmt == "csv":
        return _export_csv(tasks, config)
    elif fmt == "xml":
        return _export_xml(tasks, config)
    elif fmt in ("markdown", "md"):
        return _export_markdown(tasks, config)
    elif fmt == "yaml":
        return _export_yaml(tasks, config)
    raise ValueError(f"Unsupported format: {fmt}")


def export_single(task, config=None):
    """Export a single task."""
    if config is None:
        config = ExportConfig()
    return export_tasks([task], config)


def export_report(tasks, config=None):
    """Generate an export report."""
    if config is None:
        config = ExportConfig()
    data = export_tasks(tasks, config)
    return {
        "format": config.format,
        "task_count": len(tasks),
        "field_count": len(config.fields),
        "output_size_bytes": len(data),
        "output_size_kb": round(len(data) / 1024, 2),
        "avg_size_per_task": round(len(data) / max(len(tasks), 1), 1),
        "fields": config.fields,
    }


def default_config() -> ExportConfig:
    return ExportConfig()
