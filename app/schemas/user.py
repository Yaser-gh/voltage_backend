"""User domain request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import ORMBase
from app.validators.common import (
    validate_biography,
    validate_password_strength,
    validate_phone,
    validate_username,
)
from app.core.constants import DEFAULT_LIMIT, DEFAULT_PAGE, MAX_LIMIT


class PhoneNumberCreate(BaseModel):
    """Payload for adding a secondary phone number to a user."""
    phone: str
    label: str | None = Field(None, max_length=50)

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, v: str) -> str:
        return validate_phone(v)


class PhoneNumberResponse(ORMBase):
    """A secondary phone number belonging to a user."""
    id: UUID
    phone: str
    label: str | None

class GetUsersRequest(BaseModel):
    offset: ini | None = Field(DEFAULT_PAGE, ge=1, description="Page number, 1-indexed")
    limit: int | None = Field(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Items per page.")
    is_active: bool | None = None
    is_pinned: bool | None = None
    is_verified: bool | None = None
    search_text: str | None = None
    sort_by: str | None = Field(None, description="Field name to sort by")
    sort_order: Literal["asc", "desc"] = Field("desc", description="Sort direction")

class GetUserInfoRequest(BaseModel):
    user_id: UUID

class UserCreateRequest(BaseModel):
    """Payload for creating a new user (admin/manager action)."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr | None = None
    phone: str
    password: str = Field(..., min_length=8, max_length=128)
    biography: str | None = Field(None, max_length=2000)
    role_ids: list[UUID] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("username")
    @classmethod
    def _check_username(cls, v: str) -> str:
        return validate_username(v)

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, v: str) -> str:
        return validate_phone(v)

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("biography")
    @classmethod
    def _check_bio(cls, v: str | None) -> str | None:
        return validate_biography(v)


class UserUpdateRequest(BaseModel):
    """Payload for updating an existing user. All fields optional (partial update)."""
    user_id: UUID
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    biography: str | None = Field(None, max_length=2000)
    is_active: bool | None = None
    role_ids: list[UUID] | None = None

    @field_validator("biography")
    @classmethod
    def _check_bio(cls, v: str | None) -> str | None:
        return validate_biography(v)


class UpdateBiographyRequest(BaseModel):
    """Payload for the dedicated 'update biography' endpoint."""
    biography: str | None = Field(None, max_length=2000)

    @field_validator("biography")
    @classmethod
    def _check_bio(cls, v: str | None) -> str | None:
        return validate_biography(v)


class UpdatePhoneRequest(BaseModel):
    """Payload for updating a user's primary phone number."""
    phone: str

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, v: str) -> str:
        return validate_phone(v)


class RoleSummary(ORMBase):
    """Minimal role representation embedded in user responses."""
    id: UUID
    name: str


class UserResponse(ORMBase):
    """Full user representation returned by detail endpoints."""
    id: UUID
    first_name: str
    last_name: str
    username: str
    email: str | None
    phone: str
    biography: str | None
    avatar_url: str | None = None
    is_active: bool
    is_verified: bool
    roles: list[RoleSummary] = []
    phone_numbers: list[PhoneNumberResponse] = []
    total_payments: float
    last_payment_at: datetime | None
    projects_count: int = 0
    created_at: datetime
    updated_at: datetime


class UserListItemResponse(ORMBase):
    """Condensed user representation for list/table endpoints."""
    id: UUID
    first_name: str
    last_name: str
    username: str
    phone: str
    avatar_url: str | None = None
    is_active: bool
    total_payments: float
    last_payment_at: datetime | None
    projects_count: int = 0
    created_at: datetime


class UserPaymentSummaryResponse(BaseModel):
    """Response for the 'total payments' / 'last payment' summary endpoints."""
    user_id: UUID
    total_payments: float
    last_payment_at: datetime | None
    last_payment_amount: float | None = None


class UserProjectsCountResponse(BaseModel):
    """Response for the 'projects count' endpoint."""
    user_id: UUID
    projects_count: int
    active_count: int = 0
    finished_count: int = 0
    stopped_count: int = 0
    bad_count: int = 0
