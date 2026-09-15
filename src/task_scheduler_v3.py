"""Priority-aware job scheduler."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import heapq


@dataclass
class Job:
    """A scheduled job with priority and optional dependencies."""
    id: int
    name: str
    priority: int = 0          # higher runs first
    depends_on: List[int] = field(default_factory=list)
    ready: bool = True
    run_count: int = 0

    @property
    def sort_key(self):
        return (-self.priority, self.id)


class PriorityScheduler:
    """Schedules jobs by priority, honoring dependencies."""
    def __init__(self):
        self._jobs: Dict[int, Job] = {}
        self._next_id = 1

    def add(self, name: str, priority: int = 0, depends_on: List[int] = None) -> Job:
        """Add a job; auto-blocked if dependencies not yet run."""
        deps = depends_on or []
        job = Job(id=self._next_id, name=name, priority=priority,
                  depends_on=list(deps))
        job.ready = all(self._jobs[d].run_count > 0 for d in deps if d in self._jobs) and                     all(d in self._jobs for d in deps)
        self._jobs[self._next_id] = job
        self._next_id += 1
        return job

    def remove(self, job_id: int) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def get(self, job_id: int) -> Optional[Job]:
        return self._jobs.get(job_id)

    def ready_jobs(self) -> List[Job]:
        """Return ready jobs sorted by priority (highest first)."""
        ready = [j for j in self._jobs.values() if j.ready and j.run_count == 0]
        return sorted(ready, key=lambda j: j.sort_key)

    def next_job(self) -> Optional[Job]:
        ready = self.ready_jobs()
        return ready[0] if ready else None

    def run_next(self) -> Optional[Job]:
        """Run (mark as run) the highest-priority ready job."""
        job = self.next_job()
        if job:
            job.run_count += 1
            self._unblock_dependents(job.id)
        return job

    def _unblock_dependents(self, job_id: int):
        """Mark dependents ready when their deps have all run."""
        for j in self._jobs.values():
            if job_id in j.depends_on:
                if all(self._jobs[d].run_count > 0 for d in j.depends_on if d in self._jobs):
                    j.ready = True

    def run_all(self) -> List[Job]:
        """Run all jobs in dependency/priority order."""
        run = []
        while True:
            job = self.run_next()
            if job is None:
                break
            run.append(job)
        return run

    def job_count(self) -> int:
        return len(self._jobs)

    def pending_count(self) -> int:
        return sum(1 for j in self._jobs.values() if j.run_count == 0)

    def clear(self):
        self._jobs.clear()
        self._next_id = 1


def scheduler_report(s: PriorityScheduler) -> Dict:
    return {"total_jobs": s.job_count(), "pending": s.pending_count(),
            "completed": s.job_count() - s.pending_count()}
