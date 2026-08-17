"""Task exclusion filters for reports."""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ExclusionFilter:
    """A single exclusion filter."""
    id: int
    field: str
    operator: str  # eq, ne, in, not_in, gt, lt, contains
    value: Any

    def matches(self, task) -> bool:
        """Check if a task matches this exclusion filter."""
        attr = getattr(task, self.field, None)
        if hasattr(attr, "value"):
            attr = attr.value
        if self.operator == "eq":
            return attr == self.value
        elif self.operator == "ne":
            return attr != self.value
        elif self.operator == "in":
            return attr in (self.value or [])
        elif self.operator == "not_in":
            return attr not in (self.value or [])
        elif self.operator == "gt":
            return attr is not None and attr > self.value
        elif self.operator == "lt":
            return attr is not None and attr < self.value
        elif self.operator == "contains":
            return self.value in (attr or [])
        return False


@dataclass
class ExclusionRule:
    """A named exclusion rule combining multiple filters."""
    id: int
    name: str
    filters: List[ExclusionFilter] = field(default_factory=list)
    match_all: bool = True  # AND vs OR

    def matches(self, task) -> bool:
        """Check if task should be excluded by this rule."""
        if not self.filters:
            return False
        results = [f.matches(task) for f in self.filters]
        return all(results) if self.match_all else any(results)


class ExclusionEngine:
    """Manages exclusion rules and applies them to task lists."""
    def __init__(self):
        self._rules = {}
        self._next_id = 1

    def add_rule(self, name, filters=None, match_all=True):
        rule = ExclusionRule(id=self._next_id, name=name,
                             filters=filters or [], match_all=match_all)
        self._rules[self._next_id] = rule
        self._next_id += 1
        return rule

    def remove_rule(self, rule_id):
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get(self, rule_id):
        return self._rules.get(rule_id)

    def all_rules(self):
        return list(self._rules.values())

    def count(self):
        return len(self._rules)

    def should_exclude(self, task) -> bool:
        """Check if a task should be excluded by any rule."""
        for rule in self._rules.values():
            if rule.matches(task):
                return True
        return False

    def apply(self, tasks):
        """Return tasks that are NOT excluded."""
        return [t for t in tasks if not self.should_exclude(t)]

    def excluded(self, tasks):
        """Return tasks that ARE excluded."""
        return [t for t in tasks if self.should_exclude(t)]


def default_exclusions():
    """Create engine with common default exclusion rules."""
    engine = ExclusionEngine()
    engine.add_rule("Exclude archived", [
        ExclusionFilter(id=0, field="status", operator="eq", value="done"),
        ExclusionFilter(id=0, field="tags", operator="contains", value="archived"),
    ], match_all=True)
    engine.add_rule("Exclude completed", [
        ExclusionFilter(id=0, field="status", operator="eq", value="done"),
    ])
    return engine


def exclusion_summary(engine, tasks):
    """Generate a summary of exclusion results."""
    included = engine.apply(tasks)
    excluded = engine.excluded(tasks)
    return {"total": len(tasks), "included": len(included),
            "excluded": len(excluded), "exclusion_rate": round(len(excluded) / max(len(tasks), 1) * 100, 1)}
