"""Automatic task assignment based on skills and capacity."""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class TeamMemberInfo:
    """Team member with skills and capacity."""
    name: str
    skills: List[str] = field(default_factory=list)
    current_load: int = 0
    max_load: int = 5
    specialty: str = ""


@dataclass
class AssignmentRule:
    """A rule for matching tasks to team members."""
    id: int
    name: str
    condition: Callable
    required_skill: str = ""
    priority: int = 0
    enabled: bool = True


class AutoAssigner:
    """Automatic task assignment engine."""
    def __init__(self):
        self._rules: Dict[int, AssignmentRule] = {}
        self._next_id = 1
        self._assignments: List[dict] = []

    def add_rule(self, name, condition, required_skill="", priority=0):
        rule = AssignmentRule(id=self._next_id, name=name, condition=condition,
                              required_skill=required_skill, priority=priority)
        self._rules[self._next_id] = rule
        self._next_id += 1
        return rule

    def remove_rule(self, rule_id):
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def all_rules(self):
        return sorted(self._rules.values(), key=lambda r: -r.priority)

    def enabled_rules(self):
        return [r for r in self.all_rules() if r.enabled]

    def count(self):
        return len(self._rules)

    def assign(self, task, team):
        """Find the best team member for a task."""
        for rule in self.enabled_rules():
            try:
                if not rule.condition(task):
                    continue
            except Exception:
                continue

            candidates = self._find_candidates(rule, team)
            if candidates:
                member = candidates[0]
                member.current_load += 1
                assignment = {
                    "task_id": getattr(task, "id", None),
                    "assignee": member.name,
                    "rule": rule.name,
                    "skill_matched": rule.required_skill,
                }
                self._assignments.append(assignment)
                return assignment
        return None

    def _find_candidates(self, rule, team):
        """Find available team members with the required skill."""
        candidates = [m for m in team if m.current_load < m.max_load]
        if rule.required_skill:
            candidates = [m for m in candidates if rule.required_skill in m.skills]
        candidates.sort(key=lambda m: m.current_load)
        return candidates

    def assignments(self):
        return list(self._assignments)

    def assignment_count(self):
        return len(self._assignments)

    def clear_assignments(self):
        self._assignments = []


def assignment_report(assigner, tasks, team):
    """Generate an assignment summary report."""
    return {
        "total_tasks": len(tasks),
        "assigned": assigner.assignment_count(),
        "unassigned": len(tasks) - assigner.assignment_count(),
        "team_load": {m.name: m.current_load for m in team},
        "rules": len(assigner.all_rules()),
        "assignments": assigner.assignments(),
    }


def default_rules():
    """Create an assigner with common default rules."""
    a = AutoAssigner()
    a.add_rule("Critical to senior", lambda t: t.priority.value in ("critical",) if hasattr(t.priority, "value") else False,
               required_skill="senior", priority=10)
    a.add_rule("Bug to QA", lambda t: "bug" in (getattr(t, "tags", []) or []),
               required_skill="testing", priority=8)
    a.add_rule("Feature to devs", lambda t: "feature" in (getattr(t, "tags", []) or []),
               required_skill="development", priority=5)
    a.add_rule("Any available", lambda t: True, priority=1)
    return a
