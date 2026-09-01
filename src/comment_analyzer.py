"""Comment analyzer for sentiment and engagement."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import re


POSITIVE_WORDS = {"good", "great", "excellent", "perfect", "love", "awesome",
                  "nice", "thank", "thanks", "agree", "yes", "exactly", "right"}
NEGATIVE_WORDS = {"bad", "wrong", "fail", "hate", "terrible", "awful", "broken",
                  "bug", "issue", "problem", "no", "disagree", "wontfix", "wont"}
QUESTION_WORDS = {"what", "why", "how", "when", "where", "who", "which", "?",
                  "can", "could", "will", "would", "should", "may", "might"}
ACTION_INDICATORS = {"please", "please", "todo", "fix", "update", "change", "add",
                     "remove", "delete", "create", "check", "verify", "review",
                     "look", "need", "want", "must", "should"}


@dataclass
class CommentAnalysis:
    """Analysis result for a comment."""
    text: str
    sentiment: str  # positive, negative, neutral
    has_question: bool
    has_action_item: bool
    word_count: int
    mentions: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)


def analyze_comment(text) -> CommentAnalysis:
    """Analyze a single comment."""
    if not text:
        return CommentAnalysis(text="", sentiment="neutral", has_question=False,
                               has_action_item=False, word_count=0)
    words = text.lower().split()
    word_set = set(words)
    sentiment = _detect_sentiment(word_set)
    has_question = _has_question(word_set, text)
    mentions = re.findall(r"@([\w\-]+)", text)
    links = re.findall(r"https?://[^\s]+", text)
    action_items = _extract_actions(word_set, text)
    return CommentAnalysis(
        text=text, sentiment=sentiment, has_question=has_question,
        has_action_item=len(action_items) > 0, word_count=len(words),
        mentions=mentions, links=links, action_items=action_items,
    )


def _detect_sentiment(words: set) -> str:
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg: return "positive"
    elif neg > pos: return "negative"
    return "neutral"


def _has_question(words: set, text: str) -> bool:
    return "?" in text or bool(words & QUESTION_WORDS)


def _extract_actions(words: set, text: str) -> List[str]:
    """Extract action items from text."""
    actions = []
    sentences = re.split(r"[.!?\n]", text)
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        sentence_words = set(sentence.lower().split())
        if sentence_words & ACTION_INDICATORS:
            actions.append(sentence)
    return actions


class CommentAnalyzer:
    """Analyzes multiple comments."""
    def __init__(self):
        self._analyses: List[CommentAnalysis] = []

    def analyze(self, text) -> CommentAnalysis:
        """Analyze and store a comment."""
        analysis = analyze_comment(text)
        self._analyses.append(analysis)
        return analysis

    def analyze_batch(self, texts: List[str]) -> List[CommentAnalysis]:
        """Analyze multiple comments."""
        return [self.analyze(t) for t in texts]

    def all_analyses(self):
        return list(self._analyses)

    def count(self):
        return len(self._analyses)

    def positive_count(self):
        return sum(1 for a in self._analyses if a.sentiment == "positive")

    def negative_count(self):
        return sum(1 for a in self._analyses if a.sentiment == "negative")

    def neutral_count(self):
        return sum(1 for a in self._analyses if a.sentiment == "neutral")

    def question_count(self):
        return sum(1 for a in self._analyses if a.has_question)

    def with_action_items(self):
        return [a for a in self._analyses if a.has_action_item]

    def with_mentions(self, username):
        return [a for a in self._analyses if username in a.mentions]

    def clear(self):
        self._analyses = []


def comment_stats(comments: List[str]) -> Dict:
    """Generate engagement statistics for a list of comments."""
    analyses = [analyze_comment(c) for c in comments]
    return {
        "total_comments": len(comments),
        "total_words": sum(a.word_count for a in analyses),
        "avg_word_count": round(sum(a.word_count for a in analyses) / max(len(analyses), 1), 1),
        "questions": sum(1 for a in analyses if a.has_question),
        "action_items": sum(1 for a in analyses if a.has_action_item),
        "mentions": len(set(m for a in analyses for m in a.mentions)),
        "positive": sum(1 for a in analyses if a.sentiment == "positive"),
        "negative": sum(1 for a in analyses if a.sentiment == "negative"),
        "neutral": sum(1 for a in analyses if a.sentiment == "neutral"),
        "avg_sentiment_score": round(
            sum(1 if a.sentiment == "positive" else -1 if a.sentiment == "negative" else 0
                 for a in analyses) / max(len(analyses), 1), 2),
    }


def comment_report(comments: List[str]) -> Dict:
    """Generate a full comment analysis report."""
    stats = comment_stats(comments)
    return {
        "stats": stats,
        "top_mentions": _top_mentions(comments),
        "question_rate": round(stats["questions"] / max(stats["total_comments"], 1) * 100, 1),
        "action_item_rate": round(stats["action_items"] / max(stats["total_comments"], 1) * 100, 1),
    }


def _top_mentions(comments, n=5):
    mention_counts = {}
    for comment in comments:
        for mention in re.findall(r"@([\w\-]+)", comment):
            mention_counts[mention] = mention_counts.get(mention, 0) + 1
    return sorted(mention_counts.items(), key=lambda x: -x[1])[:n]
