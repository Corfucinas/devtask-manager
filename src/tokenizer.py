"""Text tokenizer for task search indexing."""
from typing import Dict, List, Set, Tuple
import re


STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
              "to", "of", "in", "on", "at", "by", "for", "with", "from",
              "and", "or", "not", "but", "if", "then", "else", "so", "no",
              "it", "this", "that", "these", "those", "i", "you", "he",
              "she", "we", "they", "me", "him", "her", "us", "them"}


def tokenize(text: str, remove_stop_words: bool = True) -> List[str]:
    """Split text into normalized lowercase tokens."""
    if not text:
        return []
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    if remove_stop_words:
        tokens = [t for t in tokens if t not in STOP_WORDS]
    return tokens


def unique_tokens(text: str, remove_stop_words: bool = True) -> Set[str]:
    """Return unique tokens from text."""
    return set(tokenize(text, remove_stop_words))


def build_index(tasks: List) -> Dict[str, List[int]]:
    """Build a search index from task list. Returns {token: [task_ids]}."""
    index: Dict[str, List[int]] = {}
    for task in tasks:
        task_id = getattr(task, "id", 0)
        title = getattr(task, "title", "") or ""
        desc = getattr(task, "description", "") or ""
        tags = getattr(task, "tags", []) or []
        text = f"{title} {desc} {' '.join(tags)}"
        for token in unique_tokens(text):
            if token not in index:
                index[token] = []
            index[token].append(task_id)
    return index


def search_index(index: Dict[str, List[int]], query: str) -> List[int]:
    """Search the index for tasks matching the query."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    result_sets = []
    for token in query_tokens:
        if token in index:
            result_sets.append(set(index[token]))
        else:
            result_sets.append(set())
    if not result_sets:
        return []
    # Intersection for AND search
    results = result_sets[0]
    for s in result_sets[1:]:
        results &= s
    return sorted(results)


def search_index_any(index: Dict[str, List[int]], query: str) -> List[int]:
    """Search the index for tasks matching ANY query token (OR search)."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    results = set()
    for token in query_tokens:
        if token in index:
            results.update(index[token])
    return sorted(results)


def token_stats(index: Dict[str, List[int]]) -> dict:
    """Return statistics about the search index."""
    if not index:
        return {"total_tokens": 0, "total_references": 0, "avg_refs": 0, "max_refs": 0}
    refs = [len(ids) for ids in index.values()]
    return {"total_tokens": len(index),
            "total_references": sum(refs),
            "avg_refs": round(sum(refs) / len(refs), 2),
            "max_refs": max(refs)}


def merge_indexes(*indexes: Dict[str, List[int]]) -> Dict[str, List[int]]:
    """Merge multiple search indexes."""
    merged: Dict[str, List[int]] = {}
    for index in indexes:
        for token, ids in index.items():
            if token not in merged:
                merged[token] = []
            merged[token].extend(ids)
    return merged


def index_task(task) -> Dict[str, List[int]]:
    """Index a single task."""
    return build_index([task])


def reindex(tasks: List, old_index: Dict[str, List[int]] = None) -> Dict[str, List[int]]:
    """Rebuild the index from scratch or update incrementally."""
    return build_index(tasks)


def query_suggestions(index: Dict[str, List[int]], prefix: str, limit: int = 5) -> List[str]:
    """Suggest tokens that start with a prefix."""
    prefix_lower = prefix.lower()
    matches = [t for t in index if t.startswith(prefix_lower)]
    matches.sort(key=lambda t: len(index[t]), reverse=True)
    return matches[:limit]
