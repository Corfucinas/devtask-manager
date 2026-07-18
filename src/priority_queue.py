"""Priority queue for task processing."""
import heapq
from .models import Task, Priority, Status

PRIORITY_WEIGHTS = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}

class TaskPriorityQueue:
    def __init__(self):
        self._heap = []
        self._counter = 0
    def push(self, task):
        weight = PRIORITY_WEIGHTS.get(task.priority, 99)
        heapq.heappush(self._heap, (weight, self._counter, task))
        self._counter += 1
    def pop(self):
        if not self._heap: return None
        return heapq.heappop(self._heap)[2]
    def peek(self):
        return self._heap[0][2] if self._heap else None
    def is_empty(self):
        return len(self._heap) == 0
    def size(self):
        return len(self._heap)
    def drain(self):
        tasks = []
        while not self.is_empty(): tasks.append(self.pop())
        return tasks
    def remove(self, task_id):
        self._heap = [(w, c, t) for w, c, t in self._heap if t.id != task_id]
        heapq.heapify(self._heap)

def build_queue_from_tasks(tasks):
    pq = TaskPriorityQueue()
    for t in tasks:
        if t.status != Status.DONE: pq.push(t)
    return pq
