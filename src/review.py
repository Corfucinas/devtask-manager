"""Code review tracking and approval."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Review:
    """A single code review on a task."""
    id: int
    reviewer: str
    status: str = "pending"
    comments: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


def request_review(task, reviewer: str) -> Review:
    """Request a review on a task from a specific reviewer."""
    if not hasattr(task, "reviews") or task.reviews is None:
        task.reviews = []
    review_id = max((r.id for r in task.reviews), default=0) + 1
    review = Review(id=review_id, reviewer=reviewer)
    task.reviews.append(review)
    return review


def approve_review(review: Review) -> Review:
    """Mark a review as approved."""
    review.status = "approved"
    review.updated_at = datetime.now(timezone.utc).isoformat()
    return review


def request_changes(review: Review, comment: str = "") -> Review:
    """Mark a review as requesting changes."""
    review.status = "changes_requested"
    review.updated_at = datetime.now(timezone.utc).isoformat()
    if comment:
        review.comments.append(comment)
    return review


def add_comment(review: Review, comment: str) -> None:
    """Add a comment to a review."""
    review.comments.append(comment)
    review.updated_at = datetime.now(timezone.utc).isoformat()


def review_status(task) -> str:
    """Aggregate review state for a task."""
    reviews = getattr(task, "reviews", None) or []
    if not reviews:
        return "no_reviews"
    if any(r.status == "changes_requested" for r in reviews):
        return "blocked"
    if all(r.status == "approved" for r in reviews):
        return "approved"
    if any(r.status == "pending" for r in reviews):
        return "pending"
    return "reviewed"


def blocking_reviews(task) -> List[Review]:
    """Return reviews that have changes_requested status."""
    reviews = getattr(task, "reviews", None) or []
    return [r for r in reviews if r.status == "changes_requested"]


def approved_reviews(task) -> List[Review]:
    """Return reviews that have been approved."""
    reviews = getattr(task, "reviews", None) or []
    return [r for r in reviews if r.status == "approved"]


def pending_reviews(task) -> List[Review]:
    """Return reviews that are still pending."""
    reviews = getattr(task, "reviews", None) or []
    return [r for r in reviews if r.status == "pending"]


def review_count(task) -> int:
    """Return total number of reviews on a task."""
    reviews = getattr(task, "reviews", None) or []
    return len(reviews)


def is_ready_to_merge(task, required_approvals: int = 1) -> bool:
    """Check if a task has enough approvals to merge."""
    return len(approved_reviews(task)) >= required_approvals and not blocking_reviews(task)
