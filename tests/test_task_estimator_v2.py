"""Tests for enhanced task estimator."""
import pytest
from src.task_estimator_v2 import (
    Estimate, EstimationModel, TaskEstimatorV2, estimation_report, default_estimator,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, priority="medium", story_points=5, tags=None):
        self.id = id
        self.priority = FakePriority(priority)
        self.story_points = story_points
        self.tags = tags or []


@pytest.fixture
def estimator():
    e = TaskEstimatorV2()
    e.add_historical(1, "high", 3, ["bug"], 9.0)
    e.add_historical(2, "medium", 5, ["feature"], 20.0)
    e.add_historical(3, "high", 5, ["feature"], 15.0)
    e.add_historical(4, "medium", 3, ["bug"], 12.0)
    e.add_historical(5, "medium", 8, ["docs"], 32.0)
    return e


def test_estimate_create():
    e = Estimate(task_id=1, model="parametric", optimistic=5, likely=10, pessimistic=20)
    assert e.expected == pytest.approx((5 + 40 + 20) / 6, abs=0.1)


def test_parametric_estimate(estimator):
    task = FakeTask(1, priority="medium", story_points=3)
    est = estimator.estimate(task, EstimationModel.PARAMETRIC)
    assert est.likely == 12.0
    assert est.model == "parametric"


def test_analogous_estimate(estimator):
    task = FakeTask(1, priority="medium", story_points=3)
    est = estimator.estimate(task, EstimationModel.ANALOGOUS)
    assert est.model == "analogous"
    assert est.likely == 12.0  # matches task 4


def test_analogous_no_similar(estimator):
    task = FakeTask(1, priority="critical", story_points=20)
    est = estimator.estimate(task, EstimationModel.ANALOGOUS)
    assert est.model == "parametric"  # fallback


def test_expert_estimate(estimator):
    task = FakeTask(1, priority="medium", story_points=3, tags=["bug"])
    est = estimator.estimate(task, EstimationModel.EXPERT)
    assert est.model == "expert"
    assert est.likely == 12.0  # 3 * 5 * 0.8


def test_risk_adjusted_estimate(estimator):
    task = FakeTask(1, priority="critical", story_points=3)
    est = estimator.estimate(task, EstimationModel.RISK_ADJUSTED)
    assert est.model == "risk_adjusted"
    assert est.likely > 12  # has risk buffer


def test_consensus_estimate(estimator):
    task = FakeTask(1, priority="medium", story_points=3)
    est = estimator.estimate(task, EstimationModel.CONSENSUS)
    assert est.model == "consensus"
    assert est.expected > 0


def test_compare_models(estimator):
    task = FakeTask(1, priority="medium", story_points=3)
    comparison = estimator.compare_models(task)
    assert "parametric" in comparison
    assert "analogous" in comparison
    assert "consensus" in comparison


def test_estimate_confidence():
    e = Estimate(task_id=1, model="test", optimistic=1, likely=5, pessimistic=10, confidence=0.8)
    assert e.confidence == 0.8


def test_all_estimates(estimator):
    task = FakeTask(1, priority="medium")
    estimator.estimate(task)
    estimator.estimate(task)
    assert estimator.estimate_count() == 2


def test_history_count(estimator):
    assert estimator.history_count() == 5


def test_accuracy_by_model(estimator):
    task = FakeTask(1)
    estimator.estimate(task, EstimationModel.PARAMETRIC)
    estimator.estimate(task, EstimationModel.EXPERT)
    acc = estimator.accuracy_by_model()
    assert "parametric" in acc
    assert "expert" in acc


def test_estimation_report(estimator):
    task = FakeTask(1, priority="medium", story_points=3)
    estimator.estimate(task)
    report = estimation_report(estimator)
    assert report["total_estimates"] == 1
    assert report["history_size"] == 5
    assert "by_model" in report
    assert "avg_expected" in report


def test_estimation_report_empty():
    report = estimation_report(TaskEstimatorV2())
    assert report["total"] == 0


def test_default_estimator():
    e = default_estimator()
    assert e.history_count() == 5
    task = FakeTask(1, priority="high", story_points=3)
    est = e.estimate(task, EstimationModel.ANALOGOUS)
    assert est.likely == 9.0  # matches task 1
