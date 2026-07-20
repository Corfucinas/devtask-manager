"""Task notes and comments."""
from datetime import datetime, timezone


def add_note(task, text, author="user"):
    """Append a note to a task."""
    if not hasattr(task, "notes") or task.notes is None:
        task.notes = []
    note = {
        "id": len(task.notes) + 1,
        "text": text,
        "author": author,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    task.notes.append(note)
    return note


def get_notes(task):
    """Retrieve all notes for a task in chronological order."""
    if not hasattr(task, "notes") or not task.notes:
        return []
    return list(task.notes)


def search_notes(tasks, query):
    """Full-text search across all task notes."""
    query_lower = query.lower()
    results = []
    for task in tasks:
        for note in get_notes(task):
            if query_lower in note["text"].lower():
                results.append((task, note))
    return results


def note_count(task):
    """Return the number of notes attached to a task."""
    if not hasattr(task, "notes") or not task.notes:
        return 0
    return len(task.notes)


def delete_note(task, note_id):
    """Remove a note by its ID. Returns True if deleted."""
    if not hasattr(task, "notes") or not task.notes:
        return False
    before = len(task.notes)
    task.notes = [n for n in task.notes if n["id"] != note_id]
    return len(task.notes) < before


def notes_by_author(tasks, author):
    """Find all notes by a specific author across tasks."""
    results = []
    for task in tasks:
        for note in get_notes(task):
            if note["author"] == author:
                results.append((task, note))
    return results
