"""Snapshot functionality for task state capture."""
from datetime import datetime, timezone

class TaskSnapshot:
    def __init__(self):
        self._snapshots = {}
    def capture(self, name, tasks):
        snapshot = {"name": name, "timestamp": datetime.now(timezone.utc).isoformat(), "tasks": [t.to_dict() for t in tasks], "task_count": len(tasks)}
        self._snapshots[name] = snapshot
        return snapshot
    def restore(self, name, store):
        if name not in self._snapshots:
            raise KeyError(f"Snapshot not found: {name}")
        snapshot = self._snapshots[name]
        restored = []
        for td in snapshot["tasks"]:
            task = store.create(title=td["title"], description=td.get("description", ""), priority=td.get("priority", "medium"), tags=td.get("tags", []))
            if td.get("status") == "done":
                store.update(task.id, status="done")
            restored.append(task)
        return restored
    def list_snapshots(self):
        return [{"name": s["name"], "timestamp": s["timestamp"], "task_count": s["task_count"]} for s in self._snapshots.values()]
    def compare(self, name1, name2):
        s1 = self._snapshots.get(name1)
        s2 = self._snapshots.get(name2)
        if not s1 or not s2: raise KeyError("Snapshot not found")
        t1 = {t["title"] for t in s1["tasks"]}
        t2 = {t["title"] for t in s2["tasks"]}
        return {"added": list(t2 - t1), "removed": list(t1 - t2), "common": len(t1 & t2)}
    def delete_snapshot(self, name):
        if name in self._snapshots:
            del self._snapshots[name]
            return True
        return False
