"""Project domain request/response schemas."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.constants import ProjectStatus
from app.schemas.common import ORMBase
from app.validators.common import validate_positive_amount


class ProjectCreateRequest(BaseModel):
    """Payload for creating a new project under a given owner (user)."""
    owner_id: UUID
    name: str = Field(..., min_length=2, max_length=200)
    address: str = Field(..., min_length=2, max_length=500)
    description: str | None = Field(None, max_length=5000)
    contract_date: date | None = None
    contract_end_date: date | None = None
    base_price: float = Field(..., gt=0)

    @field_validator("base_price")
    @classmethod
    def _check_price(cls, v: float) -> float:
        return validate_positive_amount(v)

    @model_validator(mode="after")
    def _check_dates(self) -> "ProjectCreateRequest":
        if self.contract_date and self.contract_end_date and self.contract_end_date < self.contract_date:
            raise ValueError("contract_end_date cannot be before contract_date")
        return self


class ProjectUpdateRequest(BaseModel):
    """Payload for updating an existing project. All fields optional (partial update)."""
    name: str | None = Field(None, min_length=2, max_length=200)
    address: str | None = Field(None, min_length=2, max_length=500)
    description: str | None = Field(None, max_length=5000)
    contract_date: date | None = None
    contract_end_date: date | None = None
    base_price: float | None = Field(None, gt=0)

    @field_validator("base_price")
    @classmethod
    def _check_price(cls, v: float | None) -> float | None:
        return validate_positive_amount(v) if v is not None else None


class ProjectStatusUpdateRequest(BaseModel):
    """Payload for explicit status-transition endpoints (start/stop/finish/mark-bad/restore)."""
    reason: str | None = Field(None, max_length=1000, description="Optional note explaining the status change")


class ProjectOwnerSummary(ORMBase):
    """Minimal owner (user) representation embedded in project responses."""
    u_id: UUID = Field(alias="id")
    first_name: str
    last_name: str
    username: str


class ProjectResponse(ORMBase):
    """Full project representation returned by detail endpoints."""
    u_id: UUID = Field(alias='id')
    owner: ProjectOwnerSummary
    name: str
    address: str
    description: str | None
    contract_date: date | None
    contract_end_date: date | None
    base_price: float
    total_paid: float
    status: ProjectStatus
    files_count: int = 0
    payments_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectListItemResponse(ORMBase):
    """Condensed project representation for list/grid endpoints."""
    u_id: UUID = Field(alias="id")
    name: str
    address: str
    owner: ProjectOwnerSummary
    base_price: float
    total_paid: float
    status: ProjectStatus
    contract_date: date | None
    created_at: datetime
