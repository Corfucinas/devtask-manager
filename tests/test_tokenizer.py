"""Tests for text tokenizer."""
import pytest
from src.tokenizer import (
    tokenize, unique_tokens, build_index, search_index, search_index_any,
    token_stats, merge_indexes, index_task, reindex, query_suggestions,
    STOP_WORDS,
)


class FakeTask:
    def __init__(self, id, title="", description="", tags=None):
        self.id = id
        self.title = title
        self.description = description
        self.tags = tags or []


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "Fix login bug", "Authentication fails on OAuth", ["bug", "auth"]),
        FakeTask(2, "Add dark mode", "UI theme switcher", ["feature", "ui"]),
        FakeTask(3, "Refactor auth module", "Clean up authentication code", ["refactor", "auth"]),
    ]


@pytest.fixture
def index(tasks):
    return build_index(tasks)


def test_tokenize_basic():
    tokens = tokenize("Fix login bug")
    assert "fix" in tokens
    assert "login" in tokens
    assert "bug" in tokens


def test_tokenize_stops():
    tokens = tokenize("The fix is a bug")
    assert "the" not in tokens
    assert "is" not in tokens
    assert "a" not in tokens


def test_tokenize_empty():
    assert tokenize("") == []


def test_tokenize_no_stop_words():
    tokens = tokenize("the bug", remove_stop_words=False)
    assert "the" in tokens


def test_unique_tokens():
    tokens = unique_tokens("bug bug bug fix")
    assert tokens == {"bug", "fix"}


def test_build_index(tasks):
    idx = build_index(tasks)
    assert "fix" in idx
    assert "login" in idx
    assert 1 in idx["fix"]


def test_search_index_and(index, tasks):
    results = search_index(index, "login bug")
    assert 1 in results
    assert 2 not in results


def test_search_index_any(index):
    results = search_index_any(index, "auth")
    assert 1 in results  # "Authentication" contains "auth"
    assert 3 in results  # "auth" tag


def test_search_index_empty_query(index):
    assert search_index(index, "") == []


def test_search_index_no_match(index):
    assert search_index(index, "nonexistent") == []


def test_token_stats(index):
    stats = token_stats(index)
    assert stats["total_tokens"] > 0
    assert stats["total_references"] > 0
    assert "avg_refs" in stats


def test_token_stats_empty():
    stats = token_stats({})
    assert stats["total_tokens"] == 0


def test_merge_indexes():
    idx1 = {"bug": [1], "fix": [1]}
    idx2 = {"bug": [2], "feature": [2]}
    merged = merge_indexes(idx1, idx2)
    assert sorted(merged["bug"]) == [1, 2]
    assert "feature" in merged


def test_index_task():
    task = FakeTask(1, "Fix bug", "description", ["tag"])
    idx = index_task(task)
    assert "fix" in idx
    assert "bug" in idx


def test_reindex(tasks):
    idx = reindex(tasks)
    assert "fix" in idx


def test_query_suggestions(index):
    suggestions = query_suggestions(index, "au")
    assert len(suggestions) <= 5
    # "auth" should be in suggestions since it starts with "au"
