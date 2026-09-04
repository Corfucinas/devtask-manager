"""Tests for task dedup with fuzzy matching."""
import pytest
from src.task_dedup import (
    SimilarPair, fuzzy_similarity, levenshtein_distance,
    normalized_levenshtein, TaskDedup, dedup_stats, default_dedup,
)


class FakeTask:
    def __init__(self, id, title="Task", tags=None):
        self.id = id
        self.title = title
        self.tags = tags or []


def test_fuzzy_similarity_identical():
    assert fuzzy_similarity("fix login bug", "fix login bug") == 1.0


def test_fuzzy_similarity_partial():
    score = fuzzy_similarity("fix login bug", "fix auth bug")
    assert 0 < score < 1.0


def test_fuzzy_similarity_none():
    assert fuzzy_similarity("", "test") == 0.0


def test_levenshtein_distance():
    assert levenshtein_distance("kitten", "sitting") == 3
    assert levenshtein_distance("same", "same") == 0


def test_normalized_levenshtein():
    assert normalized_levenshtein("same", "same") == 1.0
    score = normalized_levenshtein("abc", "abd")
    assert 0 < score < 1.0


def test_find_similar():
    tasks = [FakeTask(1, "Fix login bug"), FakeTask(2, "Fix login bug"), FakeTask(3, "Add dark mode")]
    dedup = TaskDedup(threshold=0.8)
    pairs = dedup.find_similar(tasks)
    assert len(pairs) == 1
    assert pairs[0].task_a_id == 1


def test_find_similar_no_match():
    tasks = [FakeTask(1, "Fix bug"), FakeTask(2, "Add feature")]
    dedup = TaskDedup(threshold=0.9)
    assert dedup.find_similar(tasks) == []


def test_group_similar():
    tasks = [FakeTask(1, "Fix bug"), FakeTask(2, "Fix bug"), FakeTask(3, "Add feature")]
    dedup = TaskDedup(threshold=0.8)
    groups = dedup.group_similar(tasks)
    assert len(groups) == 2  # 1 pair + 1 single


def test_keep_best():
    tasks = [FakeTask(1, "Fix bug"), FakeTask(2, "Fix bug"), FakeTask(3, "Add feature")]
    dedup = TaskDedup(threshold=0.8)
    result = dedup.keep_best(tasks)
    assert len(result) == 2


def test_merge_into():
    primary = FakeTask(1, "Fix bug", tags=["bug"])
    secondary = FakeTask(2, "Fix bug", tags=["auth"])
    dedup = TaskDedup()
    result = dedup.merge_into(primary, secondary)
    assert result["merged_into"] == 1
    assert set(result["combined_tags"]) == {"bug", "auth"}


def test_dedup_stats():
    tasks = [FakeTask(1, "Fix bug"), FakeTask(2, "Fix bug"), FakeTask(3, "Add feature")]
    stats = dedup_stats(tasks)
    assert stats["total_tasks"] == 3
    assert stats["similar_pairs"] == 1
    assert stats["estimated_unique"] == 2


def test_dedup_stats_empty():
    assert dedup_stats([])["total_tasks"] == 0


def test_default_dedup():
    d = default_dedup()
    assert d.threshold == 0.8
    assert d.use_fuzzy is True


def test_similarity_pair_high_confidence():
    pair = SimilarPair(task_a_id=1, task_b_id=2, similarity=0.95)
    assert pair.is_high_confidence is True
    pair2 = SimilarPair(task_a_id=1, task_b_id=2, similarity=0.7)
    assert pair2.is_high_confidence is False


def test_tags_boost():
    dedup = TaskDedup(threshold=0.7)
    a = FakeTask(1, "Fix bug", tags=["bug", "auth"])
    b = FakeTask(2, "Fix auth bug", tags=["bug", "auth"])
    score, reason = dedup._similarity(a, b)
    assert "tags" in reason
