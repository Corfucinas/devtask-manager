"""Task normalizer for data cleaning."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import re


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


@dataclass
class NormalizerConfig:
    """Configuration for task normalization."""
    trim_whitespace: bool = True
    lowercase_tags: bool = True
    deduplicate_tags: bool = True
    sort_tags: bool = True
    normalize_priority: bool = True
    normalize_status: bool = True
    strip_html: bool = True
    max_title_length: int = 200
    max_description_length: int = 10000


def _clean_text(text, strip_html=True, max_length=None):
    """Clean a text field."""
    if not text:
        return ""
    text = str(text).strip()
    if strip_html:
        text = re.sub(r"<[^>]+>", "", text)
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip() + "..."
    return text


def _clean_tags(tags, lowercase=True, deduplicate=True, sort=True):
    """Clean tag list."""
    if not tags:
        return []
    cleaned = [str(t).strip() for t in tags if t]
    if lowercase:
        cleaned = [t.lower() for t in cleaned]
    if deduplicate:
        seen = set()
        result = []
        for t in cleaned:
            if t not in seen:
                seen.add(t)
                result.append(t)
        cleaned = result
    if sort:
        cleaned = sorted(cleaned)
    return cleaned


PRIORITY_MAP = {
    "urgent": "critical", "blocker": "critical", "p0": "critical",
    "important": "high", "p1": "high",
    "normal": "medium", "p2": "medium",
    "minor": "low", "p3": "low", "trivial": "low",
}

STATUS_MAP = {
    "open": "todo", "new": "todo", "pending": "todo",
    "working": "in-progress", "wip": "in-progress", "started": "in-progress",
    "resolved": "done", "closed": "done", "complete": "done", "completed": "done",
    "waiting": "review", "qa": "review",
}


def normalize_task(task, config=None):
    """Normalize a single task. Returns dict of changed fields."""
    if config is None:
        config = NormalizerConfig()
    changes = {}
    
    if config.trim_whitespace or config.strip_html:
        title = getattr(task, "title", "") or ""
        cleaned = _clean_text(title, config.strip_html, config.max_title_length)
        if cleaned != title:
            task.title = cleaned
            changes["title"] = {"from": title, "to": cleaned}
        
        desc = getattr(task, "description", "") or ""
        cleaned_desc = _clean_text(desc, config.strip_html, config.max_description_length)
        if cleaned_desc != desc:
            task.description = cleaned_desc
            changes["description"] = {"from": desc, "to": cleaned_desc}
    
    tags = getattr(task, "tags", []) or []
    cleaned_tags = _clean_tags(tags, config.lowercase_tags, config.deduplicate_tags, config.sort_tags)
    if cleaned_tags != list(tags):
        task.tags = cleaned_tags
        changes["tags"] = {"from": list(tags), "to": cleaned_tags}
    
    if config.normalize_priority:
        priority = _get_priority(task)
        normalized = PRIORITY_MAP.get(priority.lower(), priority.lower())
        if normalized != priority and hasattr(task.priority, "value"):
            from src.models import Priority
            task.priority = Priority(normalized)
            changes["priority"] = {"from": priority, "to": normalized}
        elif normalized != priority:
            task.priority = normalized
            changes["priority"] = {"from": priority, "to": normalized}
    
    if config.normalize_status:
        status = _get_status(task)
        normalized = STATUS_MAP.get(status.lower(), status)
        if normalized != status and hasattr(task.status, "value"):
            from src.models import Status
            task.status = Status(normalized)
            changes["status"] = {"from": status, "to": normalized}
        elif normalized != status:
            task.status = normalized
            changes["status"] = {"from": status, "to": normalized}
    
    assignee = getattr(task, "assignee", None)
    if assignee and isinstance(assignee, str):
        cleaned_assignee = assignee.strip()
        if cleaned_assignee != assignee:
            task.assignee = cleaned_assignee
            changes["assignee"] = {"from": assignee, "to": cleaned_assignee}
    
    return changes


def normalize_batch(tasks, config=None):
    """Normalize multiple tasks."""
    results = []
    for task in tasks:
        changes = normalize_task(task, config)
        results.append({"task_id": getattr(task, "id", None), "changes": changes})
    return results


def normalization_report(tasks, config=None):
    """Generate a normalization report."""
    if config is None:
        config = NormalizerConfig()
    results = normalize_batch(tasks, config)
    total_changes = sum(len(r["changes"]) for r in results)
    changed_tasks = sum(1 for r in results if r["changes"])
    by_field = {}
    for r in results:
        for field in r["changes"]:
            by_field[field] = by_field.get(field, 0) + 1
    return {
        "total_tasks": len(tasks),
        "changed_tasks": changed_tasks,
        "unchanged_tasks": len(tasks) - changed_tasks,
        "total_changes": total_changes,
        "by_field": by_field,
        "config": {
            "trim_whitespace": config.trim_whitespace,
            "lowercase_tags": config.lowercase_tags,
            "normalize_priority": config.normalize_priority,
            "normalize_status": config.normalize_status,
        },
    }


def default_config():
    """Return default normalizer config."""
    return NormalizerConfig()
