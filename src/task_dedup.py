"""Task dedup with fuzzy matching."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


@dataclass
class SimilarPair:
    """A pair of similar tasks."""
    task_a_id: int
    task_b_id: int
    similarity: float
    match_reason: str = ""

    @property
    def is_high_confidence(self) -> bool:
        return self.similarity >= 0.9


def _normalize(text: str) -> str:
    """Normalize text for comparison."""
    return text.lower().strip()


def _tokenize(text: str) -> set:
    """Tokenize text into words."""
    return set(_normalize(text).split())


def fuzzy_similarity(a: str, b: str) -> float:
    """Calculate fuzzy similarity between two strings (0-1)."""
    if not a or not b:
        return 0.0
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return round(len(intersection) / len(union), 3)


def levenshtein_distance(a: str, b: str) -> int:
    """Calculate Levenshtein edit distance."""
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)
    matrix = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        matrix[i][0] = i
    for j in range(len(b) + 1):
        matrix[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i-1] == b[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,
                matrix[i][j-1] + 1,
                matrix[i-1][j-1] + cost
            )
    return matrix[len(a)][len(b)]


def normalized_levenshtein(a: str, b: str) -> float:
    """Normalized Levenshtein similarity (0-1)."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    dist = levenshtein_distance(_normalize(a), _normalize(b))
    max_len = max(len(_normalize(a)), len(_normalize(b)))
    return round(1 - dist / max_len, 3)


class TaskDedup:
    """Deduplicates tasks using fuzzy matching."""
    def __init__(self, threshold: float = 0.8, use_fuzzy: bool = True):
        self.threshold = threshold
        self.use_fuzzy = use_fuzzy

    def _similarity(self, a, b) -> Tuple[float, str]:
        """Calculate similarity between two tasks."""
        title_a = getattr(a, "title", "") or ""
        title_b = getattr(b, "title", "") or ""
        if self.use_fuzzy:
            jaccard = fuzzy_similarity(title_a, title_b)
            lev = normalized_levenshtein(title_a, title_b)
            score = (jaccard + lev) / 2
            reason = "fuzzy+jaccard"
        else:
            score = fuzzy_similarity(title_a, title_b)
            reason = "jaccard"
        # Boost if tags match
        tags_a = set(getattr(a, "tags", []) or [])
        tags_b = set(getattr(b, "tags", []) or [])
        if tags_a and tags_b and tags_a == tags_b:
            score = min(1.0, score + 0.1)
            reason = "fuzzy+tags"
        return round(score, 3), reason

    def find_similar(self, tasks: List) -> List[SimilarPair]:
        """Find all pairs of similar tasks above threshold."""
        pairs = []
        for i, a in enumerate(tasks):
            for b in tasks[i + 1:]:
                score, reason = self._similarity(a, b)
                if score >= self.threshold:
                    pairs.append(SimilarPair(
                        task_a_id=getattr(a, "id", i),
                        task_b_id=getattr(b, "id", i + 1),
                        similarity=score,
                        match_reason=reason,
                    ))
        pairs.sort(key=lambda p: -p.similarity)
        return pairs

    def group_similar(self, tasks: List) -> List[List]:
        """Group tasks into clusters of similar tasks."""
        pairs = self.find_similar(tasks)
        parent = {getattr(t, "id", i): getattr(t, "id", i) for i, t in enumerate(tasks)}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for pair in pairs:
            root_a = find(pair.task_a_id)
            root_b = find(pair.task_b_id)
            if root_a != root_b:
                parent[root_b] = root_a

        groups: Dict[int, List] = {}
        for i, t in enumerate(tasks):
            tid = getattr(t, "id", i)
            root = find(tid)
            if root not in groups:
                groups[root] = []
            groups[root].append(t)
        return list(groups.values())

    def keep_best(self, tasks: List) -> List:
        """Keep only the best task from each similar group (highest ID)."""
        groups = self.group_similar(tasks)
        result = []
        for group in groups:
            best = max(group, key=lambda t: getattr(t, "id", 0))
            result.append(best)
        return result

    def merge_into(self, primary, secondary) -> Dict:
        """Merge secondary task data into primary."""
        result = {"merged_from": getattr(secondary, "id", None),
                  "merged_into": getattr(primary, "id", None),
                  "merged_at": datetime.now(timezone.utc).isoformat()}
        tags_a = set(getattr(primary, "tags", []) or [])
        tags_b = set(getattr(secondary, "tags", []) or [])
        result["combined_tags"] = sorted(tags_a | tags_b)
        return result


def dedup_stats(tasks: List, threshold: float = 0.8) -> Dict:
    """Generate dedup statistics for a task list."""
    dedup = TaskDedup(threshold=threshold)
    pairs = dedup.find_similar(tasks)
    return {
        "total_tasks": len(tasks),
        "similar_pairs": len(pairs),
        "high_confidence_pairs": sum(1 for p in pairs if p.is_high_confidence),
        "avg_similarity": round(sum(p.similarity for p in pairs) / max(len(pairs), 1), 3)
            if pairs else 0.0,
        "estimated_unique": len(dedup.keep_best(tasks)),
    }


def default_dedup() -> TaskDedup:
    """Create a default deduplicator."""
    return TaskDedup(threshold=0.8, use_fuzzy=True)
