"""Tests for migration utilities."""
import pytest
from src.migrate import get_current_version, migrate_v1_to_v2, migrate_v2_to_v3, migrate_v3_to_v4, migrate, needs_migration

class TestGetVersion:
    def test_v1(self):
        assert get_current_version([{"id": 1, "title": "Test"}]) == 1
    def test_v2(self):
        assert get_current_version([{"id": 1, "title": "Test", "tags": []}]) == 2
    def test_v3(self):
        assert get_current_version([{"id": 1, "title": "Test", "tags": [], "priority": "high"}]) == 3
    def test_v4(self):
        assert get_current_version([{"id": 1, "title": "Test", "tags": [], "priority": "high", "updated_at": "2026-01-01"}]) == 4

class TestMigrations:
    def test_v1_to_v2(self):
        result = migrate_v1_to_v2([{"id": 1, "title": "Test"}])
        assert result[0]["tags"] == []
    def test_v2_to_v3(self):
        result = migrate_v2_to_v3([{"id": 1, "title": "Test", "tags": []}])
        assert result[0]["priority"] == "medium"
    def test_v3_to_v4(self):
        result = migrate_v3_to_v4([{"id": 1, "title": "Test", "tags": [], "priority": "high", "created_at": "2026-01-01"}])
        assert "updated_at" in result[0]

class TestMigrate:
    def test_full_migration(self):
        result = migrate([{"id": 1, "title": "Test"}], target_version=4)
        assert result[0].get("tags") == []
        assert result[0].get("priority") == "medium"
        assert "updated_at" in result[0]

class TestNeedsMigration:
    def test_needs(self):
        assert needs_migration([{"id": 1, "title": "Test"}]) is True
    def test_does_not_need(self):
        assert needs_migration([{"id": 1, "title": "Test", "tags": [], "priority": "high", "updated_at": "2026-01-01"}]) is False
