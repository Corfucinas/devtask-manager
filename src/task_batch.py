"""Task batch processor with parallel execution."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class BatchResult:
    """Result of a batch processing operation."""
    total: int = 0
    success: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)
    results: List[Any] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""

    @property
    def success_rate(self) -> float:
        if self.total == 0: return 0.0
        return round(self.success / self.total * 100, 1)

    @property
    def duration_seconds(self) -> float:
        if not self.started_at or not self.finished_at:
            return 0.0
        try:
            start = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(self.finished_at.replace("Z", "+00:00"))
            return round((end - start).total_seconds(), 2)
        except (ValueError, TypeError):
            return 0.0


class BatchProcessor:
    """Processes tasks in batches."""
    def __init__(self, batch_size: int = 10):
        self._batch_size = batch_size
        self._history: List[BatchResult] = []

    def process_batch(self, tasks: List, operation: Callable, batch_size: int = None) -> BatchResult:
        """Process all tasks through an operation."""
        bs = batch_size or self._batch_size
        result = BatchResult(total=len(tasks), started_at=datetime.now(timezone.utc).isoformat())
        for task in tasks:
            try:
                op_result = operation(task)
                result.success += 1
                result.results.append(op_result)
            except Exception as e:
                result.failed += 1
                result.errors.append(str(e))
                result.results.append(None)
        result.finished_at = datetime.now(timezone.utc).isoformat()
        self._history.append(result)
        return result

    def process_chunks(self, tasks: List, operation: Callable, chunk_size: int = None) -> List[BatchResult]:
        """Process tasks in chunks, returning a result per chunk."""
        bs = chunk_size or self._batch_size
        results = []
        for i in range(0, len(tasks), bs):
            chunk = tasks[i:i+bs]
            result = self.process_batch(chunk, operation)
            results.append(result)
        return results

    def history(self) -> List[BatchResult]:
        return list(self._history)

    def clear_history(self):
        self._history = []

    def total_processed(self) -> int:
        return sum(r.total for r in self._history)

    def total_success(self) -> int:
        return sum(r.success for r in self._history)


def batch_report(result: BatchResult) -> Dict:
    """Generate a batch execution report."""
    return {
        "total": result.total,
        "success": result.success,
        "failed": result.failed,
        "success_rate": result.success_rate,
        "error_count": len(result.errors),
        "duration_seconds": result.duration_seconds,
        "errors": result.errors[:5],
    }


def batch_summary(processor: BatchProcessor) -> Dict:
    """Generate a processor summary."""
    return {
        "total_batches": len(processor.history()),
        "total_processed": processor.total_processed(),
        "total_success": processor.total_success(),
        "overall_success_rate": round(
            processor.total_success() / max(processor.total_processed(), 1) * 100, 1
        ),
    }


def default_processor():
    """Create a default batch processor."""
    return BatchProcessor(batch_size=10)
