"""Error sentry for capturing operation failures."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class CapturedError:
    """A captured error occurrence."""
    signature: str
    error_type: str
    message: str
    context: Dict = field(default_factory=dict)
    count: int = 1
    first_seen: str = ""
    last_seen: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.first_seen:
            self.first_seen = now
        if not self.last_seen:
            self.last_seen = now


class ErrorSentry:
    """Captures, deduplicates, and retains recent errors."""
    def __init__(self, max_distinct: int = 100, max_recent: int = 500):
        self._by_signature: Dict[str, CapturedError] = {}
        self._recent: List[CapturedError] = []
        self._max_distinct = max_distinct
        self._max_recent = max_recent

    @staticmethod
    def make_signature(error: BaseException, context: Dict = None) -> str:
        """Stable signature: exception type + context keys."""
        ctx_keys = ",".join(sorted((context or {}).keys()))
        return f"{type(error).__name__}|{ctx_keys}"

    def capture(self, error: BaseException, context: Dict = None) -> CapturedError:
        """Capture an error; deduplicates by signature."""
        sig = self.make_signature(error, context)
        existing = self._by_signature.get(sig)
        now = datetime.now(timezone.utc).isoformat()
        if existing:
            existing.count += 1
            existing.last_seen = now
            existing.context.update(context or {})
            return existing
        captured = CapturedError(
            signature=sig, error_type=type(error).__name__,
            message=str(error)[:500], context=dict(context or {}))
        self._by_signature[sig] = captured
        if len(self._by_signature) > self._max_distinct:
            oldest = min(self._by_signature.values(), key=lambda c: c.last_seen)
            del self._by_signature[oldest.signature]
        self._recent.append(captured)
        if len(self._recent) > self._max_recent:
            self._recent.pop(0)
        return captured

    def top_errors(self, n: int = 5) -> List[CapturedError]:
        return sorted(self._by_signature.values(), key=lambda c: -c.count)[:n]

    def recent(self, n: int = 20) -> List[CapturedError]:
        return self._recent[-n:]

    def distinct_count(self) -> int:
        return len(self._by_signature)

    def total_count(self) -> int:
        return sum(c.count for c in self._by_signature.values())

    def find(self, signature: str) -> Optional[CapturedError]:
        return self._by_signature.get(signature)

    def clear(self):
        self._by_signature.clear()
        self._recent.clear()


def sentry_report(sentry: ErrorSentry) -> Dict:
    return {"distinct": sentry.distinct_count(),
            "total": sentry.total_count(),
            "top": [{"type": c.error_type, "count": c.count,
                     "message": c.message[:80]}
                    for c in sentry.top_errors(3)]}
