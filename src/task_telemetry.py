"""Telemetry spans for tracing task operations."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import time as time_module


class SpanStatus:
    OK = "ok"
    ERROR = "error"


@dataclass
class Span:
    """A traced operation span."""
    id: int
    name: str
    started_at: float
    ended_at: Optional[float] = None
    status: str = SpanStatus.OK
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        if self.ended_at is None:
            return round((time_module.time() - self.started_at) * 1000, 2)
        return round((self.ended_at - self.started_at) * 1000, 2)

    @property
    def is_open(self) -> bool:
        return self.ended_at is None

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def add_event(self, name: str, **data):
        self.events.append({"name": name,
                            "at_ms": round((time_module.time() - self.started_at) * 1000, 2),
                            **data})

    def end(self, status: str = SpanStatus.OK):
        if self.ended_at is None:
            self.ended_at = time_module.time()
            self.status = status


class TelemetryHub:
    """Creates and collects spans."""
    def __init__(self, max_spans: int = 2000):
        self._spans: List[Span] = []
        self._next_id = 1
        self._max = max_spans

    def start_span(self, name: str, **attributes) -> Span:
        span = Span(id=self._next_id, name=name, started_at=time_module.time())
        span.attributes.update(attributes)
        self._spans.append(span)
        self._next_id += 1
        if len(self._spans) > self._max:
            self._spans.pop(0)
        return span

    def end_span(self, span: Span, status: str = SpanStatus.OK):
        span.end(status)

    def spans(self, name: str = None) -> List[Span]:
        if name:
            return [s for s in self._spans if s.name == name]
        return list(self._spans)

    def error_spans(self) -> List[Span]:
        return [s for s in self._spans if s.status == SpanStatus.ERROR]

    def span_count(self) -> int:
        return len(self._spans)

    def avg_duration(self, name: str = None) -> float:
        spans = [s for s in self.spans(name) if not s.is_open]
        if not spans:
            return 0.0
        return round(sum(s.duration_ms for s in spans) / len(spans), 2)

    def clear(self):
        self._spans.clear()
        self._next_id = 1


def trace_summary(hub: TelemetryHub) -> Dict:
    spans = hub.spans()
    closed = [s for s in spans if not s.is_open]
    by_name: Dict[str, int] = {}
    for s in spans:
        by_name[s.name] = by_name.get(s.name, 0) + 1
    return {"total_spans": len(spans),
            "errors": len(hub.error_spans()),
            "avg_duration_ms": hub.avg_duration(),
            "by_operation": dict(sorted(by_name.items(), key=lambda kv: -kv[1]))}
