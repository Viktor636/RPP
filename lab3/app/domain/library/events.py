from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime


@dataclass(frozen=True)
class BookIssued(DomainEvent):
    loan_id: UUID
    book_id: UUID


@dataclass(frozen=True)
class BookReturned(DomainEvent):
    loan_id: UUID
    with_damage: bool


@dataclass(frozen=True)
class ReminderSent(DomainEvent):
    loan_id: UUID
    reader_id: UUID


@dataclass(frozen=True)
class ReaderCardBlocked(DomainEvent):
    reader_id: UUID
    loan_id: UUID