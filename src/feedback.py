"""Feedback collection and sentiment tracking."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


POSITIVE_WORDS = {"good", "great", "excellent", "amazing", "perfect", "love",
                   "awesome", "fantastic", "wonderful", "happy", "satisfied",
                   "nice", "brilliant", "outstanding", "superb", "glad"}
NEGATIVE_WORDS = {"bad", "terrible", "awful", "hate", "horrible", "broken",
                  "wrong", "fail", "fail", "poor", "disappointed", "sad",
                  "angry", "frustrated", "useless", "buggy", "crash", "stuck"}
NEUTRAL_WORDS = {"ok", "fine", "normal", "average", "moderate", "neutral"}


@dataclass
class Feedback:
    """A single feedback entry."""
    id: int
    author: str
    text: str
    sentiment: str = "neutral"  # positive, negative, neutral
    task_id: Optional[int] = None
    rating: Optional[int] = None  # 1-5
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


def analyze_sentiment(text: str) -> str:
    """Simple keyword-based sentiment analysis."""
    if not text:
        return "neutral"
    words = set(text.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


class FeedbackCollector:
    """Collects and manages feedback."""
    def __init__(self):
        self._feedback: List[Feedback] = {}
        self._next_id = 1

    def add(self, author, text, task_id=None, rating=None):
        sentiment = analyze_sentiment(text)
        f = Feedback(id=self._next_id, author=author, text=text,
                     sentiment=sentiment, task_id=task_id, rating=rating)
        self._feedback[self._next_id] = f
        self._next_id += 1
        return f

    def get(self, feedback_id):
        return self._feedback.get(feedback_id)

    def all_feedback(self):
        return list(self._feedback.values())

    def for_task(self, task_id):
        return [f for f in self._feedback.values() if f.task_id == task_id]

    def by_author(self, author):
        return [f for f in self._feedback.values() if f.author == author]

    def by_sentiment(self, sentiment):
        return [f for f in self._feedback.values() if f.sentiment == sentiment]

    def count(self):
        return len(self._feedback)

    def average_rating(self):
        ratings = [f.rating for f in self._feedback.values() if f.rating is not None]
        if not ratings: return 0.0
        return round(sum(ratings) / len(ratings), 1)

    def remove(self, feedback_id):
        if feedback_id in self._feedback:
            del self._feedback[feedback_id]
            return True
        return False

    def clear(self):
        self._feedback = {}
        self._next_id = 1


def feedback_report(collector):
    """Generate a feedback summary report."""
    all_f = collector.all_feedback()
    return {"total": len(all_f),
            "positive": len(collector.by_sentiment("positive")),
            "negative": len(collector.by_sentiment("negative")),
            "neutral": len(collector.by_sentiment("neutral")),
            "avg_rating": collector.average_rating(),
            "sentiment_distribution": {
                "positive": round(len(collector.by_sentiment("positive")) / max(len(all_f), 1) * 100, 1),
                "negative": round(len(collector.by_sentiment("negative")) / max(len(all_f), 1) * 100, 1),
                "neutral": round(len(collector.by_sentiment("neutral")) / max(len(all_f), 1) * 100, 1),
            }}
