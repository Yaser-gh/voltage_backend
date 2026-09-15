"""Shared base schemas used across multiple domain schema modules."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    """Base schema for models read out of the ORM (enables `from_attributes`)."""
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(ORMBase):
    """Adds standard audit timestamp fields to a response schema."""
    id: UUID
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Generic simple message response, e.g. for delete/action endpoints."""
    message: str
