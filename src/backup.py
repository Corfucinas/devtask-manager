"""Backup and restore for task storage."""
import os, shutil
from datetime import datetime, timezone

def create_backup(storage_path, backup_dir=None):
    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(storage_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"tasks_backup_{timestamp}.json")
    if os.path.exists(storage_path):
        shutil.copy2(storage_path, backup_path)
    return backup_path

def list_backups(backup_dir):
    if not os.path.exists(backup_dir):
        return []
    backups = []
    for f in sorted(os.listdir(backup_dir), reverse=True):
        if f.startswith("tasks_backup_") and f.endswith(".json"):
            path = os.path.join(backup_dir, f)
            backups.append({"filename": f, "path": path, "size": os.path.getsize(path)})
    return backups

def restore_backup(backup_path, storage_path):
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    shutil.copy2(backup_path, storage_path)
    return storage_path

def cleanup_old_backups(backup_dir, keep=10):
    backups = list_backups(backup_dir)
    if len(backups) <= keep:
        return 0
    for b in backups[keep:]:
        os.remove(b["path"])
    return len(backups) - keep
