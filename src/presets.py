"""Task preset templates for quick creation."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Preset:
    """A task creation preset with predefined attributes."""
    id: int
    name: str
    title_template: str = ""
    description_template: str = ""
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)
    default_status: str = "todo"

    def render_title(self, **kwargs) -> str:
        """Render the title template with provided values."""
        if not self.title_template:
            return kwargs.get("title", "")
        try:
            return self.title_template.format(**kwargs)
        except (KeyError, IndexError):
            return self.title_template

    def render_description(self, **kwargs) -> str:
        """Render the description template with provided values."""
        if not self.description_template:
            return kwargs.get("description", "")
        try:
            return self.description_template.format(**kwargs)
        except (KeyError, IndexError):
            return self.description_template

    def to_task_attrs(self, **kwargs) -> dict:
        """Generate task attributes from this preset."""
        return {
            "title": self.render_title(**kwargs),
            "description": self.render_description(**kwargs),
            "priority": self.priority,
            "tags": list(self.tags),
            "status": self.default_status,
        }


class PresetLibrary:
    """Manages a collection of task presets."""

    def __init__(self):
        self._presets: Dict[int, Preset] = {}
        self._next_id = 1

    def add(self, name: str, title_template: str = "", description_template: str = "",
            priority: str = "medium", tags: List[str] = None,
            default_status: str = "todo") -> Preset:
        """Add a new preset to the library."""
        preset = Preset(
            id=self._next_id,
            name=name,
            title_template=title_template,
            description_template=description_template,
            priority=priority,
            tags=tags or [],
            default_status=default_status,
        )
        self._presets[self._next_id] = preset
        self._next_id += 1
        return preset

    def get(self, preset_id: int) -> Optional[Preset]:
        """Retrieve a preset by ID."""
        return self._presets.get(preset_id)

    def find_by_name(self, name: str) -> Optional[Preset]:
        """Find a preset by name (case-insensitive)."""
        for p in self._presets.values():
            if p.name.lower() == name.lower():
                return p
        return None

    def remove(self, preset_id: int) -> bool:
        """Remove a preset by ID."""
        if preset_id in self._presets:
            del self._presets[preset_id]
            return True
        return False

    def all_presets(self) -> List[Preset]:
        """Return all presets sorted by name."""
        return sorted(self._presets.values(), key=lambda p: p.name)

    def count(self) -> int:
        """Return total number of presets."""
        return len(self._presets)

    def apply(self, preset_id: int, **kwargs) -> Optional[dict]:
        """Apply a preset and return task attributes."""
        preset = self.get(preset_id)
        if not preset:
            return None
        return preset.to_task_attrs(**kwargs)

    def apply_by_name(self, name: str, **kwargs) -> Optional[dict]:
        """Apply a preset by name and return task attributes."""
        preset = self.find_by_name(name)
        if not preset:
            return None
        return preset.to_task_attrs(**kwargs)


def default_presets() -> PresetLibrary:
    """Create a library with common default presets."""
    lib = PresetLibrary()
    defaults = [
        ("Bug", "Fix: {title}", "## Bug Report\n\n**Description:** {description}\n",
         "high", ["bug", "fix"]),
        ("Feature", "Feature: {title}", "## Feature Request\n\n**Description:** {description}\n",
         "medium", ["feature"]),
        ("Refactor", "Refactor: {title}", "## Refactor\n\n**What:** {description}\n",
         "low", ["refactor"]),
        ("Documentation", "Docs: {title}", "## Documentation\n\n**Topic:** {description}\n",
         "low", ["docs"]),
        ("Research", "Research: {title}", "## Research Task\n\n**Question:** {description}\n",
         "medium", ["research"]),
        ("Hotfix", "HOTFIX: {title}", "## Hotfix\n\n**Issue:** {description}\n",
         "critical", ["hotfix", "urgent"]),
    ]
    for name, title_tpl, desc_tpl, priority, tags in defaults:
        lib.add(name, title_tpl, desc_tpl, priority, tags)
    return lib
