"""Tests for deduplication."""
import pytest
from src.models import Task, Priority, Status
from src.dedupe import similarity, find_duplicates, suggest_merges

class TestSimilarity:
    def test_identical(self):
        assert similarity("Fix bug", "Fix bug") == 1.0
    def test_different(self):
        assert similarity("Fix bug", "Write docs") < 0.3

class TestFindDuplicates:
    def test_finds_similar(self):
        tasks = [Task(id=1, title="Fix login bug"), Task(id=2, title="Fix login bug"), Task(id=3, title="Write docs")]
        dups = find_duplicates(tasks, threshold=0.9)
        assert len(dups) == 1
    def test_excludes_done(self):
        tasks = [Task(id=1, title="Fix bug", status=Status.DONE), Task(id=2, title="Fix bug")]
        assert len(find_duplicates(tasks, threshold=0.9)) == 0

class TestSuggestMerges:
    def test_suggests(self):
        tasks = [Task(id=1, title="Fix login"), Task(id=2, title="Fix login")]
        suggestions = suggest_merges(tasks, threshold=0.9)
        assert len(suggestions) == 1
        assert suggestions[0]["keep"] == 1
