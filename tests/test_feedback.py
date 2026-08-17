"""Tests for feedback collection."""
import pytest
from src.feedback import (
    Feedback, FeedbackCollector, analyze_sentiment, feedback_report,
)


@pytest.fixture
def collector():
    c = FeedbackCollector()
    c.add("alice", "This is great and amazing", task_id=1, rating=5)
    c.add("bob", "This is terrible and broken", task_id=1, rating=2)
    c.add("charlie", "It is ok", task_id=2, rating=3)
    return c


def test_analyze_sentiment_positive():
    assert analyze_sentiment("This is great and amazing") == "positive"


def test_analyze_sentiment_negative():
    assert analyze_sentiment("This is terrible and awful") == "negative"


def test_analyze_sentiment_neutral():
    assert analyze_sentiment("It is fine") == "neutral"


def test_analyze_sentiment_empty():
    assert analyze_sentiment("") == "neutral"


def test_collector_add():
    c = FeedbackCollector()
    f = c.add("alice", "Great work")
    assert f.id == 1
    assert f.author == "alice"
    assert f.sentiment == "positive"


def test_collector_get(collector):
    assert collector.get(1) is not None
    assert collector.get(999) is None


def test_collector_for_task(collector):
    task1 = collector.for_task(1)
    assert len(task1) == 2
    task2 = collector.for_task(2)
    assert len(task2) == 1


def test_collector_by_author(collector):
    alice = collector.by_author("alice")
    assert len(alice) == 1


def test_collector_by_sentiment(collector):
    pos = collector.by_sentiment("positive")
    neg = collector.by_sentiment("negative")
    assert len(pos) == 1
    assert len(neg) == 1


def test_collector_count(collector):
    assert collector.count() == 3


def test_collector_average_rating(collector):
    assert collector.average_rating() == pytest.approx(3.3, abs=0.1)


def test_collector_remove(collector):
    assert collector.remove(1) is True
    assert collector.count() == 2
    assert collector.remove(999) is False


def test_collector_clear(collector):
    collector.clear()
    assert collector.count() == 0


def test_feedback_report(collector):
    report = feedback_report(collector)
    assert report["total"] == 3
    assert report["positive"] == 1
    assert report["negative"] == 1
    assert report["neutral"] == 1
    assert "avg_rating" in report
    assert "sentiment_distribution" in report


def test_feedback_auto_sentiment():
    c = FeedbackCollector()
    f = c.add("alice", "Love it!")
    assert f.sentiment == "positive"
    f2 = c.add("bob", "Hate it!")
    assert f2.sentiment == "negative"
