"""Tag cloud generator for task visualization."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import math


@dataclass
class TagCloudItem:
    """A single tag in the cloud."""
    name: str
    count: int = 0
    weight: float = 0.0  # 0-1 normalized
    size: int = 12  # font size in px
    color: str = "#999"

    @property
    def importance(self) -> str:
        """Return importance label based on weight."""
        if self.weight >= 0.75: return "high"
        elif self.weight >= 0.5: return "medium"
        elif self.weight >= 0.25: return "low"
        else: return "minimal"


def _get_tags(task):
    return set(getattr(task, "tags", []) or [])


def generate_tag_cloud(tasks: List, min_count: int = 1) -> List[TagCloudItem]:
    """Generate a tag cloud from task tags."""
    counts: Dict[str, int] = {}
    for task in tasks:
        for tag in _get_tags(task):
            counts[tag] = counts.get(tag, 0) + 1
    if not counts:
        return []
    max_count = max(counts.values())
    min_count_val = min(counts.values())
    range_count = max(max_count - min_count_val, 1)

    items = []
    for name, count in sorted(counts.items(), key=lambda x: -x[1]):
        if count < min_count:
            continue
        weight = (count - min_count_val) / range_count if range_count > 0 else 0.5
        size = int(12 + math.log2(count + 1) * 6)
        color = _weight_to_color(weight)
        items.append(TagCloudItem(name=name, count=count, weight=round(weight, 3),
                                   size=size, color=color))
    return items


def _weight_to_color(weight: float) -> str:
    """Map weight (0-1) to a color."""
    if weight >= 0.75: return "#d73a4a"  # red - high frequency
    elif weight >= 0.5: return "#fbca04"  # yellow
    elif weight >= 0.25: return "#0075ca"  # blue
    else: return "#999999"  # grey - low frequency


def tag_cloud_report(tasks: List) -> Dict:
    """Generate a full tag cloud report."""
    cloud = generate_tag_cloud(tasks)
    total_tags = len(cloud)
    total_occurrences = sum(item.count for item in cloud)
    return {
        "total_tags": total_tags,
        "total_occurrences": total_occurrences,
        "avg_occurrences": round(total_occurrences / max(total_tags, 1), 1),
        "most_common": [{"name": i.name, "count": i.count} for i in cloud[:5]],
        "by_importance": {
            "high": sum(1 for i in cloud if i.importance == "high"),
            "medium": sum(1 for i in cloud if i.importance == "medium"),
            "low": sum(1 for i in cloud if i.importance == "low"),
            "minimal": sum(1 for i in cloud if i.importance == "minimal"),
        },
    }


def filter_by_weight(cloud: List[TagCloudItem], min_weight: float = 0.3) -> List[TagCloudItem]:
    """Filter out low-weight tags."""
    return [item for item in cloud if item.weight >= min_weight]


def co_occurrence_matrix(tasks: List) -> Dict[str, Dict[str, int]]:
    """Build a tag co-occurrence matrix."""
    matrix: Dict[str, Dict[str, int]] = {}
    for task in tasks:
        tags = list(_get_tags(task))
        for i, tag_a in enumerate(tags):
            for tag_b in tags[i+1:]:
                if tag_a not in matrix:
                    matrix[tag_a] = {}
                if tag_b not in matrix:
                    matrix[tag_b] = {}
                matrix[tag_a][tag_b] = matrix[tag_a].get(tag_b, 0) + 1
                matrix[tag_b][tag_a] = matrix[tag_b].get(tag_a, 0) + 1
    return matrix


def top_co_occurrences(matrix: Dict, n: int = 10) -> List[dict]:
    """Find the most common tag pairs."""
    pairs = []
    seen = set()
    for tag_a, row in matrix.items():
        for tag_b, count in row.items():
            key = tuple(sorted([tag_a, tag_b]))
            if key in seen:
                continue
            seen.add(key)
            pairs.append({"tag_a": tag_a, "tag_b": tag_b, "count": count})
    pairs.sort(key=lambda x: -x["count"])
    return pairs[:n]


def tag_diversity(tasks: List) -> float:
    """Calculate tag diversity (Shannon entropy)."""
    counts: Dict[str, int] = {}
    for task in tasks:
        for tag in _get_tags(task):
            counts[tag] = counts.get(tag, 0) + 1
    total = sum(counts.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return round(entropy, 3)
