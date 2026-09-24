"""
RBAC — Role-Based Access Control dependency for FastAPI routes.
Usage:
    @router.post("/some-action")
    def my_action(current_user: User = Depends(RequireRole([UserRole.ORG_ADMIN, UserRole.BLOOD_BANK_MANAGER]))):
        ...
"""
from typing import List
from fastapi import Depends, HTTPException, status
from app.security.auth import get_current_active_user
from app.models.users import User, UserRole


class RequireRole:
    """Dependency that enforces role-based access control on any endpoint."""

    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "message": (
                            f"This action requires one of the following roles: "
                            f"{[r.value for r in self.allowed_roles]}. "
                            f"Your role is: {current_user.role.value}."
                        ),
                    }
                },
            )
        return current_user


def require_org_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Shorthand: only Platform Admin or Org Admin."""
    return RequireRole([UserRole.PLATFORM_ADMIN, UserRole.ORG_ADMIN])(current_user)


def require_manager(current_user: User = Depends(get_current_active_user)) -> User:
    """Shorthand: Org Admin, Blood Bank Manager, or Hospital Manager."""
    return RequireRole([
        UserRole.PLATFORM_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.BLOOD_BANK_MANAGER,
        UserRole.HOSPITAL_MANAGER,
    ])(current_user)


def require_logistics(current_user: User = Depends(get_current_active_user)) -> User:
    """Shorthand: Anyone who can initiate transfers."""
    return RequireRole([
        UserRole.PLATFORM_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.BLOOD_BANK_MANAGER,
        UserRole.HOSPITAL_MANAGER,
        UserRole.LOGISTICS_COORDINATOR,
    ])(current_user)
