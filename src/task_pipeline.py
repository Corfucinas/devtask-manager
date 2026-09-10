"""Task pipeline for chaining operations."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class PipelineStep:
    """A single step in the pipeline."""
    id: int
    name: str
    operation: Callable
    enabled: bool = True
    executed: bool = False
    error: Optional[str] = None
    input_count: int = 0
    output_count: int = 0
    execution_time_ms: float = 0.0


class TaskPipeline:
    """Chains operations on task lists."""
    def __init__(self):
        self._steps: List[PipelineStep] = []
        self._next_id = 1
        self._results: List[Dict] = []

    def pipe(self, name: str, operation: Callable) -> "TaskPipeline":
        """Add an operation to the pipeline."""
        step = PipelineStep(id=self._next_id, name=name, operation=operation)
        self._steps.append(step)
        self._next_id += 1
        return self

    def filter(self, predicate: Callable) -> "TaskPipeline":
        """Add a filter step."""
        return self.pipe("filter", lambda tasks: [t for t in tasks if predicate(t)])

    def sort(self, key: Callable, reverse: bool = False) -> "TaskPipeline":
        """Add a sort step."""
        return self.pipe("sort", lambda tasks: sorted(tasks, key=key, reverse=reverse))

    def limit(self, n: int) -> "TaskPipeline":
        """Add a limit step."""
        return self.pipe("limit", lambda tasks: tasks[:n])

    def map(self, transform: Callable) -> "TaskPipeline":
        """Add a map step."""
        return self.pipe("map", lambda tasks: [transform(t) for t in tasks])

    def deduplicate(self, key: Callable = None) -> "TaskPipeline":
        """Add a deduplication step."""
        def dedup(tasks):
            seen = set()
            result = []
            for t in tasks:
                k = key(t) if key else t
                if k not in seen:
                    seen.add(k)
                    result.append(t)
            return result
        return self.pipe("deduplicate", dedup)

    def execute(self, tasks: List) -> List:
        """Execute all pipeline steps."""
        current = list(tasks)
        for step in self._steps:
            step.input_count = len(current)
            start = datetime.now(timezone.utc)
            try:
                current = step.operation(current)
                step.output_count = len(current)
                step.error = None
            except Exception as e:
                step.error = str(e)
                step.output_count = 0
            end = datetime.now(timezone.utc)
            step.execution_time_ms = round((end - start).total_seconds() * 1000, 2)
            step.executed = True
        self._results.append({
            "input_count": len(tasks),
            "output_count": len(current),
            "steps_executed": sum(1 for s in self._steps if s.executed),
        })
        return current

    def steps(self) -> List[PipelineStep]:
        return list(self._steps)

    def step_count(self) -> int:
        return len(self._steps)

    def clear(self):
        self._steps = []
        self._results = []
        self._next_id = 1

    def executed_steps(self) -> List[PipelineStep]:
        return [s for s in self._steps if s.executed]

    def had_errors(self) -> bool:
        return any(s.error for s in self._steps)

    def error_steps(self) -> List[PipelineStep]:
        return [s for s in self._steps if s.error]

    def total_time_ms(self) -> float:
        return sum(s.execution_time_ms for s in self._steps)

    def reset_execution(self):
        """Reset execution state but keep steps."""
        for step in self._steps:
            step.executed = False
            step.error = None
            step.input_count = 0
            step.output_count = 0
            step.execution_time_ms = 0.0


def pipeline_report(pipeline: TaskPipeline) -> Dict:
    """Generate a pipeline report."""
    steps = pipeline.steps()
    return {
        "total_steps": pipeline.step_count(),
        "executed_steps": len(pipeline.executed_steps()),
        "had_errors": pipeline.had_errors(),
        "error_steps": [s.name for s in pipeline.error_steps()],
        "total_time_ms": pipeline.total_time_ms(),
        "steps": [{"name": s.name, "executed": s.executed, "error": s.error,
                   "input": s.input_count, "output": s.output_count,
                   "time_ms": s.execution_time_ms}
                  for s in steps],
    }


def default_pipeline() -> TaskPipeline:
    """Create a pipeline with common defaults."""
    p = TaskPipeline()
    return p
