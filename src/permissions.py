"""Role-based access control for task operations."""
from enum import Enum
from typing import Dict, Set


class Role(Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(Enum):
    """Task operations that can be permitted."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ASSIGN = "assign"
    MERGE = "merge"


DEFAULT_MATRIX: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {Permission.CREATE, Permission.READ, Permission.UPDATE,
                 Permission.DELETE, Permission.ASSIGN, Permission.MERGE},
    Role.DEVELOPER: {Permission.CREATE, Permission.READ, Permission.UPDATE, Permission.ASSIGN},
    Role.VIEWER: {Permission.READ},
    Role.GUEST: set(),
}


class RoleMatrix:
    """Configurable permission matrix for roles."""

    def __init__(self, matrix: Dict[Role, Set[Permission]] = None):
        self._matrix = matrix or {r: set(p) for r, p in DEFAULT_MATRIX.items()}

    def grant(self, role: Role, permission: Permission) -> None:
        if role not in self._matrix:
            self._matrix[role] = set()
        self._matrix[role].add(permission)

    def revoke(self, role: Role, permission: Permission) -> None:
        if role in self._matrix:
            self._matrix[role].discard(permission)

    def has_permission(self, role: Role, permission: Permission) -> bool:
        return permission in self._matrix.get(role, set())

    def permissions_for(self, role: Role) -> Set[Permission]:
        return set(self._matrix.get(role, set()))

    def roles_with_permission(self, permission: Permission) -> list:
        return [role for role, perms in self._matrix.items() if permission in perms]

    def to_dict(self) -> dict:
        return {
            role.value: [p.value for p in sorted(perms, key=lambda x: x.value)]
            for role, perms in self._matrix.items()
        }


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role has a permission using the default matrix."""
    return permission in DEFAULT_MATRIX.get(role, set())


def filter_by_permission(tasks, role: Role, permission: Permission) -> list:
    """Filter tasks based on what a role can access."""
    if not has_permission(role, Permission.READ):
        return []
    if permission == Permission.UPDATE:
        if not has_permission(role, permission):
            return [t for t in tasks
                    if (t.status.value if hasattr(t.status, "value") else t.status) == "done"]
    return list(tasks)


def can_create(role: Role) -> bool:
    return has_permission(role, Permission.CREATE)


def can_delete(role: Role) -> bool:
    return has_permission(role, Permission.DELETE)


def can_merge(role: Role) -> bool:
    return has_permission(role, Permission.MERGE)


def role_from_string(value: str) -> Role:
    try:
        return Role(value.lower())
    except ValueError:
        raise ValueError(
            f"Invalid role: {value}. Use: {', '.join(r.value for r in Role)}"
        )


def permission_from_string(value: str) -> Permission:
    try:
        return Permission(value.lower())
    except ValueError:
        raise ValueError(
            f"Invalid permission: {value}. Use: {', '.join(p.value for p in Permission)}"
        )
