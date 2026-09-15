"""ORM model registry — import all models here so Alembic autogenerate sees them."""
from app.database.base import Base
from app.models.file import FileAsset
from app.models.payment import Payment
from app.models.project import Project
from app.models.role import Permission, Role, role_permissions, user_roles
from app.models.token import RefreshToken
from app.models.user import User, UserPhoneNumber

__all__ = [
    "Base", "User", "UserPhoneNumber", "Role", "Permission", "role_permissions", "user_roles",
    "Project", "Payment", "FileAsset", "RefreshToken",
]
