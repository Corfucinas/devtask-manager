"""Tests for code review tracking."""
import pytest
from src.review import (
    Review, request_review, approve_review, request_changes,
    add_comment, review_status, blocking_reviews, approved_reviews,
    pending_reviews, review_count, is_ready_to_merge,
)


class FakeTask:
    def __init__(self):
        self.reviews = None


@pytest.fixture
def task():
    t = FakeTask()
    request_review(t, "alice")
    request_review(t, "bob")
    return t


def test_request_review():
    t = FakeTask()
    r = request_review(t, "alice")
    assert r.id == 1
    assert r.reviewer == "alice"
    assert r.status == "pending"
    assert len(t.reviews) == 1


def test_approve_review(task):
    approve_review(task.reviews[0])
    assert task.reviews[0].status == "approved"
    assert task.reviews[0].updated_at is not None


def test_request_changes(task):
    request_changes(task.reviews[1], "Fix the bug")
    assert task.reviews[1].status == "changes_requested"
    assert "Fix the bug" in task.reviews[1].comments


def test_add_comment(task):
    add_comment(task.reviews[0], "Looks good mostly")
    assert "Looks good mostly" in task.reviews[0].comments


def test_review_status_no_reviews():
    t = FakeTask()
    assert review_status(t) == "no_reviews"


def test_review_status_pending(task):
    assert review_status(task) == "pending"


def test_review_status_approved(task):
    approve_review(task.reviews[0])
    approve_review(task.reviews[1])
    assert review_status(task) == "approved"


def test_review_status_blocked(task):
    request_changes(task.reviews[0])
    assert review_status(task) == "blocked"


def test_blocking_reviews(task):
    request_changes(task.reviews[0])
    blocking = blocking_reviews(task)
    assert len(blocking) == 1
    assert blocking[0].reviewer == "alice"


def test_approved_reviews(task):
    approve_review(task.reviews[0])
    approved = approved_reviews(task)
    assert len(approved) == 1


def test_pending_reviews(task):
    pending = pending_reviews(task)
    assert len(pending) == 2


def test_review_count(task):
    assert review_count(task) == 2


def test_is_ready_to_merge(task):
    assert is_ready_to_merge(task) is False
    approve_review(task.reviews[0])
    approve_review(task.reviews[1])
    assert is_ready_to_merge(task) is True


def test_is_ready_to_merge_blocked(task):
    approve_review(task.reviews[0])
    request_changes(task.reviews[1])
    assert is_ready_to_merge(task) is False


def test_is_ready_to_merge_multiple_approvals():
    t = FakeTask()
    request_review(t, "alice")
    request_review(t, "bob")
    request_review(t, "charlie")
    approve_review(t.reviews[0])
    approve_review(t.reviews[1])
    approve_review(t.reviews[2])
    assert is_ready_to_merge(t, required_approvals=2) is True
