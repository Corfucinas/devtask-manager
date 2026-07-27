"""User preference management with typed settings."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Preference:
    """A single user preference with type and default."""
    key: str
    value: Any
    type: str
    default: Any = None
    description: str = ""

    def reset_to_default(self) -> None:
        """Reset value to the default."""
        self.value = self.default

    @property
    def is_default(self) -> bool:
        """Check if current value equals the default."""
        return self.value == self.default


class PreferenceStore:
    """Manages user preferences with type validation."""

    def __init__(self):
        self._prefs: Dict[str, Preference] = {}

    def register(self, key: str, default: Any, pref_type: str, description: str = "") -> Preference:
        """Register a new preference with a default value."""
        pref = Preference(key=key, value=default, type=pref_type,
                          default=default, description=description)
        self._prefs[key] = pref
        return pref

    def get(self, key: str) -> Optional[Any]:
        """Get a preference value by key."""
        pref = self._prefs.get(key)
        return pref.value if pref else None

    def set(self, key: str, value: Any) -> bool:
        """Set a preference value. Returns False if key doesn't exist or type mismatch."""
        pref = self._prefs.get(key)
        if not pref:
            return False
        if not self._validate_type(value, pref.type):
            return False
        pref.value = value
        return True

    def reset(self, key: str) -> bool:
        """Reset a preference to its default value."""
        pref = self._prefs.get(key)
        if not pref:
            return False
        pref.reset_to_default()
        return True

    def reset_all(self) -> None:
        """Reset all preferences to defaults."""
        for pref in self._prefs.values():
            pref.reset_to_default()

    def get_all(self) -> Dict[str, Any]:
        """Return all preference values as a dict."""
        return {k: p.value for k, p in self._prefs.items()}

    def list_preferences(self) -> List[Preference]:
        """Return all registered preferences sorted by key."""
        return sorted(self._prefs.values(), key=lambda p: p.key)

    def has(self, key: str) -> bool:
        """Check if a preference key exists."""
        return key in self._prefs

    def count(self) -> int:
        """Return total number of registered preferences."""
        return len(self._prefs)

    def changed_preferences(self) -> List[Preference]:
        """Return preferences whose value differs from the default."""
        return [p for p in self._prefs.values() if not p.is_default]

    def to_dict(self) -> dict:
        """Serialize all preferences to a plain dict."""
        return {
            k: {"value": p.value, "type": p.type, "default": p.default,
                "description": p.description}
            for k, p in self._prefs.items()
        }

    @staticmethod
    def _validate_type(value: Any, expected: str) -> bool:
        """Validate that a value matches the expected type."""
        if expected == "string":
            return isinstance(value, str)
        elif expected == "int":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected == "float":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected == "bool":
            return isinstance(value, bool)
        elif expected == "list":
            return isinstance(value, list)
        return True


def default_preferences() -> PreferenceStore:
    """Create a store with sensible default preferences."""
    store = PreferenceStore()
    defaults = [
        ("theme", "dark", "string", "UI color theme"),
        ("language", "en", "string", "Display language"),
        ("timezone", "UTC", "string", "Timezone for date display"),
        ("items_per_page", 25, "int", "Tasks shown per page"),
        ("auto_save", True, "bool", "Automatically save changes"),
        ("notification_enabled", True, "bool", "Enable notifications"),
        ("default_priority", "medium", "string", "Default priority for new tasks"),
        ("compact_view", False, "bool", "Use compact task list view"),
        ("confirm_delete", True, "bool", "Ask before deleting tasks"),
        ("refresh_interval", 30, "int", "Dashboard refresh interval in seconds"),
    ]
    for key, default, ptype, desc in defaults:
        store.register(key, default, ptype, desc)
    return store
