from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------- Library ----------
class CreateLoanRequest(BaseModel):
    book_id: UUID
    reader_id: UUID
    copy_id: UUID


class IssueLoanRequest(BaseModel):
    has_overdue: bool = False
    has_unpaid_fine: bool = False


class ExtendLoanRequest(BaseModel):
    has_queue: bool = False


class ReturnLoanRequest(BaseModel):
    damaged: bool = False


class LoanResponse(BaseModel):
    id: UUID
    book_id: UUID
    reader_id: UUID
    copy_id: UUID
    state: str
    allowed_events: list[str]
    fine: str
    started_at: datetime
    due_at: datetime
    returned_at: datetime | None


# ---------- Parking ----------
class StartSessionRequest(BaseModel):
    spot_id: UUID
    license_plate: str
    blocklist: list[str] = Field(default_factory=list)


class PayRequest(BaseModel):
    amount: str


class SessionResponse(BaseModel):
    id: UUID
    spot_id: UUID
    license_plate: str
    state: str
    allowed_events: list[str]
    started_at: datetime
    finished_at: datetime | None
    total_paid: str
    exit_window_closes_at: datetime | None


# ---------- Служебные ----------
class TickRequest(BaseModel):
    now: datetime | None = None


class ErrorResponse(BaseModel):
    error: str
    message: str