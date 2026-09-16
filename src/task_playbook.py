"""Playbook system for repeatable procedures."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class PlaybookStep:
    """One step of a playbook."""
    id: int
    description: str
    optional: bool = False
    done: bool = False


@dataclass
class Playbook:
    """A named, ordered, repeatable procedure."""
    id: int
    name: str
    description: str = ""
    prerequisites: List[str] = field(default_factory=list)
    steps: List[PlaybookStep] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def add_step(self, description: str, optional: bool = False) -> PlaybookStep:
        step = PlaybookStep(id=len(self.steps) + 1, description=description,
                            optional=optional)
        self.steps.append(step)
        return step

    def remove_step(self, step_id: int) -> bool:
        before = len(self.steps)
        self.steps = [s for s in self.steps if s.id != step_id]
        return len(self.steps) < before

    def mark_done(self, step_id: int) -> bool:
        for s in self.steps:
            if s.id == step_id:
                s.done = True
                return True
        return False

    def progress(self) -> float:
        if not self.steps:
            return 0.0
        done = sum(1 for s in self.steps if s.done)
        return round(done / len(self.steps) * 100, 1)

    def next_step(self) -> Optional[PlaybookStep]:
        for s in self.steps:
            if not s.done:
                return s
        return None

    def remaining(self) -> List[PlaybookStep]:
        return [s for s in self.steps if not s.done]

    def is_complete(self) -> bool:
        return bool(self.steps) and all(s.done or s.optional for s in self.steps)

    def reset(self):
        for s in self.steps:
            s.done = False


class PlaybookLibrary:
    """Stores named playbooks and tracks runs."""
    def __init__(self):
        self._playbooks: Dict[int, Playbook] = {}
        self._runs: List[Dict] = []
        self._next_id = 1

    def create(self, name: str, description: str = "",
               prerequisites: List[str] = None) -> Playbook:
        pb = Playbook(id=self._next_id, name=name, description=description,
                      prerequisites=prerequisites or [])
        self._playbooks[self._next_id] = pb
        self._next_id += 1
        return pb

    def get(self, playbook_id: int) -> Optional[Playbook]:
        return self._playbooks.get(playbook_id)

    def all_playbooks(self) -> List[Playbook]:
        return list(self._playbooks.values())

    def count(self) -> int:
        return len(self._playbooks)

    def record_run(self, playbook: Playbook):
        self._runs.append({
            "playbook_id": playbook.id,
            "name": playbook.name,
            "progress": playbook.progress(),
            "complete": playbook.is_complete(),
            "ran_at": datetime.now(timezone.utc).isoformat(),
        })

    def runs(self) -> List[Dict]:
        return list(self._runs)


def playbook_report(lib: PlaybookLibrary) -> Dict:
    return {"total_playbooks": lib.count(), "total_runs": len(lib.runs()),
            "playbooks": [{"id": p.id, "name": p.name,
                           "steps": len(p.steps), "progress": p.progress()}
                          for p in lib.all_playbooks()]}
