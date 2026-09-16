"""Garbage collection for orphaned task data."""
from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass
class GCResult:
    """Outcome of one GC pass."""
    orphan_comments: int = 0
    orphan_tags: int = 0
    orphan_subtasks: int = 0
    purged: int = 0
    dry_run: bool = True

    @property
    def total_orphans(self) -> int:
        return self.orphan_comments + self.orphan_tags + self.orphan_subtasks


def _existing_ids(tasks: List) -> Set[int]:
    return {getattr(t, "id", i) for i, t in enumerate(tasks)}


def find_orphans(tasks: List, comments: List, tag_links: List,
                 subtask_links: List) -> GCResult:
    """Identify references to non-existent tasks."""
    existing = _existing_ids(tasks)
    orphan_comments = [c for c in comments
                        if getattr(c, "task_id", None) not in existing]
    orphan_tags = [l for l in tag_links
                   if getattr(l, "task_id", None) not in existing]
    orphan_subtasks = [s for s in subtask_links
                       if getattr(s, "parent_id", None) not in existing
                       or getattr(s, "child_id", None) not in existing]
    return GCResult(orphan_comments=len(orphan_comments),
                    orphan_tags=len(orphan_tags),
                    orphan_subtasks=len(orphan_subtasks),
                    dry_run=True)


def purge_orphans(tasks: List, comments: List, tag_links: List,
                  subtask_links: List, dry_run: bool = True) -> GCResult:
    """Remove orphaned references (or count them if dry_run)."""
    existing = _existing_ids(tasks)
    orphan_c = [c for c in comments if getattr(c, "task_id", None) not in existing]
    orphan_t = [l for l in tag_links if getattr(l, "task_id", None) not in existing]
    orphan_s = [s for s in subtask_links
                if getattr(s, "parent_id", None) not in existing
                or getattr(s, "child_id", None) not in existing]
    result = GCResult(orphan_comments=len(orphan_c), orphan_tags=len(orphan_t),
                      orphan_subtasks=len(orphan_s), dry_run=dry_run)
    if dry_run:
        return result
    result.purged = len(orphan_c) + len(orphan_t) + len(orphan_s)
    # In-place list filtering (caller sees purged lists)
    comments[:] = [c for c in comments if c not in orphan_c]
    tag_links[:] = [l for l in tag_links if l not in orphan_t]
    subtask_links[:] = [s for s in subtask_links if s not in orphan_s]
    return result


def gc_report(result: GCResult) -> Dict:
    return {"orphan_comments": result.orphan_comments,
            "orphan_tags": result.orphan_tags,
            "orphan_subtasks": result.orphan_subtasks,
            "total_orphans": result.total_orphans,
            "purged": result.purged,
            "mode": "dry-run" if result.dry_run else "purge"}
