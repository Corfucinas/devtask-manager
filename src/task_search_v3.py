"""Search with fuzzy ranking and highlighting."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


def _tokens(text: str) -> List[str]:
    return [t for t in (text or "").lower().split() if t]


def _score_task(task, query: str) -> Tuple[float, Dict]:
    """Score a task against a query; returns (score, highlight_offsets)."""
    title = (getattr(task, "title", "") or "")
    desc = (getattr(task, "description", "") or "")
    tags = getattr(task, "tags", []) or []
    q = query.lower().strip()
    if not q:
        return 0.0, {}
    score = 0.0
    offsets: Dict[str, List[Tuple[int, int]]] = {}

    # Title exact prefix (highest signal)
    if title.lower().startswith(q):
        score += 50
        offsets.setdefault("title", []).append((0, len(q)))
    # Title token match
    title_toks = _tokens(title)
    if q in title_toks:
        score += 30
        idx = title.lower().index(q)
        offsets.setdefault("title", []).append((idx, idx + len(q)))
    # Title substring (weaker)
    elif q in title.lower():
        score += 15
        idx = title.lower().index(q)
        offsets.setdefault("title", []).append((idx, idx + len(q)))
    # Description substring
    if q in desc.lower():
        score += 10
        idx = desc.lower().index(q)
        offsets.setdefault("description", []).append((idx, idx + len(q)))
    # Tag match
    for tag in tags:
        if q == str(tag).lower():
            score += 20
            offsets.setdefault("tags", []).append((0, len(str(tag))))
    return score, offsets


def ranked_search(tasks, query: str, min_score: float = 1.0,
                  limit: int = None) -> List[Dict]:
    """Return tasks matching query, sorted by relevance."""
    results = []
    for i, task in enumerate(tasks):
        score, offsets = _score_task(task, query)
        if score >= min_score:
            results.append({
                "task": task,
                "id": getattr(task, "id", i),
                "title": getattr(task, "title", ""),
                "score": score,
                "highlights": offsets,
            })
    results.sort(key=lambda r: -r["score"])
    if limit:
        results = results[:limit]
    return results


def highlight_text(text: str, query: str, marker: str = "**") -> str:
    """Wrap query occurrences in text with markers."""
    if not query or not text:
        return text
    lower = text.lower()
    q = query.lower()
    out = []
    i = 0
    while i < len(text):
        idx = lower.find(q, i)
        if idx == -1:
            out.append(text[i:])
            break
        out.append(text[i:idx])
        out.append(marker + text[idx:idx + len(q)] + marker)
        i = idx + len(q)
    return "".join(out)


def search_stats(tasks, query: str) -> Dict:
    results = ranked_search(tasks, query)
    if not results:
        return {"query": query, "matches": 0, "avg_score": 0.0,
                "top_score": 0.0}
    return {"query": query, "matches": len(results),
            "avg_score": round(sum(r["score"] for r in results) / len(results), 1),
            "top_score": results[0]["score"]}
