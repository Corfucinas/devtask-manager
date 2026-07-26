"""Threaded comments on tasks."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Comment:
    """A comment or reply on a task."""
    id: int
    author: str
    text: str
    parent_id: Optional[int] = None
    created_at: str = ""
    edited: bool = False
    edited_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


def add_comment(task, author: str, text: str, parent_id: int = None) -> Comment:
    """Add a comment or reply to a task."""
    if not hasattr(task, "comments") or task.comments is None:
        task.comments = []
    comment_id = max((c.id for c in task.comments), default=0) + 1
    comment = Comment(id=comment_id, author=author, text=text, parent_id=parent_id)
    task.comments.append(comment)
    return comment


def edit_comment(task, comment_id: int, new_text: str) -> bool:
    """Edit an existing comment."""
    for c in get_comments(task):
        if c.id == comment_id:
            c.text = new_text
            c.edited = True
            c.edited_at = datetime.now(timezone.utc).isoformat()
            return True
    return False


def delete_comment(task, comment_id: int) -> bool:
    """Delete a comment and all its replies."""
    if not hasattr(task, "comments") or not task.comments:
        return False
    to_delete = {comment_id}
    changed = True
    while changed:
        changed = False
        for c in task.comments:
            if c.parent_id in to_delete and c.id not in to_delete:
                to_delete.add(c.id)
                changed = True
    before = len(task.comments)
    task.comments = [c for c in task.comments if c.id not in to_delete]
    return len(task.comments) < before


def get_comments(task) -> List[Comment]:
    """Return all comments on a task."""
    if not hasattr(task, "comments") or not task.comments:
        return []
    return list(task.comments)


def comment_thread(task, comment_id: int) -> List[Comment]:
    """Get a comment and all its replies (thread)."""
    comments = get_comments(task)
    result = []
    queue = [comment_id]
    while queue:
        current = queue.pop(0)
        for c in comments:
            if c.id == current or c.parent_id == current:
                if c not in result:
                    result.append(c)
                    if c.id not in queue and c.id != current:
                        queue.append(c.id)
    return result


def flatten_comments(task) -> List[Comment]:
    """Return all comments in chronological order."""
    return sorted(get_comments(task), key=lambda c: c.created_at)


def reply_count(task, comment_id: int) -> int:
    """Count direct replies to a comment."""
    return sum(1 for c in get_comments(task) if c.parent_id == comment_id)


def top_level_comments(task) -> List[Comment]:
    """Return only top-level comments (no parent)."""
    return [c for c in get_comments(task) if c.parent_id is None]


def comments_by_author(task, author: str) -> List[Comment]:
    """Return all comments by a specific author."""
    return [c for c in get_comments(task) if c.author == author]


def comment_count(task) -> int:
    """Return total number of comments on a task."""
    return len(get_comments(task))


def build_tree(task) -> List[dict]:
    """Build a nested tree structure of comments and replies."""
    comments = get_comments(task)
    by_id = {c.id: {"comment": c, "replies": []} for c in comments}
    roots = []
    for c in comments:
        node = by_id[c.id]
        if c.parent_id and c.parent_id in by_id:
            by_id[c.parent_id]["replies"].append(node)
        else:
            roots.append(node)
    return roots
