"""Tests for comment analyzer."""
import pytest
from src.comment_analyzer import (
    CommentAnalysis, analyze_comment, CommentAnalyzer,
    comment_stats, comment_report,
)


def test_analyze_positive():
    result = analyze_comment("This is great, perfect, excellent work!")
    assert result.sentiment == "positive"


def test_analyze_negative():
    result = analyze_comment("This is broken and fails, terrible.")
    assert result.sentiment == "negative"


def test_analyze_neutral():
    result = analyze_comment("The task is done.")
    assert result.sentiment == "neutral"


def test_analyze_question():
    result = analyze_comment("How do we fix this?")
    assert result.has_question is True


def test_analyze_no_question():
    result = analyze_comment("We should fix this.")
    assert result.has_question is False


def test_analyze_mentions():
    result = analyze_comment("Hey @alice and @bob, check this")
    assert "alice" in result.mentions
    assert "bob" in result.mentions


def test_analyze_links():
    result = analyze_comment("See https://example.com for details")
    assert "https://example.com" in result.links


def test_analyze_action_items():
    result = analyze_comment("Please fix this bug immediately")
    assert result.has_action_item is True
    assert len(result.action_items) > 0


def test_analyze_word_count():
    result = analyze_comment("hello world")
    assert result.word_count == 2


def test_analyze_empty():
    result = analyze_comment("")
    assert result.word_count == 0
    assert result.sentiment == "neutral"


def test_analyzer_basic():
    a = CommentAnalyzer()
    a.analyze("Great work!")
    assert a.count() == 1
    assert a.positive_count() == 1


def test_analyzer_batch():
    a = CommentAnalyzer()
    a.analyze_batch(["Good one", "Fix this", "How?", "ok"])
    assert a.count() == 4


def test_analyzer_sentiment_counts():
    a = CommentAnalyzer()
    a.analyze("Great!")
    a.analyze("Bad!")
    a.analyze("Ok")
    assert a.positive_count() == 1
    assert a.negative_count() == 1
    assert a.neutral_count() == 1


def test_analyzer_question_count():
    a = CommentAnalyzer()
    a.analyze("Why?")
    a.analyze("Yes")
    assert a.question_count() == 1


def test_analyzer_with_mentions():
    a = CommentAnalyzer()
    a.analyze("Hi @alice")
    a.analyze("No mentions")
    with_mentions = a.with_mentions("alice")
    assert len(with_mentions) == 1


def test_analyzer_clear():
    a = CommentAnalyzer()
    a.analyze("test")
    a.clear()
    assert a.count() == 0


def test_comment_stats():
    comments = ["Good job!", "Fix this bug @alice", "How do I do this?"]
    stats = comment_stats(comments)
    assert stats["total_comments"] == 3
    assert stats["total_words"] > 0
    assert stats["questions"] == 1
    assert stats["action_items"] == 1


def test_comment_stats_empty():
    stats = comment_stats([])
    assert stats["total_comments"] == 0


def test_comment_report():
    comments = ["Great!", "Bad.", "What?", "Ok"]
    report = comment_report(comments)
    assert "stats" in report
    assert "top_mentions" in report
    assert report["question_rate"] == 25.0
