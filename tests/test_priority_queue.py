"""Tests for priority queue."""
import pytest
from src.models import Task, Priority, Status
from src.priority_queue import TaskPriorityQueue, build_queue_from_tasks

class TestTaskPriorityQueue:
    def test_push_pop(self):
        pq = TaskPriorityQueue()
        pq.push(Task(id=1, title="Low", priority=Priority.LOW))
        pq.push(Task(id=2, title="Critical", priority=Priority.CRITICAL))
        assert pq.pop().title == "Critical"
        assert pq.pop().title == "Low"
    def test_empty(self):
        pq = TaskPriorityQueue()
        assert pq.is_empty()
        assert pq.pop() is None
    def test_peek(self):
        pq = TaskPriorityQueue()
        pq.push(Task(id=1, title="High", priority=Priority.HIGH))
        assert pq.peek().title == "High"
    def test_drain(self):
        pq = TaskPriorityQueue()
        pq.push(Task(id=1, title="A", priority=Priority.LOW))
        pq.push(Task(id=2, title="B", priority=Priority.HIGH))
        tasks = pq.drain()
        assert tasks[0].title == "B"
        assert pq.is_empty()
    def test_remove(self):
        pq = TaskPriorityQueue()
        pq.push(Task(id=1, title="A", priority=Priority.HIGH))
        pq.push(Task(id=2, title="B", priority=Priority.LOW))
        pq.remove(1)
        assert pq.size() == 1

class TestBuildQueue:
    def test_excludes_done(self):
        tasks = [Task(id=1, title="Active", priority=Priority.HIGH), Task(id=2, title="Done", status=Status.DONE, priority=Priority.CRITICAL)]
        pq = build_queue_from_tasks(tasks)
        assert pq.size() == 1
