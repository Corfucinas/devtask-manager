"""Custom exceptions for DevTask Manager."""

class DevTaskError(Exception):
    """Base exception for DevTask errors."""
    pass

class TaskNotFoundError(DevTaskError):
    def __init__(self, task_id):
        self.task_id = task_id
        super().__init__(f"Task #{task_id} not found")

class StorageError(DevTaskError):
    pass

class InvalidPriorityError(DevTaskError):
    pass

class InvalidStatusError(DevTaskError):
    pass
