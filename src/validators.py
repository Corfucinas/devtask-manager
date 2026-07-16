"""Input validation for DevTask Manager."""
import re

def validate_title(title):
    if not title or not title.strip():
        raise ValueError("Title cannot be empty")
    if len(title) > 200:
        raise ValueError("Title must be 200 characters or less")
    return title.strip()

def validate_tags(tags):
    if not tags:
        return []
    validated = []
    for tag in tags:
        if not re.match(r'^[a-zA-Z0-9-]+$', tag):
            raise ValueError(f"Invalid tag: {tag}")
        if len(tag) > 30:
            raise ValueError(f"Tag too long: {tag}")
        validated.append(tag.lower())
    return validated

def validate_id(task_id):
    if not isinstance(task_id, int) or task_id < 1:
        raise ValueError(f"Invalid task ID: {task_id}")
    return task_id
