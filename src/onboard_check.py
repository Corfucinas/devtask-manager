"""Onboarding checklist and progress tracking."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ChecklistItem:
    """A single onboarding checklist item."""
    id: int
    name: str
    description: str = ""
    required: bool = True
    completed: bool = False
    completed_at: Optional[str] = None
    completed_by: Optional[str] = None
    category: str = "general"


class OnboardingChecklist:
    """Manages onboarding checklist for a new team member."""
    def __init__(self, member_name: str = ""):
        self.member_name = member_name
        self._items: Dict[int, ChecklistItem] = {}
        self._next_id = 1
        self.created_at = datetime.now(timezone.utc).isoformat()

    def add(self, name, description="", required=True, category="general"):
        item = ChecklistItem(id=self._next_id, name=name, description=description,
                             required=required, category=category)
        self._items[self._next_id] = item
        self._next_id += 1
        return item

    def get(self, item_id):
        return self._items.get(item_id)

    def find_by_name(self, name):
        for item in self._items.values():
            if item.name.lower() == name.lower():
                return item
        return None

    def complete(self, item_id, completed_by=None):
        item = self._items.get(item_id)
        if item:
            item.completed = True
            item.completed_at = datetime.now(timezone.utc).isoformat()
            item.completed_by = completed_by
            return True
        return False

    def uncomplete(self, item_id):
        item = self._items.get(item_id)
        if item:
            item.completed = False
            item.completed_at = None
            item.completed_by = None
            return True
        return False

    def remove(self, item_id):
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False

    def all_items(self):
        return list(self._items.values())

    def by_category(self, category):
        return [item for item in self._items.values() if item.category == category]

    def completed_items(self):
        return [item for item in self._items.values() if item.completed]

    def pending_items(self):
        return [item for item in self._items.values() if not item.completed]

    def required_pending(self):
        return [item for item in self._items.values() if item.required and not item.completed]

    def count(self):
        return len(self._items)

    def completed_count(self):
        return len(self.completed_items())

    def progress(self):
        total = self.count()
        if total == 0: return 0.0
        return round(self.completed_count() / total * 100, 1)

    def required_progress(self):
        required = [item for item in self._items.values() if item.required]
        if not required: return 100.0
        done = sum(1 for item in required if item.completed)
        return round(done / len(required) * 100, 1)

    def is_complete(self):
        return len(self.required_pending()) == 0

    def categories(self):
        return sorted(set(item.category for item in self._items.values()))


def onboarding_report(checklist):
    """Generate a full onboarding report."""
    return {
        "member": checklist.member_name,
        "total_items": checklist.count(),
        "completed": checklist.completed_count(),
        "pending": len(checklist.pending_items()),
        "required_pending": len(checklist.required_pending()),
        "progress": checklist.progress(),
        "required_progress": checklist.required_progress(),
        "is_complete": checklist.is_complete(),
        "categories": {
            cat: {
                "total": len(checklist.by_category(cat)),
                "completed": sum(1 for item in checklist.by_category(cat) if item.completed),
            }
            for cat in checklist.categories()
        },
    }


def default_checklist(member_name=""):
    """Create a checklist with common default onboarding items."""
    cl = OnboardingChecklist(member_name)
    cl.add("Create GitHub account", "Set up your GitHub account", category="setup")
    cl.add("Clone the repository", "Clone the main repo", category="setup")
    cl.add("Set up development environment", "Install dependencies and tools", category="setup")
    cl.add("Read the README", "Read the project README", category="docs", required=False)
    cl.add("Read the CONTRIBUTING guide", "Read contributing guidelines", category="docs")
    cl.add("Set up SSH keys", "Configure SSH for GitHub", category="setup")
    cl.add("Join the team chat", "Join Slack/Discord", category="communication", required=False)
    cl.add("Complete first task", "Pick up and complete your first task", category="first_task")
    cl.add("Submit first PR", "Create your first pull request", category="first_task")
    cl.add("Get code review", "Have your code reviewed by a senior dev", category="first_task")
    return cl
