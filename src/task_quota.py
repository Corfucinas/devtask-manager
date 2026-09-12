"""Task quota management for per-user limits."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class UserQuota:
    """Quota for a single user."""
    user: str
    limit: int = 10
    used: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    @property
    def is_exceeded(self) -> bool:
        return self.used >= self.limit

    @property
    def utilization(self) -> float:
        return round(self.used / max(self.limit, 1) * 100, 1)


class TaskQuota:
    """Manages per-user task quotas."""
    def __init__(self, default_limit: int = 10):
        self._quotas: Dict[str, UserQuota] = {}
        self._default_limit = default_limit

    def set_limit(self, user: str, limit: int):
        """Set a custom limit for a user."""
        if user not in self._quotas:
            self._quotas[user] = UserQuota(user=user, limit=limit)
        else:
            self._quotas[user].limit = limit

    def get_quota(self, user: str) -> UserQuota:
        """Get (or create) quota for a user."""
        if user not in self._quotas:
            self._quotas[user] = UserQuota(user=user, limit=self._default_limit)
        return self._quotas[user]

    def can_create(self, user: str) -> bool:
        """Check if user can create another task."""
        return not self.get_quota(user).is_exceeded

    def increment(self, user: str) -> bool:
        """Increment usage if quota allows."""
        quota = self.get_quota(user)
        if quota.is_exceeded:
            return False
        quota.used += 1
        return True

    def decrement(self, user: str) -> bool:
        """Decrement usage (task completed/deleted)."""
        quota = self.get_quota(user)
        if quota.used > 0:
            quota.used -= 1
            return True
        return False

    def exceeded_users(self) -> List[str]:
        """Return users who have exceeded their quota."""
        return sorted(u for u, q in self._quotas.items() if q.is_exceeded)

    def reset(self, user: str):
        """Reset a user's usage."""
        self.get_quota(user).used = 0

    def reset_all(self):
        """Reset all usage counts."""
        for quota in self._quotas.values():
            quota.used = 0

    def user_count(self) -> int:
        return len(self._quotas)


def quota_report(quota: TaskQuota) -> Dict:
    return {"total_users": quota.user_count(),
            "exceeded": len(quota.exceeded_users()),
            "by_user": {q.user: {"limit": q.limit, "used": q.used,
                                  "utilization": q.utilization}
                         for q in quota._quotas.values()}}
