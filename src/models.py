"""Task model with priority, status, and tags."""

from datetime import datetime, timezone
from enum import Enum


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_string(cls, value):
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Invalid priority: {value}. Use: {', '.join(p.value for p in cls)}"
            )


class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    DONE = "done"

    @classmethod
    def from_string(cls, value):
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Invalid status: {value}. Use: {', '.join(s.value for s in cls)}"
            )


class Task:
    def __init__(
        self,
        id,
        title,
        description="",
        priority=Priority.MEDIUM,
        status=Status.TODO,
        tags=None,
        created_at=None,
        updated_at=None,
    ):
        self.id = id
        self.title = title
        self.description = description
        self.priority = priority
        self.status = status
        self.tags = tags or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            priority=Priority(data.get("priority", "medium")),
            status=Status(data.get("status", "todo")),
            tags=data.get("tags", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def update(self, **kwargs):
        if "title" in kwargs:
            self.title = kwargs["title"]
        if "description" in kwargs:
            self.description = kwargs["description"]
        if "priority" in kwargs:
            self.priority = Priority.from_string(kwargs["priority"])
        if "status" in kwargs:
            self.status = Status.from_string(kwargs["status"])
        if "tags" in kwargs:
            self.tags = kwargs["tags"]
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def __repr__(self):
        return f"Task(id={self.id}, title='{self.title}', status={self.status.value}, priority={self.priority.value})"
