"""Release versioning and changelog generation."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class Release:
    """A software release with version and included tasks."""
    version: str
    date: str = ""
    tasks: List[int] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self):
        if not self.date:
            self.date = datetime.now(timezone.utc).isoformat()


def bump_version(current: str, bump_type: str = "patch") -> str:
    """Bump a semantic version string. Supports major, minor, patch."""
    parts = current.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version: {current}. Expected format: X.Y.Z")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Use: major, minor, patch")
    return f"{major}.{minor}.{patch}"


def generate_changelog(tasks, version: str) -> str:
    """Auto-generate a changelog from completed tasks."""
    lines = [f"## {version} ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})", ""]
    features = []
    fixes = []
    docs = []
    others = []

    for t in tasks:
        status = t.status.value if hasattr(t.status, "value") else t.status
        if status != "done":
            continue
        title = getattr(t, "title", str(t))
        tags = set(getattr(t, "tags", []) or [])
        if "feature" in tags:
            features.append(title)
        elif "bug" in tags:
            fixes.append(title)
        elif "docs" in tags:
            docs.append(title)
        else:
            others.append(title)

    if features:
        lines.append("### Features")
        for f in features:
            lines.append(f"- {f}")
        lines.append("")
    if fixes:
        lines.append("### Bug Fixes")
        for f in fixes:
            lines.append(f"- {f}")
        lines.append("")
    if docs:
        lines.append("### Documentation")
        for d in docs:
            lines.append(f"- {d}")
        lines.append("")
    if others:
        lines.append("### Other Changes")
        for o in others:
            lines.append(f"- {o}")
        lines.append("")

    return "\n".join(lines)


def release_notes(release: Release, tasks) -> str:
    """Generate formatted release notes for a specific release."""
    changelog = generate_changelog(tasks, release.version)
    task_count = len(release.tasks)
    header = f"# Release {release.version}\nDate: {release.date}\nTasks included: {task_count}\n"
    return f"{header}\n{changelog}"


def compare_versions(v1: str, v2: str) -> int:
    """Compare two semantic versions. Returns -1, 0, or 1."""
    p1 = [int(x) for x in v1.split(".")]
    p2 = [int(x) for x in v2.split(".")]
    for a, b in zip(p1, p2):
        if a < b:
            return -1
        if a > b:
            return 1
    return 0


def is_prerelease(version: str) -> bool:
    """Check if a version string indicates a pre-release."""
    return "-" in version
