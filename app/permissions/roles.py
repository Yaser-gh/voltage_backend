"""Static role and permission definitions for the RBAC system."""
from enum import Enum


class RoleName(str, Enum):
    """Built-in system roles. Custom roles may also be created in the DB at runtime."""
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Fine-grained permission codes, assignable to roles.

    Naming convention: `<resource>:<action>`.
    """
    # Users
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"

    # Projects
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_LIST = "project:list"
    PROJECT_CHANGE_STATUS = "project:change_status"

    # Payments
    PAYMENT_CREATE = "payment:create"
    PAYMENT_READ = "payment:read"
    PAYMENT_UPDATE = "payment:update"
    PAYMENT_DELETE = "payment:delete"
    PAYMENT_LIST = "payment:list"

    # Files
    FILE_UPLOAD = "file:upload"
    FILE_READ = "file:read"
    FILE_DELETE = "file:delete"

    # Dashboard
    DASHBOARD_READ = "dashboard:read"

    # Admin-only
    ROLE_MANAGE = "role:manage"


# Default role -> permission mapping. Seed data / migrations should persist this
# to the `roles` / `permissions` / `role_permissions` tables; this constant is
# the single source of truth referenced by seed scripts.
DEFAULT_ROLE_PERMISSIONS: dict[RoleName, list[Permission]] = {
    RoleName.ADMIN: list(Permission),  # all permissions
    RoleName.MANAGER: [
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_LIST,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE, Permission.PROJECT_LIST, Permission.PROJECT_CHANGE_STATUS,
        Permission.PAYMENT_CREATE, Permission.PAYMENT_READ, Permission.PAYMENT_UPDATE,
        Permission.PAYMENT_DELETE, Permission.PAYMENT_LIST,
        Permission.FILE_UPLOAD, Permission.FILE_READ, Permission.FILE_DELETE,
        Permission.DASHBOARD_READ,
    ],
    RoleName.EMPLOYEE: [
        Permission.USER_READ, Permission.USER_LIST,
        Permission.PROJECT_READ, Permission.PROJECT_LIST, Permission.PROJECT_UPDATE,
        Permission.PAYMENT_CREATE, Permission.PAYMENT_READ, Permission.PAYMENT_LIST,
        Permission.FILE_UPLOAD, Permission.FILE_READ,
        Permission.DASHBOARD_READ,
    ],
    RoleName.VIEWER: [
        Permission.USER_READ, Permission.USER_LIST,
        Permission.PROJECT_READ, Permission.PROJECT_LIST,
        Permission.PAYMENT_READ, Permission.PAYMENT_LIST,
        Permission.FILE_READ,
        Permission.DASHBOARD_READ,
    ],
}
