"""FastAPI dependency for enforcing Permission-Based Access Control (PBAC)."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.permissions.roles import Permission
from app.schemas.auth import CurrentUser


class RequirePermission:
    """Dependency class: raises 403 unless the current user holds ALL given permissions.

    Usage:
        @router.post("/projects", dependencies=[Depends(RequirePermission(Permission.PROJECT_CREATE))])
    """

    def __init__(self, *required: Permission) -> None:
        self.required = set(required)

    def __call__(self, current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.is_superuser:
            return current_user
        if not self.required.issubset(set(current_user.permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user


class RequireRole:
    """Dependency class: raises 403 unless the current user holds one of the given roles."""

    def __init__(self, *allowed_roles: str) -> None:
        self.allowed_roles = set(allowed_roles)

    def __call__(self, current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.is_superuser:
            return current_user
        if not self.allowed_roles.intersection(set(current_user.roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role to perform this action",
            )
        return current_user
