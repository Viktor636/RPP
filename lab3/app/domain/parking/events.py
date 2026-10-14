from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime


@dataclass(frozen=True)
class SessionStarted(DomainEvent):
    session_id: UUID
    spot_id: UUID


@dataclass(frozen=True)
class SessionPaid(DomainEvent):
    session_id: UUID
    amount: str


@dataclass(frozen=True)
class LongTermParkingDetected(DomainEvent):
    session_id: UUID


@dataclass(frozen=True)
class SessionCompleted(DomainEvent):
    session_id: UUID
    spot_id: UUID
    total: str