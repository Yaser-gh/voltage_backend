"""Payment domain request/response schemas."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMBase
from app.validators.common import (
    validate_bank_account_number,
    validate_bank_name,
    validate_not_future_date,
    validate_positive_amount,
)


class PaymentCreateRequest(BaseModel):
    """Payload for recording a new payment against a project."""
    project_id: UUID
    amount: float = Field(..., gt=0)
    bank_name: str = Field(..., min_length=2, max_length=100)
    account_number: str = Field(..., min_length=5, max_length=50)
    description: str | None = Field(None, max_length=1000)
    paid_at: date

    @field_validator("amount")
    @classmethod
    def _check_amount(cls, v: float) -> float:
        return validate_positive_amount(v)

    @field_validator("bank_name")
    @classmethod
    def _check_bank(cls, v: str) -> str:
        return validate_bank_name(v)

    @field_validator("account_number")
    @classmethod
    def _check_account(cls, v: str) -> str:
        return validate_bank_account_number(v)

    @field_validator("paid_at")
    @classmethod
    def _check_paid_at(cls, v: date) -> date:
        return validate_not_future_date(v)


class PaymentUpdateRequest(BaseModel):
    """Payload for updating an existing payment. All fields optional (partial update)."""
    amount: float | None = Field(None, gt=0)
    bank_name: str | None = Field(None, min_length=2, max_length=100)
    account_number: str | None = Field(None, min_length=5, max_length=50)
    description: str | None = Field(None, max_length=1000)
    paid_at: date | None = None

    @field_validator("amount")
    @classmethod
    def _check_amount(cls, v: float | None) -> float | None:
        return validate_positive_amount(v) if v is not None else None

    @field_validator("bank_name")
    @classmethod
    def _check_bank(cls, v: str | None) -> str | None:
        return validate_bank_name(v) if v is not None else None

    @field_validator("account_number")
    @classmethod
    def _check_account(cls, v: str | None) -> str | None:
        return validate_bank_account_number(v) if v is not None else None

    @field_validator("paid_at")
    @classmethod
    def _check_paid_at(cls, v: date | None) -> date | None:
        return validate_not_future_date(v) if v is not None else None


class PaymentProjectSummary(ORMBase):
    """Minimal project representation embedded in payment responses."""
    id: UUID
    name: str


class PaymentResponse(ORMBase):
    """Full payment representation returned by detail endpoints."""
    id: UUID
    project: PaymentProjectSummary
    amount: float
    bank_name: str
    account_number: str
    description: str | None
    receipt_created_at: date
    paid_at: date
    files_count: int = 0
    created_at: datetime
    updated_at: datetime


class PaymentListItemResponse(ORMBase):
    """Condensed payment representation for list endpoints."""
    id: UUID
    project: PaymentProjectSummary
    amount: float
    bank_name: str
    paid_at: date
    created_at: datetime


class TotalPaymentsResponse(BaseModel):
    """Aggregate total-payments response (system-wide or scoped)."""
    total_amount: float
    count: int
    scope: str = Field(..., description="e.g. 'system', 'project:<id>', 'user:<id>'")
