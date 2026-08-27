"""Task lifecycle manager with stage tracking."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class LifecycleStage(Enum):
    """All stages in the task lifecycle."""
    IDEA = "idea"
    BACKLOG = "backlog"
    SPRINT_PLANNING = "sprint_planning"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    DONE = "done"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


STAGE_ORDER = [
    LifecycleStage.IDEA,
    LifecycleStage.BACKLOG,
    LifecycleStage.SPRINT_PLANNING,
    LifecycleStage.TODO,
    LifecycleStage.IN_PROGRESS,
    LifecycleStage.REVIEW,
    LifecycleStage.TESTING,
    LifecycleStage.DONE,
]


STAGE_TRANSITIONS = {
    LifecycleStage.IDEA: [LifecycleStage.BACKLOG, LifecycleStage.CANCELLED],
    LifecycleStage.BACKLOG: [LifecycleStage.SPRINT_PLANNING, LifecycleStage.CANCELLED],
    LifecycleStage.SPRINT_PLANNING: [LifecycleStage.TODO, LifecycleStage.BACKLOG],
    LifecycleStage.TODO: [LifecycleStage.IN_PROGRESS, LifecycleStage.CANCELLED],
    LifecycleStage.IN_PROGRESS: [LifecycleStage.REVIEW, LifecycleStage.TODO],
    LifecycleStage.REVIEW: [LifecycleStage.TESTING, LifecycleStage.IN_PROGRESS],
    LifecycleStage.TESTING: [LifecycleStage.DONE, LifecycleStage.IN_PROGRESS],
    LifecycleStage.DONE: [LifecycleStage.ARCHIVED],
    LifecycleStage.ARCHIVED: [],
    LifecycleStage.CANCELLED: [],
}


@dataclass
class StageRecord:
    """A record of entering a lifecycle stage."""
    stage: LifecycleStage
    entered_at: str = ""
    exited_at: Optional[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if not self.entered_at:
            self.entered_at = datetime.now(timezone.utc).isoformat()


class TaskLifecycle:
    """Tracks a task through its lifecycle."""
    def __init__(self, task_id: int, initial_stage: LifecycleStage = LifecycleStage.IDEA):
        self.task_id = task_id
        self._stage: LifecycleStage = initial_stage
        self._history: List[StageRecord] = [StageRecord(stage=initial_stage)]
        self._stage_index: Dict[LifecycleStage, int] = {initial_stage: 0}

    @property
    def stage(self) -> LifecycleStage:
        return self._stage

    @property
    def is_terminal(self) -> bool:
        return not STAGE_TRANSITIONS.get(self._stage, [])

    def can_transition(self, target: LifecycleStage) -> bool:
        return target in STAGE_TRANSITIONS.get(self._stage, [])

    def valid_transitions(self) -> List[LifecycleStage]:
        return STAGE_TRANSITIONS.get(self._stage, [])

    def advance(self, target: LifecycleStage = None) -> bool:
        """Move to the next stage (or a specific valid stage)."""
        if target is None:
            transitions = self.valid_transitions()
            if not transitions:
                return False
            target = transitions[0]
        if not self.can_transition(target):
            return False
        now = datetime.now(timezone.utc).isoformat()
        if self._history:
            last = self._history[-1]
            last.exited_at = now
            if last.entered_at:
                try:
                    start = datetime.fromisoformat(last.entered_at.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(now.replace("Z", "+00:00"))
                    last.duration_seconds = (end - start).total_seconds()
                except (ValueError, TypeError):
                    pass
        record = StageRecord(stage=target)
        self._history.append(record)
        self._stage_index[target] = len(self._history) - 1
        self._stage = target
        return True

    def history(self) -> List[StageRecord]:
        return list(self._history)

    def stage_count(self) -> int:
        return len(self._history)

    def time_in_stage(self, stage: LifecycleStage) -> float:
        """Total time spent in a stage (seconds)."""
        return sum(r.duration_seconds for r in self._history if r.stage == stage)

    def total_time(self) -> float:
        """Total lifecycle time (seconds)."""
        return sum(r.duration_seconds for r in self._history)

    def has_visited(self, stage: LifecycleStage) -> bool:
        return stage in self._stage_index

    def visits_to(self, stage: LifecycleStage) -> int:
        return sum(1 for r in self._history if r.stage == stage)

    def current_duration(self) -> float:
        """Duration in current stage so far."""
        if not self._history:
            return 0.0
        last = self._history[-1]
        if not last.entered_at:
            return 0.0
        try:
            start = datetime.fromisoformat(last.entered_at.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - start).total_seconds()
        except (ValueError, TypeError):
            return 0.0

    def progress_percent(self) -> float:
        """How far through the lifecycle (0-100)."""
        if self.is_terminal:
            return 100.0
        try:
            idx = STAGE_ORDER.index(self._stage)
            return round((idx / (len(STAGE_ORDER) - 1)) * 100, 1)
        except ValueError:
            return 0.0


def lifecycle_report(lifecycle: TaskLifecycle) -> Dict:
    """Generate a full lifecycle report."""
    return {
        "task_id": lifecycle.task_id,
        "current_stage": lifecycle.stage.value,
        "is_terminal": lifecycle.is_terminal,
        "stage_count": lifecycle.stage_count(),
        "total_time_seconds": round(lifecycle.total_time(), 1),
        "current_duration_seconds": round(lifecycle.current_duration(), 1),
        "progress_percent": lifecycle.progress_percent(),
        "stages_visited": [r.stage.value for r in lifecycle.history()],
        "valid_transitions": [s.value for s in lifecycle.valid_transitions()],
    }


def batch_lifecycle_report(lifecycles: List[TaskLifecycle]) -> Dict:
    """Generate a report for multiple task lifecycles."""
    by_stage = {}
    for lc in lifecycles:
        stage = lc.stage.value
        by_stage[stage] = by_stage.get(stage, 0) + 1
    return {
        "total_tasks": len(lifecycles),
        "by_stage": by_stage,
        "terminal_count": sum(1 for lc in lifecycles if lc.is_terminal),
        "avg_progress": round(
            sum(lc.progress_percent() for lc in lifecycles) / max(len(lifecycles), 1), 1
        ),
    }
