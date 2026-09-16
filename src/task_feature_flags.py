"""Feature flags for gradual rollout."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Flag:
    """A single feature flag."""
    name: str
    enabled: bool = False
    rollout_percent: int = 0          # 0-100
    user_overrides: Dict[str, bool] = field(default_factory=dict)
    description: str = ""

    def is_enabled_for(self, user: str = None) -> bool:
        """Override wins; else rollout %; else global default."""
        if user is not None and user in self.user_overrides:
            return self.user_overrides[user]
        if not self.enabled:
            return False
        if self.rollout_percent >= 100:
            return True
        if self.rollout_percent <= 0:
            return False
        if user is None:
            return False
        return _stable_hash(user, self.name) % 100 < self.rollout_percent


def _stable_hash(user: str, salt: str) -> int:
    """Deterministic bucket hash for a user+flag pair."""
    import hashlib
    digest = hashlib.sha256(f"{salt}:{user}".encode()).hexdigest()
    return int(digest, 16)


class FeatureFlags:
    """Registry of feature flags."""
    def __init__(self):
        self._flags: Dict[str, Flag] = {}

    def define(self, name: str, enabled: bool = False, rollout: int = 0,
               description: str = "") -> Flag:
        flag = Flag(name=name, enabled=enabled, rollout_percent=max(0, min(100, rollout)),
                    description=description)
        self._flags[name] = flag
        return flag

    def get(self, name: str) -> Optional[Flag]:
        return self._flags.get(name)

    def enable(self, name: str) -> bool:
        f = self._flags.get(name)
        if f:
            f.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        f = self._flags.get(name)
        if f:
            f.enabled = False
            return True
        return False

    def kill_switch(self, name: str) -> bool:
        """Hard-disable: global off AND rollout zero AND overrides cleared."""
        f = self._flags.get(name)
        if not f:
            return False
        f.enabled = False
        f.rollout_percent = 0
        f.user_overrides.clear()
        return True

    def set_rollout(self, name: str, percent: int) -> bool:
        f = self._flags.get(name)
        if not f:
            return False
        f.rollout_percent = max(0, min(100, percent))
        return True

    def override_for(self, name: str, user: str, value: bool) -> bool:
        f = self._flags.get(name)
        if not f:
            return False
        f.user_overrides[user] = value
        return True

    def is_enabled(self, name: str, user: str = None) -> bool:
        f = self._flags.get(name)
        return f.is_enabled_for(user) if f else False

    def flag_names(self) -> List[str]:
        return sorted(self._flags.keys())

    def flag_count(self) -> int:
        return len(self._flags)


def flags_report(ff: FeatureFlags) -> Dict:
    return {"total": ff.flag_count(),
            "enabled": sum(1 for f in ff._flags.values() if f.enabled),
            "flags": {n: {"enabled": f.enabled, "rollout": f.rollout_percent,
                          "overrides": len(f.user_overrides)}
                      for n, f in sorted(ff._flags.items())}}
