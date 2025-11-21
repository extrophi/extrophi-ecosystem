"""
A01:2021 - Broken Access Control
Role-Based Access Control (RBAC) Implementation
"""

from enum import Enum
from typing import Set


class Role(Enum):
    """User roles with different permission levels."""

    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class Permission(Enum):
    """Available permissions in the system."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


# Role-to-Permission mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN},
    Role.USER: {Permission.READ, Permission.WRITE},
    Role.READONLY: {Permission.READ},
}


def has_permission(user_role: Role, required_permission: Permission) -> bool:
    """
    Check if a role has the required permission.

    Args:
        user_role: The user's role
        required_permission: The permission required for the action

    Returns:
        bool: True if the role has the permission, False otherwise

    Example:
        >>> has_permission(Role.ADMIN, Permission.DELETE)
        True
        >>> has_permission(Role.READONLY, Permission.WRITE)
        False
    """
    return required_permission in ROLE_PERMISSIONS.get(user_role, set())


def get_user_permissions(user_role: Role) -> Set[Permission]:
    """
    Get all permissions for a given role.

    Args:
        user_role: The user's role

    Returns:
        Set[Permission]: Set of permissions for the role
    """
    return ROLE_PERMISSIONS.get(user_role, set())


def require_permission(user_role: Role, required_permission: Permission) -> None:
    """
    Raise an exception if the user doesn't have the required permission.

    Args:
        user_role: The user's role
        required_permission: The permission required for the action

    Raises:
        PermissionError: If the user doesn't have the required permission
    """
    if not has_permission(user_role, required_permission):
        raise PermissionError(
            f"Role '{user_role.value}' does not have '{required_permission.value}' permission"
        )
