"""Duplicate task detection and merging."""
from typing import Dict, List, Optional, Tuple


def _normalize(text: str) -> str:
    return text.lower().strip()


def _tokenize(text: str) -> set:
    return set(_normalize(text).split())


def title_similarity(a: str, b: str) -> float:
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def tag_similarity(tags_a: list, tags_b: list) -> float:
    set_a = set(t.lower() for t in tags_a or [])
    set_b = set(t.lower() for t in tags_b or [])
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def similarity_score(task_a, task_b) -> float:
    title_sim = title_similarity(
        getattr(task_a, "title", ""),
        getattr(task_b, "title", ""),
    )
    tag_sim = tag_similarity(
        getattr(task_a, "tags", []) or [],
        getattr(task_b, "tags", []) or [],
    )
    priority_a = task_a.priority.value if hasattr(task_a.priority, "value") else task_a.priority
    priority_b = task_b.priority.value if hasattr(task_b.priority, "value") else task_b.priority
    priority_match = 1.0 if priority_a == priority_b else 0.0
    status_a = task_a.status.value if hasattr(task_a.status, "value") else task_a.status
    status_b = task_b.status.value if hasattr(task_b.status, "value") else task_b.status
    status_match = 1.0 if status_a == status_b else 0.0
    score = title_sim * 0.60 + tag_sim * 0.25 + priority_match * 0.10 + status_match * 0.05
    return round(min(1.0, score), 3)


def find_duplicates(tasks, threshold: float = 0.7) -> List[Tuple]:
    duplicates = []
    for i, a in enumerate(tasks):
        for b in tasks[i + 1:]:
            score = similarity_score(a, b)
            if score >= threshold:
                duplicates.append((a, b, score))
    duplicates.sort(key=lambda x: x[2], reverse=True)
    return duplicates


def merge_tasks(primary, duplicate) -> dict:
    merged = {
        "primary_id": getattr(primary, "id", None),
        "duplicate_id": getattr(duplicate, "id", None),
        "merged_tags": list(set(
            (getattr(primary, "tags", []) or []) + (getattr(duplicate, "tags", []) or [])
        )),
        "merged_notes": [],
        "merged_subtasks": [],
    }
    if hasattr(duplicate, "notes") and duplicate.notes:
        merged["merged_notes"] = list(duplicate.notes)
        if not hasattr(primary, "notes") or not primary.notes:
            primary.notes = []
        primary.notes.extend(duplicate.notes)
    if hasattr(duplicate, "subtasks") and duplicate.subtasks:
        merged["merged_subtasks"] = list(duplicate.subtasks)
        if not hasattr(primary, "subtasks") or primary.subtasks is None:
            primary.subtasks = []
        for st in duplicate.subtasks:
            if st not in primary.subtasks:
                primary.subtasks.append(st)
    if not getattr(primary, "description", "") and getattr(duplicate, "description", ""):
        primary.description = duplicate.description
        merged["took_description"] = True
    return merged


def duplicate_report(tasks, threshold: float = 0.7) -> dict:
    dupes = find_duplicates(tasks, threshold)
    groups = {}
    for a, b, score in dupes:
        a_id = getattr(a, "id", id(a))
        b_id = getattr(b, "id", id(b))
        if a_id not in groups:
            groups[a_id] = {"primary": a_id, "duplicates": [], "scores": []}
        groups[a_id]["duplicates"].append(b_id)
        groups[a_id]["scores"].append(score)
    return {
        "total_tasks": len(tasks),
        "duplicate_pairs": len(dupes),
        "duplicate_groups": len(groups),
        "highest_similarity": dupes[0][2] if dupes else 0.0,
        "groups": list(groups.values()),
    }


def auto_merge_duplicates(tasks, threshold: float = 0.85) -> List[dict]:
    results = []
    dupes = find_duplicates(tasks, threshold)
    merged_ids = set()
    for primary, duplicate, score in dupes:
        if getattr(duplicate, "id", id(duplicate)) in merged_ids:
            continue
        merge_result = merge_tasks(primary, duplicate)
        merge_result["similarity_score"] = score
        results.append(merge_result)
        merged_ids.add(getattr(duplicate, "id", id(duplicate)))
    return results
