"""@mention parsing and notification routing."""
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


MENTION_PATTERN = re.compile(r"@([\w\-]+)")


@dataclass
class Mention:
    """A parsed @mention in text."""
    user: str
    field: str
    position: int
    context: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


def parse_mentions(text, field_name="text"):
    if not text:
        return []
    mentions = []
    for match in MENTION_PATTERN.finditer(text):
        mentions.append(Mention(
            user=match.group(1), field=field_name, position=match.start(),
            context=text[max(0, match.start()-20):match.end()+20]))
    return mentions


def extract_mentions_from_task(task):
    mentions = []
    title = getattr(task, "title", "") or ""
    mentions.extend(parse_mentions(title, "title"))
    desc = getattr(task, "description", "") or ""
    mentions.extend(parse_mentions(desc, "description"))
    comments = getattr(task, "comments", None) or []
    for i, comment in enumerate(comments):
        text = comment.text if hasattr(comment, "text") else str(comment)
        mentions.extend(parse_mentions(text, f"comment_{i}"))
    return mentions


def unique_users(mentions):
    seen = set()
    result = []
    for m in mentions:
        if m.user not in seen:
            seen.add(m.user)
            result.append(m.user)
    return result


def route_mentions(mentions, task, notification_center=None):
    results = []
    users = unique_users(mentions)
    for user in users:
        user_mentions = [m for m in mentions if m.user == user]
        result = {"user": user, "mention_count": len(user_mentions),
                  "fields": list(set(m.field for m in user_mentions)),
                  "task_id": getattr(task, "id", None), "notified": False}
        if notification_center:
            try:
                notification_center.create("mention",
                    f"You were mentioned in task #{getattr(task, 'id', '?')}",
                    f"@{user} was mentioned", priority="normal", target_user=user)
                result["notified"] = True
            except Exception:
                result["notified"] = False
        results.append(result)
    return results


def mention_count(task):
    return len(extract_mentions_from_task(task))


def is_mentioned(task, username):
    mentions = extract_mentions_from_task(task)
    return any(m.user == username for m in mentions)


def mention_summary(tasks):
    all_mentions = []
    for task in tasks:
        all_mentions.extend(extract_mentions_from_task(task))
    user_counts = {}
    for m in all_mentions:
        user_counts[m.user] = user_counts.get(m.user, 0) + 1
    return {"total_mentions": len(all_mentions), "unique_users": len(user_counts),
            "most_mentioned": sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "tasks_with_mentions": sum(1 for t in tasks if mention_count(t) > 0)}


def replace_mentions(text, replacements):
    def replacer(match):
        username = match.group(1)
        return replacements.get(username, match.group(0))
    return MENTION_PATTERN.sub(replacer, text)
