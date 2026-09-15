"""Orchestrator for end-to-end task workflows."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import time as time_module


@dataclass
class StepResult:
    """Result of executing one orchestration step."""
    name: str
    ok: bool
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    rolled_back: bool = False


@dataclass
class Step:
    """A workflow step with optional rollback."""
    name: str
    run: Callable
    rollback: Optional[Callable] = None


class Orchestrator:
    """Runs steps in order; rolls back completed steps on failure."""
    def __init__(self):
        self._steps: List[Step] = []
        self._runs: List[Dict] = []

    def add(self, name: str, run: Callable, rollback: Callable = None) -> "Orchestrator":
        self._steps.append(Step(name=name, run=run, rollback=rollback))
        return self

    def step_count(self) -> int:
        return len(self._steps)

    def execute(self, context: Dict = None) -> Dict:
        """Run all steps; on failure, roll back completed steps in reverse."""
        context = dict(context or {})
        completed: List[StepResult] = []
        failed: Optional[StepResult] = None
        for step in self._steps:
            start = time_module.time()
            try:
                result = step.run(context)
                sr = StepResult(name=step.name, ok=True, result=result,
                                duration_ms=round((time_module.time() - start) * 1000, 2))
                completed.append(sr)
            except Exception as e:
                sr = StepResult(name=step.name, ok=False, error=str(e),
                                duration_ms=round((time_module.time() - start) * 1000, 2))
                failed = sr
                break
        if failed:
            for i in range(len(completed) - 1, -1, -1):
                step = self._steps[i]
                step_result = completed[i]
                if step.rollback:
                    try:
                        step.rollback(context)
                        step_result.rolled_back = True
                    except Exception:
                        pass
        run_record = {
            "success": failed is None,
            "steps": [{"name": s.name, "ok": s.ok, "error": s.error,
                        "duration_ms": s.duration_ms, "rolled_back": s.rolled_back}
                       for s in completed],
            "failed_step": failed.name if failed else None,
            "total_ms": round(sum(s.duration_ms for s in completed), 2),
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }
        self._runs.append(run_record)
        return run_record

    def runs(self) -> List[Dict]:
        return list(self._runs)

    def run_count(self) -> int:
        return len(self._runs)

    def success_rate(self) -> float:
        if not self._runs:
            return 0.0
        ok = sum(1 for r in self._runs if r["success"])
        return round(ok / len(self._runs) * 100, 1)

    def clear_history(self):
        self._runs.clear()


def orchestrator_report(o: Orchestrator) -> Dict:
    return {"steps": o.step_count(), "runs": o.run_count(),
            "success_rate": o.success_rate()}
