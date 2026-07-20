"""Tests for task archiving system."""

import json
import os
import tempfile
import pytest
from src.archive import TaskArchiver


@pytest.fixture
def archiver():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.close()
    arch = TaskArchiver(archive_path=tmp.name)
    yield arch
    os.unlink(tmp.name)


@pytest.fixture
def sample_tasks():
    return [
        {"id": 1, "title": "Done task", "status": "done", "tags": ["bug"]},
        {"id": 2, "title": "Active task", "status": "todo", "tags": ["feature"]},
        {"id": 3, "title": "Another done", "status": "done", "tags": ["bug", "docs"]},
    ]


class TestTaskArchiver:
    def test_archive_single_task(self, archiver):
        task = {"id": 1, "title": "Test", "status": "done", "tags": []}
        result = archiver.archive_task(task)
        assert result is True
        archived = archiver.list_archived()
        assert len(archived) == 1
        assert archived[0]["id"] == 1
        assert "archived_at" in archived[0]

    def test_archive_completed_batch(self, archiver, sample_tasks):
        count, remaining = archiver.archive_completed(sample_tasks)
        assert count == 2
        assert len(remaining) == 1
        assert remaining[0]["id"] == 2

    def test_list_archived_with_tag_filter(self, archiver, sample_tasks):
        archiver.archive_completed(sample_tasks)
        docs = archiver.list_archived(tag="docs")
        assert len(docs) == 1
        assert docs[0]["id"] == 3

    def test_list_archived_with_limit(self, archiver, sample_tasks):
        archiver.archive_completed(sample_tasks)
        limited = archiver.list_archived(limit=1)
        assert len(limited) == 1

    def test_restore_task(self, archiver):
        task = {"id": 5, "title": "Restore me", "status": "done", "tags": []}
        archiver.archive_task(task)
        restored = archiver.restore_task(5)
        assert restored is not None
        assert restored["status"] == "todo"
        assert "archived_at" not in restored
        archived = archiver.list_archived()
        assert len(archived) == 0

    def test_restore_nonexistent(self, archiver):
        result = archiver.restore_task(999)
        assert result is None

    def test_archive_stats(self, archiver, sample_tasks):
        archiver.archive_completed(sample_tasks)
        stats = archiver.archive_stats()
        assert stats["total_archived"] == 2
        assert stats["by_tag"]["bug"] == 2
        assert stats["by_tag"]["docs"] == 1
