"""Date and time utilities."""
from datetime import datetime, timezone, timedelta

def parse_date(date_str):
    formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S+00:00", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"]
    for fmt in formats:
        try: return datetime.strptime(date_str, fmt)
        except ValueError: continue
    raise ValueError(f"Unable to parse date: {date_str}")

def format_relative(date_str):
    dt = parse_date(date_str) if isinstance(date_str, str) else date_str
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    seconds = (now - dt).total_seconds()
    if seconds < 60: return "just now"
    elif seconds < 3600: return f"{int(seconds // 60)}m ago"
    elif seconds < 86400: return f"{int(seconds // 3600)}h ago"
    elif seconds < 604800: return f"{int(seconds // 86400)}d ago"
    else: return f"{int(seconds // 604800)}w ago"

def get_due_date_info(due_date_str):
    due = parse_date(due_date_str)
    now = datetime.now(timezone.utc)
    if due.tzinfo is None: due = due.replace(tzinfo=timezone.utc)
    diff = due - now
    return {"due_date": due.isoformat(), "is_overdue": diff.total_seconds() < 0, "is_today": diff.days == 0 and diff.total_seconds() > 0, "days_until": diff.days, "relative": format_relative(due_date_str)}

def get_week_range(date=None):
    if date is None: date = datetime.now(timezone.utc)
    start = date - timedelta(days=date.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return start, end
