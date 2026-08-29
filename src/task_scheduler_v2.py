"""Task scheduler with recurring and one-time jobs."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ScheduledJob:
    """A scheduled job (one-time or recurring)."""
    id: int
    name: str
    task_ids: List[int] = field(default_factory=list)
    operation: str = "notify"
    scheduled_time: str = ""
    recurring: bool = False
    interval_seconds: int = 0
    callback: Optional[Callable] = None
    enabled: bool = True
    executed_count: int = 0
    last_executed: Optional[str] = None
    next_run: Optional[str] = None
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.next_run and self.scheduled_time:
            self.next_run = self.scheduled_time

    @property
    def is_due(self) -> bool:
        """Check if this job should run now."""
        if not self.enabled:
            return False
        if not self.next_run:
            return bool(self.scheduled_time)
        try:
            next_dt = datetime.fromisoformat(self.next_run.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) >= next_dt
        except (ValueError, TypeError):
            return False

    def mark_executed(self):
        """Mark as executed and schedule next run if recurring."""
        self.executed_count += 1
        self.last_executed = datetime.now(timezone.utc).isoformat()
        if self.recurring and self.interval_seconds > 0:
            self.next_run = (datetime.now(timezone.utc) +
                            timedelta(seconds=self.interval_seconds)).isoformat()
        else:
            self.enabled = False
            self.next_run = None


class TaskSchedulerV2:
    """Manages scheduled jobs."""
    def __init__(self):
        self._jobs: Dict[int, ScheduledJob] = {}
        self._next_id = 1

    def schedule(self, name, task_ids=None, operation="notify",
                 scheduled_time=None, recurring=False, interval_seconds=0,
                 callback=None):
        """Schedule a new job."""
        if scheduled_time is None and not recurring:
            scheduled_time = datetime.now(timezone.utc).isoformat()
        job = ScheduledJob(
            id=self._next_id, name=name, task_ids=task_ids or [],
            operation=operation, scheduled_time=scheduled_time or "",
            recurring=recurring, interval_seconds=interval_seconds,
            callback=callback)
        self._jobs[self._next_id] = job
        self._next_id += 1
        return job

    def get(self, job_id):
        return self._jobs.get(job_id)

    def all_jobs(self):
        return list(self._jobs.values())

    def enabled_jobs(self):
        return [j for j in self._jobs.values() if j.enabled]

    def due_jobs(self):
        """Return jobs that are due to execute."""
        return [j for j in self._jobs.values() if j.is_due]

    def execute_due(self):
        """Execute all due jobs."""
        results = []
        for job in self.due_jobs():
            result = {"job_id": job.id, "name": job.name, "executed": False}
            if job.callback:
                try:
                    job.callback(job.task_ids, operation=job.operation)
                    result["executed"] = True
                except Exception as e:
                    result["error"] = str(e)
            else:
                result["executed"] = True
            job.mark_executed()
            results.append(result)
        return results

    def cancel(self, job_id):
        """Cancel a scheduled job."""
        if job_id in self._jobs:
            self._jobs[job_id].enabled = False
            return True
        return False

    def remove(self, job_id):
        """Remove a job entirely."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def count(self):
        return len(self._jobs)

    def recurring_count(self):
        return sum(1 for j in self._jobs.values() if j.recurring)

    def clear(self):
        self._jobs = {}
        self._next_id = 1


def scheduler_report(scheduler):
    """Generate a scheduler report."""
    return {
        "total_jobs": scheduler.count(),
        "enabled": len(scheduler.enabled_jobs()),
        "due": len(scheduler.due_jobs()),
        "recurring": scheduler.recurring_count(),
        "one_time": scheduler.count() - scheduler.recurring_count(),
    }


def default_scheduler():
    """Create a scheduler with sample jobs."""
    s = TaskSchedulerV2()
    s.schedule("Daily standup reminder", operation="notify",
               recurring=True, interval_seconds=86400)
    s.schedule("Weekly report", operation="export",
               recurring=True, interval_seconds=604800)
    return s
