"""Deduplication utilities for tasks."""
from .models import Task, Status
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_duplicates(tasks, threshold=0.85):
    duplicates = []
    active = [t for t in tasks if t.status != Status.DONE]
    for i, t1 in enumerate(active):
        for t2 in active[i+1:]:
            sim = similarity(t1.title, t2.title)
            if sim >= threshold: duplicates.append((t1, t2, sim))
    return duplicates

def suggest_merges(tasks, threshold=0.85):
    dups = find_duplicates(tasks, threshold)
    return [{"keep": t1.id, "merge": t2.id, "similarity": round(sim, 2), "title": t1.title} for t1, t2, sim in dups]
