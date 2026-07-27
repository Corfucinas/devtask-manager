"""Command history and macro recording."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class CommandEntry:
    """A single executed command."""
    id: int
    command: str
    args: List[Any] = field(default_factory=list)
    timestamp: str = ""
    result: Optional[str] = None
    success: bool = True

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class CommandHistory:
    """Tracks executed commands for undo and replay."""

    def __init__(self, max_size: int = 100):
        self._entries: List[CommandEntry] = []
        self._next_id = 1
        self._max_size = max_size

    def record(self, command: str, args: List[Any] = None,
               result: str = None, success: bool = True) -> CommandEntry:
        """Record a executed command."""
        entry = CommandEntry(
            id=self._next_id,
            command=command,
            args=args or [],
            result=result,
            success=success,
        )
        self._entries.append(entry)
        self._next_id += 1
        if len(self._entries) > self._max_size:
            self._entries.pop(0)
        return entry

    def last(self, n: int = 1) -> List[CommandEntry]:
        """Return the last N commands."""
        if n <= 0:
            return []
        return self._entries[-n:]

    def all_entries(self) -> List[CommandEntry]:
        """Return all history entries."""
        return list(self._entries)

    def filter_by_command(self, command: str) -> List[CommandEntry]:
        """Return all entries for a specific command type."""
        return [e for e in self._entries if e.command == command]

    def filter_by_success(self, success: bool = True) -> List[CommandEntry]:
        """Return entries filtered by success status."""
        return [e for e in self._entries if e.success == success]

    def count(self) -> int:
        """Return total number of recorded commands."""
        return len(self._entries)

    def clear(self) -> None:
        """Clear all history."""
        self._entries = []
        self._next_id = 1

    def undo_last(self) -> Optional[CommandEntry]:
        """Return and remove the last command (for undo)."""
        if not self._entries:
            return None
        return self._entries.pop()

    def search(self, query: str) -> List[CommandEntry]:
        """Search command history by query string."""
        query_lower = query.lower()
        return [
            e for e in self._entries
            if query_lower in e.command.lower()
            or any(query_lower in str(a).lower() for a in e.args)
        ]

    def frequency(self) -> Dict[str, int]:
        """Return command usage frequency."""
        counts = {}
        for e in self._entries:
            counts[e.command] = counts.get(e.command, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


@dataclass
class Macro:
    """A recorded sequence of commands for replay."""
    id: int
    name: str
    commands: List[CommandEntry] = field(default_factory=list)
    created_at: str = ""
    play_count: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class MacroLibrary:
    """Manages saved command macros."""

    def __init__(self):
        self._macros: Dict[int, Macro] = {}
        self._next_id = 1

    def save(self, name: str, commands: List[CommandEntry]) -> Macro:
        """Save a sequence of commands as a macro."""
        macro = Macro(id=self._next_id, name=name, commands=list(commands))
        self._macros[self._next_id] = macro
        self._next_id += 1
        return macro

    def get(self, macro_id: int) -> Optional[Macro]:
        """Retrieve a macro by ID."""
        return self._macros.get(macro_id)

    def find_by_name(self, name: str) -> Optional[Macro]:
        """Find a macro by name."""
        for m in self._macros.values():
            if m.name.lower() == name.lower():
                return m
        return None

    def remove(self, macro_id: int) -> bool:
        """Remove a macro."""
        if macro_id in self._macros:
            del self._macros[macro_id]
            return True
        return False

    def all_macros(self) -> List[Macro]:
        """Return all macros sorted by name."""
        return sorted(self._macros.values(), key=lambda m: m.name)

    def play(self, macro_id: int) -> Optional[List[CommandEntry]]:
        """Return the command sequence for a macro and increment play count."""
        macro = self.get(macro_id)
        if not macro:
            return None
        macro.play_count += 1
        return list(macro.commands)

    def count(self) -> int:
        """Return total number of macros."""
        return len(self._macros)


def record_macro(history: CommandHistory, name: str,
                 start_id: int, end_id: int) -> Optional[Macro]:
    """Create a macro from a range of history entries."""
    entries = history.all_entries()
    selected = [e for e in entries if start_id <= e.id <= end_id]
    if not selected:
        return None
    lib = MacroLibrary()
    return lib.save(name, selected)
