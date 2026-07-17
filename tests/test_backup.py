"""Tests for backup module."""
import os, tempfile, json, pytest
from src.backup import create_backup, list_backups, restore_backup, cleanup_old_backups

@pytest.fixture
def setup():
    d = tempfile.mkdtemp()
    storage = os.path.join(d, "tasks.json")
    backup_dir = os.path.join(d, "backups")
    with open(storage, "w") as f:
        json.dump([{"id": 1, "title": "Test"}], f)
    return storage, backup_dir, d

class TestCreateBackup:
    def test_creates(self, setup):
        storage, backup_dir, _ = setup
        path = create_backup(storage, backup_dir)
        assert os.path.exists(path)

class TestListBackups:
    def test_lists(self, setup):
        storage, backup_dir, _ = setup
        create_backup(storage, backup_dir)
        assert len(list_backups(backup_dir)) == 1

class TestRestoreBackup:
    def test_restores(self, setup):
        storage, backup_dir, _ = setup
        path = create_backup(storage, backup_dir)
        with open(storage, "w") as f:
            f.write("[]")
        restore_backup(path, storage)
        with open(storage) as f:
            assert json.load(f) == [{"id": 1, "title": "Test"}]

class TestCleanup:
    def test_keeps_latest(self, setup):
        storage, backup_dir, _ = setup
        for _ in range(15):
            create_backup(storage, backup_dir)
        cleanup_old_backups(backup_dir, keep=10)
        assert len(list_backups(backup_dir)) == 10
