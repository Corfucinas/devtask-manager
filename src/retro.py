"""Sprint retrospective action items."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class ActionItem:
    """A retrospective action item."""
    id: int
    text: str
    owner: str
    category: str = "improvement"
    resolved: bool = False
    created_at: str = ""
    resolved_at: Optional[str] = None


@dataclass
class Retro:
    """A sprint retrospective with action items."""
    id: int
    sprint_id: int
    items: List[ActionItem] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    date: str = ""
    notes: str = ""

    def __post_init__(self):
        if not self.date:
            self.date = datetime.now(timezone.utc).isoformat()


def add_action_item(retro: Retro, text: str, owner: str, category: str = "improvement") -> ActionItem:
    """Add an action item to the retrospective."""
    item_id = max((i.id for i in retro.items), default=0) + 1
    item = ActionItem(
        id=item_id,
        text=text,
        owner=owner,
        category=category,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    retro.items.append(item)
    return item


def resolve_item(retro: Retro, item_id: int) -> bool:
    """Mark an action item as resolved."""
    for item in retro.items:
        if item.id == item_id:
            item.resolved = True
            item.resolved_at = datetime.now(timezone.utc).isoformat()
            return True
    return False


def unresolved_items(retro: Retro) -> List[ActionItem]:
    """Return all unresolved action items."""
    return [i for i in retro.items if not i.resolved]


def items_by_owner(retro: Retro, owner: str) -> List[ActionItem]:
    """Return all action items assigned to a specific owner."""
    return [i for i in retro.items if i.owner == owner]


def items_by_category(retro: Retro, category: str) -> List[ActionItem]:
    """Return all action items in a specific category."""
    return [i for i in retro.items if i.category == category]


def retro_summary(retro: Retro) -> dict:
    """Generate a summary of the retrospective."""
    total = len(retro.items)
    resolved_count = sum(1 for i in retro.items if i.resolved)
    return {
        "retro_id": retro.id,
        "sprint_id": retro.sprint_id,
        "date": retro.date,
        "participants": len(retro.participants),
        "total_items": total,
        "resolved": resolved_count,
        "unresolved": total - resolved_count,
        "resolution_rate": round((resolved_count / total * 100), 1) if total > 0 else 0.0,
    }


def add_participant(retro: Retro, name: str) -> None:
    """Add a participant to the retrospective."""
    if name not in retro.participants:
        retro.participants.append(name)
