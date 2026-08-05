"""Team availability and time-off tracking."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


@dataclass
class TimeOff:
    """A time-off record for a team member."""
    id: int
    member: str
    start_date: str
    end_date: str
    reason: str = "vacation"
    approved: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def includes_date(self, date_str):
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        start = datetime.fromisoformat(self.start_date.replace("Z", "+00:00")).date()
        end = datetime.fromisoformat(self.end_date.replace("Z", "+00:00")).date()
        return start <= date <= end

    @property
    def duration_days(self):
        start = datetime.fromisoformat(self.start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.end_date.replace("Z", "+00:00"))
        return (end - start).days + 1


class TimeOffManager:
    """Manages time-off records for team members."""

    def __init__(self):
        self._records: Dict[int, TimeOff] = {}
        self._next_id = 1

    def request(self, member, start_date, end_date, reason="vacation"):
        record = TimeOff(id=self._next_id, member=member, start_date=start_date,
                         end_date=end_date, reason=reason)
        self._records[self._next_id] = record
        self._next_id += 1
        return record

    def approve(self, record_id):
        record = self._records.get(record_id)
        if record:
            record.approved = True
            return True
        return False

    def reject(self, record_id):
        if record_id in self._records:
            del self._records[record_id]
            return True
        return False

    def get(self, record_id):
        return self._records.get(record_id)

    def for_member(self, member):
        return [r for r in self._records.values() if r.member == member]

    def approved_records(self):
        return [r for r in self._records.values() if r.approved]

    def pending_records(self):
        return [r for r in self._records.values() if not r.approved]

    def on_time_off(self, member, date_str):
        for record in self.for_member(member):
            if record.approved and record.includes_date(date_str):
                return True
        return False

    def available_members(self, members, date_str):
        return [m for m in members if not self.on_time_off(m, date_str)]

    def unavailable_members(self, members, date_str):
        return [m for m in members if self.on_time_off(m, date_str)]

    def count(self):
        return len(self._records)

    def all_records(self):
        return list(self._records.values())

    def upcoming_time_off(self, days=30):
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days)
        results = []
        for record in self.approved_records():
            start = datetime.fromisoformat(record.start_date.replace("Z", "+00:00"))
            if now <= start <= cutoff:
                results.append(record)
        return sorted(results, key=lambda r: r.start_date)


def is_available(manager, member, date_str):
    return not manager.on_time_off(member, date_str)


def availability_report(manager, members, date_str):
    available = manager.available_members(members, date_str)
    unavailable = manager.unavailable_members(members, date_str)
    return {"date": date_str, "total_members": len(members),
            "available": len(available), "unavailable": len(unavailable),
            "available_members": available, "unavailable_members": unavailable,
            "availability_rate": round(len(available) / max(len(members), 1) * 100, 1)}


def team_capacity_date(manager, members, date_str):
    available = manager.available_members(members, date_str)
    return {"date": date_str, "total_members": len(members),
            "available_members": len(available),
            "capacity_percentage": round(len(available) / max(len(members), 1) * 100, 1),
            "understaffed": len(available) < len(members) * 0.5}


def conflict_check(manager, member, start_date, end_date):
    start = datetime.fromisoformat(start_date.replace("Z", "+00:00")).date()
    end = datetime.fromisoformat(end_date.replace("Z", "+00:00")).date()
    for record in manager.for_member(member):
        if not record.approved:
            continue
        rec_start = datetime.fromisoformat(record.start_date.replace("Z", "+00:00")).date()
        rec_end = datetime.fromisoformat(record.end_date.replace("Z", "+00:00")).date()
        if start <= rec_end and end >= rec_start:
            return True
    return False
