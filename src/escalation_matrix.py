"""Escalation matrix with severity and routing."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class EscalationLevel:
    """A single escalation level in the matrix."""
    level: int
    name: str
    contact: str
    response_time_hours: float = 24.0
    notification_channels: List[str] = field(default_factory=lambda: ["email"])


@dataclass
class EscalationRecord:
    """A record of an escalation event."""
    id: int
    task_id: int
    level: int
    contact: str
    reason: str = ""
    timestamp: str = ""
    acknowledged: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class EscalationMatrix:
    """Manages escalation levels and records."""
    def __init__(self):
        self._levels: Dict[int, EscalationLevel] = {}
        self._records: List[EscalationRecord] = {}
        self._next_id = 1

    def add_level(self, level, name, contact, response_time_hours=24.0,
                  notification_channels=None):
        esc_level = EscalationLevel(
            level=level, name=name, contact=contact,
            response_time_hours=response_time_hours,
            notification_channels=notification_channels or ["email"])
        self._levels[level] = esc_level
        return esc_level

    def get_level(self, level):
        return self._levels.get(level)

    def all_levels(self):
        return sorted(self._levels.values(), key=lambda l: l.level)

    def level_count(self):
        return len(self._levels)

    def escalate(self, task_id, level=1, reason=""):
        """Escalate a task to a specific level."""
        esc_level = self.get_level(level)
        if not esc_level:
            return None
        record = EscalationRecord(
            id=self._next_id, task_id=task_id, level=level,
            contact=esc_level.contact, reason=reason)
        self._records[self._next_id] = record
        self._next_id += 1
        return record

    def auto_escalate(self, task, severity="medium"):
        """Auto-escalate based on severity mapping."""
        severity_map = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        level = severity_map.get(severity, 0)
        if level == 0:
            return None
        return self.escalate(getattr(task, "id", 0), level=level,
                              reason=f"Auto-escalated: {severity}")

    def records(self):
        return list(self._records.values())

    def records_for_task(self, task_id):
        return [r for r in self._records.values() if r.task_id == task_id]

    def acknowledge(self, record_id):
        if record_id in self._records:
            self._records[record_id].acknowledged = True
            return True
        return False

    def unacknowledged(self):
        return [r for r in self._records.values() if not r.acknowledged]

    def record_count(self):
        return len(self._records)

    def clear_records(self):
        self._records = {}
        self._next_id = 1


def escalation_report(matrix):
    """Generate an escalation summary report."""
    records = matrix.records()
    return {
        "total_levels": matrix.level_count(),
        "total_escalations": len(records),
        "unacknowledged": len(matrix.unacknowledged()),
        "by_level": {level: sum(1 for r in records if r.level == level)
                      for level in matrix._levels.keys()},
        "levels": [{"level": l.level, "name": l.name, "contact": l.contact,
                     "response_time_hours": l.response_time_hours}
                    for l in matrix.all_levels()],
    }


def default_escalation_matrix():
    """Create a matrix with common default escalation levels."""
    matrix = EscalationMatrix()
    matrix.add_level(1, "Team Lead", "tech_lead", response_time_hours=8)
    matrix.add_level(2, "Engineering Manager", "eng_manager", response_time_hours=4,
                     notification_channels=["email", "slack"])
    matrix.add_level(3, "VP Engineering", "vp_eng", response_time_hours=2,
                     notification_channels=["email", "slack", "phone"])
    return matrix
