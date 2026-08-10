"""Tag taxonomy management and validation."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class TagDefinition:
    """A tag definition in the taxonomy."""
    id: int
    name: str
    category: str = "general"
    color: str = "#999999"
    description: str = ""
    synonyms: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def matches(self, text):
        text_lower = text.lower().strip()
        if text_lower == self.name.lower():
            return True
        return text_lower in [s.lower() for s in self.synonyms]

    @property
    def all_forms(self):
        return [self.name] + self.synonyms


class TagTaxonomy:
    """Manages a tag taxonomy with categories."""

    def __init__(self):
        self._tags = {}
        self._by_name = {}
        self._next_id = 1

    def register(self, name, category="general", color="#999999",
                 description="", synonyms=None):
        tag = TagDefinition(id=self._next_id, name=name, category=category,
                            color=color, description=description, synonyms=synonyms or [])
        self._tags[self._next_id] = tag
        self._by_name[name.lower()] = self._next_id
        for syn in (synonyms or []):
            self._by_name[syn.lower()] = self._next_id
        self._next_id += 1
        return tag

    def get(self, tag_id):
        return self._tags.get(tag_id)

    def find(self, name):
        tag_id = self._by_name.get(name.lower().strip())
        return self._tags.get(tag_id) if tag_id else None

    def remove(self, tag_id):
        if tag_id in self._tags:
            tag = self._tags[tag_id]
            del self._tags[tag_id]
            self._by_name.pop(tag.name.lower(), None)
            for syn in tag.synonyms:
                self._by_name.pop(syn.lower(), None)
            return True
        return False

    def all_tags(self):
        return sorted(self._tags.values(), key=lambda t: t.name)

    def by_category(self, category):
        return [t for t in self._tags.values() if t.category == category]

    def categories(self):
        return sorted(set(t.category for t in self._tags.values()))

    def count(self):
        return len(self._tags)

    def validate_tag(self, name):
        return self.find(name) is not None

    def validate_tags(self, tags):
        return [t for t in tags if not self.validate_tag(t)]


def normalize_tag(tag, taxonomy):
    definition = taxonomy.find(tag)
    return definition.name if definition else tag


def normalize_tags(tags, taxonomy):
    seen = set()
    result = []
    for tag in tags:
        normalized = normalize_tag(tag, taxonomy)
        if normalized.lower() not in seen:
            seen.add(normalized.lower())
            result.append(normalized)
    return result


def suggest_tags(text, taxonomy, max_suggestions=5):
    text_lower = text.lower()
    scores = {}
    for tag in taxonomy.all_tags():
        score = 0
        if tag.name.lower() in text_lower:
            score += 3
        for syn in tag.synonyms:
            if syn.lower() in text_lower:
                score += 2
        if score > 0:
            scores[tag.name] = score
    sorted_tags = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [t[0] for t in sorted_tags[:max_suggestions]]


def tag_taxonomy_summary(taxonomy):
    return {"total_tags": taxonomy.count(), "categories": len(taxonomy.categories()),
            "category_breakdown": {c: len(taxonomy.by_category(c)) for c in taxonomy.categories()},
            "total_synonyms": sum(len(t.synonyms) for t in taxonomy.all_tags())}


def default_taxonomy():
    taxonomy = TagTaxonomy()
    defaults = [
        ("bug", "type", "#d73a4a", "A defect", ["defect", "issue", "error"]),
        ("feature", "type", "#a2eeef", "New functionality", ["enhancement", "improvement"]),
        ("refactor", "type", "#d876e3", "Code restructuring", ["cleanup", "restructure"]),
        ("docs", "type", "#0075ca", "Documentation", ["documentation", "readme"]),
        ("urgent", "priority", "#e99695", "High urgency", ["asap", "immediate"]),
        ("backend", "area", "#c5def5", "Backend changes", ["server", "api"]),
        ("frontend", "area", "#fef2c0", "Frontend changes", ["ui", "client"]),
        ("devops", "area", "#1d76db", "DevOps changes", ["ci", "deploy", "infra"]),
    ]
    for name, category, color, desc, synonyms in defaults:
        taxonomy.register(name, category, color, desc, synonyms)
    return taxonomy
