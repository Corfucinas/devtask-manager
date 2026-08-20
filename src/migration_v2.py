"""Data migration framework with versioning."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional


@dataclass
class Migration:
    """A single data migration."""
    version: int
    name: str
    up: Callable
    down: Optional[Callable] = None
    description: str = ""
    applied_at: Optional[str] = None

    def apply(self, context=None):
        """Apply this migration."""
        try:
            self.up(context)
            self.applied_at = datetime.now(timezone.utc).isoformat()
            return True
        except Exception:
            return False

    def revert(self, context=None):
        """Revert this migration."""
        if not self.down:
            return False
        try:
            self.down(context)
            self.applied_at = None
            return True
        except Exception:
            return False


class MigrationRunner:
    """Manages and executes data migrations."""
    def __init__(self):
        self._migrations: Dict[int, Migration] = {}
        self._current_version: int = 0
        self._history: List[dict] = []

    def register(self, version, name, up, down=None, description=""):
        """Register a new migration."""
        migration = Migration(version=version, name=name, up=up, down=down,
                              description=description)
        self._migrations[version] = migration
        return migration

    def get(self, version):
        return self._migrations.get(version)

    def all_migrations(self):
        return sorted(self._migrations.values(), key=lambda m: m.version)

    def pending(self):
        """Return migrations not yet applied."""
        return [m for m in self.all_migrations()
                if m.version > self._current_version and m.applied_at is None]

    def applied(self):
        """Return applied migrations."""
        return [m for m in self._migrations.values() if m.applied_at is not None]

    def current_version(self):
        return self._current_version

    def count(self):
        return len(self._migrations)

    def migrate(self, context=None):
        """Run all pending migrations."""
        results = []
        for migration in self.pending():
            success = migration.apply(context)
            results.append({"version": migration.version, "name": migration.name,
                            "success": success})
            if success:
                self._current_version = migration.version
                self._history.append({"action": "up", "version": migration.version,
                                      "timestamp": migration.applied_at})
        return results

    def rollback(self, target_version, context=None):
        """Rollback to a specific version."""
        applied = sorted(self.applied(), key=lambda m: -m.version)
        results = []
        for migration in applied:
            if migration.version <= target_version:
                break
            success = migration.revert(context)
            results.append({"version": migration.version, "name": migration.name,
                            "success": success})
            if success:
                self._current_version = target_version
                self._history.append({"action": "down", "version": migration.version,
                                      "timestamp": datetime.now(timezone.utc).isoformat()})
        return results

    def history(self):
        return list(self._history)

    def is_up_to_date(self):
        return len(self.pending()) == 0


def migration_report(runner):
    """Generate a migration status report."""
    return {
        "current_version": runner.current_version(),
        "total_migrations": runner.count(),
        "applied": len(runner.applied()),
        "pending": len(runner.pending()),
        "up_to_date": runner.is_up_to_date(),
        "history_count": len(runner.history()),
    }
