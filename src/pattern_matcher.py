"""Pattern matching for task auto-categorization."""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Pattern:
    """A categorization pattern."""
    id: int
    name: str
    regex: str
    category: str
    confidence: float = 0.8
    tags: List[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self):
        self._compiled = None

    @property
    def compiled(self):
        if self._compiled is None:
            self._compiled = re.compile(self.regex, re.IGNORECASE)
        return self._compiled

    def matches(self, text: str) -> bool:
        """Check if this pattern matches text."""
        if not self.enabled or not text:
            return False
        return bool(self.compiled.search(text))


class PatternMatcher:
    """Applies patterns to categorize tasks."""
    def __init__(self):
        self._patterns: Dict[int, Pattern] = {}
        self._next_id = 1

    def add(self, name, regex, category, confidence=0.8, tags=None):
        """Add a new pattern."""
        p = Pattern(id=self._next_id, name=name, regex=regex, category=category,
                    confidence=confidence, tags=tags or [])
        self._patterns[self._next_id] = p
        self._next_id += 1
        return p

    def remove(self, pattern_id):
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            return True
        return False

    def get(self, pattern_id):
        return self._patterns.get(pattern_id)

    def all_patterns(self):
        return list(self._patterns.values())

    def enabled_patterns(self):
        return [p for p in self._patterns.values() if p.enabled]

    def count(self):
        return len(self._patterns)

    def enable(self, pattern_id):
        if pattern_id in self._patterns:
            self._patterns[pattern_id].enabled = True
            return True
        return False

    def disable(self, pattern_id):
        if pattern_id in self._patterns:
            self._patterns[pattern_id].enabled = False
            return True
        return False

    def categorize(self, task):
        """Auto-categorize a task based on its content."""
        title = getattr(task, "title", "") or ""
        desc = getattr(task, "description", "") or ""
        text = f"{title} {desc}"

        matches = []
        for pattern in self.enabled_patterns():
            if pattern.matches(text):
                matches.append({
                    "pattern_id": pattern.id,
                    "pattern_name": pattern.name,
                    "category": pattern.category,
                    "confidence": pattern.confidence,
                    "tags": pattern.tags,
                })

        if not matches:
            return {"categorized": False, "category": None, "matches": []}

        matches.sort(key=lambda m: m["confidence"], reverse=True)
        best = matches[0]
        return {"categorized": True, "category": best["category"],
                "confidence": best["confidence"], "tags": best["tags"],
                "all_matches": matches}

    def categorize_batch(self, tasks):
        """Categorize multiple tasks."""
        return [self.categorize(t) for t in tasks]

    def suggest_tags(self, task):
        """Suggest tags for a task based on patterns."""
        result = self.categorize(task)
        return result.get("tags", []) if result.get("categorized") else []


def pattern_report(matcher, tasks):
    """Generate a categorization report."""
    results = matcher.categorize_batch(tasks)
    categorized = sum(1 for r in results if r.get("categorized"))
    categories = {}
    for r in results:
        if r.get("categorized"):
            cat = r["category"]
            categories[cat] = categories.get(cat, 0) + 1
    return {
        "total_tasks": len(tasks),
        "categorized": categorized,
        "uncategorized": len(tasks) - categorized,
        "categorization_rate": round(categorized / max(len(tasks), 1) * 100, 1),
        "categories": categories,
        "total_patterns": matcher.count(),
    }


def default_patterns():
    """Create a matcher with common default patterns."""
    m = PatternMatcher()
    m.add("Bug pattern", r"\b(bug|fix|error|crash|broken|fail)\b", "bug", 0.9, ["bug"])
    m.add("Feature pattern", r"\b(feature|add|implement|create|new)\b", "feature", 0.7, ["feature"])
    m.add("Refactor pattern", r"\b(refactor|cleanup|restructure|optimize)\b", "refactor", 0.8, ["refactor"])
    m.add("Docs pattern", r"\b(docs?|documentation|readme|guide)\b", "documentation", 0.85, ["docs"])
    m.add("Test pattern", r"\b(test|testing|spec|coverage)\b", "testing", 0.75, ["test"])
    m.add("Security pattern", r"\b(security|vulnerability|cve|exploit|auth)\b", "security", 0.9, ["security"])
    return m
