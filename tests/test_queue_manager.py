"""Tests for task queue manager."""
import pytest
from src.queue_manager import TaskQueue, QueueItem, queue_stats


@pytest.fixture
def queue():
    q = TaskQueue()
    q.enqueue(1, "medium")
    q.enqueue(2, "high")
    q.enqueue(3, "low")
    q.enqueue(4, "critical")
    return q


def test_enqueue():
    q = TaskQueue()
    item = q.enqueue(1, "high")
    assert item.task_id == 1
    assert q.size() == 1


def test_dequeue_priority(queue):
    item = queue.dequeue()
    assert item.task_id == 4  # critical first
    item2 = queue.dequeue()
    assert item2.task_id == 2  # high second


def test_dequeue_empty():
    q = TaskQueue()
    assert q.dequeue() is None


def test_peek_next(queue):
    item = queue.peek_next()
    assert item is not None
    assert item.task_id == 4  # critical
    assert queue.size() == 4  # not removed


def test_peek_empty():
    q = TaskQueue()
    assert q.peek_next() is None


def test_remove(queue):
    assert queue.remove(2) is True
    assert queue.size() == 3
    assert queue.remove(999) is False


def test_size(queue):
    assert queue.size() == 4


def test_is_empty():
    q = TaskQueue()
    assert q.is_empty() is True
    q.enqueue(1)
    assert q.is_empty() is False


def test_all_items_sorted(queue):
    items = queue.all_items()
    assert items[0].priority == "critical"
    assert items[-1].priority == "low"


def test_by_priority(queue):
    high_items = queue.by_priority("high")
    assert len(high_items) == 1
    assert high_items[0].task_id == 2


def test_clear(queue):
    queue.clear()
    assert queue.size() == 0
    assert queue.dequeued_count() == 0


def test_dequeued_count(queue):
    queue.dequeue()
    assert queue.dequeued_count() == 1


def test_requeue(queue):
    item = queue.dequeue()
    assert queue.requeue(item.task_id) is True
    assert queue.size() == 4
    assert queue.requeue(999) is False


def test_requeue_with_new_priority(queue):
    item = queue.dequeue()
    queue.requeue(item.task_id, priority="low")
    items = queue.by_priority("low")
    assert any(i.task_id == item.task_id for i in items)


def test_fifo_same_priority():
    q = TaskQueue()
    q.enqueue(1, "medium")
    q.enqueue(2, "medium")
    q.enqueue(3, "medium")
    assert q.dequeue().task_id == 1
    assert q.dequeue().task_id == 2
    assert q.dequeue().task_id == 3


def test_queue_stats(queue):
    stats = queue_stats(queue)
    assert stats["size"] == 4
    assert stats["by_priority"]["critical"] == 1
    assert stats["next_task"] == 4
