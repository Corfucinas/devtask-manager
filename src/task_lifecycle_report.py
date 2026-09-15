"""Lifecycle stage reporting and analytics."""
from dataclasses import dataclass
from typing import Dict, List, Optional
import statistics


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def stage_counts(tasks: List) -> Dict[str, int]:
    """Count tasks currently in each status."""
    counts: Dict[str, int] = {}
    for t in tasks:
        s = _get_status(t)
        counts[s] = counts.get(s, 0) + 1
    return counts


def aggregate_durations(duration_lists: Dict[str, List[float]]) -> Dict[str, Dict]:
    """Aggregate per-stage durations: mean/median/max/min."""
    result = {}
    for stage, durations in duration_lists.items():
        if not durations:
            result[stage] = {"count": 0, "mean": 0, "median": 0, "max": 0, "min": 0}
            continue
        result[stage] = {
            "count": len(durations),
            "mean": round(statistics.mean(durations), 2),
            "median": round(statistics.median(durations), 2),
            "max": round(max(durations), 2),
            "min": round(min(durations), 2),
        }
    return result


def bottleneck_stage(durations: Dict[str, List[float]]) -> Optional[str]:
    """Return the stage with the highest mean duration."""
    agg = aggregate_durations(durations)
    if not agg:
        return None
    return max(agg.items(), key=lambda kv: kv[1]["mean"])[0]


def transition_matrix(sequences: List[List[str]]) -> Dict[str, Dict[str, int]]:
    """Build a from->to count matrix from stage sequences."""
    matrix: Dict[str, Dict[str, int]] = {}
    for seq in sequences:
        for i in range(len(seq) - 1):
            frm, to = seq[i], seq[i + 1]
            matrix.setdefault(frm, {})
            matrix[frm][to] = matrix[frm].get(to, 0) + 1
    return matrix


def lifecycle_report(tasks: List, durations: Dict[str, List[float]] = None) -> Dict:
    """Full lifecycle analytics report."""
    durations = durations or {}
    agg = aggregate_durations(durations)
    return {
        "total_tasks": len(tasks),
        "stage_counts": stage_counts(tasks),
        "stage_durations": agg,
        "bottleneck": bottleneck_stage(durations),
    }
