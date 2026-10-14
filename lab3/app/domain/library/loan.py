from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from app.domain.common.exceptions import DomainInvariantViolation
from app.domain.library.states import (
    Blocked,
    Cancelled,
    Extended,
    Issued,
    LoanState,
    Overdue,
    Rejected,
    Reserved,
    ReturnedDamaged,
    ReturnedFine,
    ReturnedOk,
    STATE_REGISTRY,
)
from app.domain.library.value_objects import (
    BookId,
    CopyId,
    Fine,
    LoanId,
    LoanPeriod,
    ReaderId,
)

DEFAULT_LOAN_DAYS = 14
EXTEND_DAYS = 7
FINE_PER_DAY = Decimal("10")
DAMAGE_FINE = Decimal("500")


class Loan:
    """Aggregate Root: выдача книги.

    Состояние хранится в self._state и меняется ТОЛЬКО через методы событий.
    Публичного сеттера нет — обойти инварианты нельзя.
    """

    def __init__(
        self,
        loan_id: LoanId,
        book_id: BookId,
        reader_id: ReaderId,
        copy_id: CopyId,
        period: LoanPeriod,
        state: LoanState | None = None,
        fine: Fine | None = None,
        returned_at: datetime | None = None,
        issued_at: datetime | None = None,
    ) -> None:
        self._id = loan_id
        self._book_id = book_id
        self._reader_id = reader_id
        self._copy_id = copy_id
        self._period = period
        self._fine = fine or Fine(Decimal("0"))
        self._returned_at = returned_at
        self._issued_at = issued_at
        self._state: LoanState = state or Reserved()

    # --- read-only properties ---
    @property
    def id(self) -> LoanId: return self._id

    @property
    def book_id(self) -> BookId: return self._book_id

    @property
    def reader_id(self) -> ReaderId: return self._reader_id

    @property
    def copy_id(self) -> CopyId: return self._copy_id

    @property
    def period(self) -> LoanPeriod: return self._period

    @property
    def fine(self) -> Fine: return self._fine

    @property
    def state(self) -> LoanState: return self._state

    @property
    def state_name(self) -> str: return self._state.name

    @property
    def is_returned(self) -> bool: return self._returned_at is not None

    @property
    def returned_at(self) -> datetime | None: return self._returned_at

    @property
    def issued_at(self) -> datetime | None: return self._issued_at

    @property
    def due_at(self) -> datetime: return self._period.due_at

    def allowed_events(self) -> tuple[str, ...]:
        return self._state.allowed_events()

    # --- события (делегируют в состояние) ---
    def _apply(self, event_name: str, now: datetime) -> None:
        method = getattr(self._state, f"on_{event_name}")
        self._state = method(self, now)

    def issue(self, now: datetime) -> None:
        self._apply("issue", now)

    def reject(self, now: datetime) -> None:
        self._apply("reject", now)

    def cancel_booking(self, now: datetime) -> None:
        self._apply("cancel_booking", now)

    def extend(self, now: datetime) -> None:
        self._apply("extend", now)

    def return_ok(self, now: datetime) -> None:
        self._apply("return_ok", now)

    def return_damaged(self, now: datetime) -> None:
        self._apply("return_damaged", now)

    def on_due_date_passed(self, now: datetime) -> None:
        self._apply("due_date_passed", now)

    def on_thirty_days_passed(self, now: datetime) -> None:
        self._apply("thirty_days_passed", now)

    # --- «приватные» методы, вызываемые состояниями ---
    def _record_issue(self, now: datetime) -> None:
        self._issued_at = now
        self._period = LoanPeriod(
            started_at=now,
            due_at=now + timedelta(days=DEFAULT_LOAN_DAYS),
        )

    def _extend_period(self, now: datetime, days: int) -> None:
        self._period = LoanPeriod(
            started_at=self._period.started_at,
            due_at=self._period.due_at + timedelta(days=days),
        )

    def _close(self, now: datetime, damaged: bool) -> None:
        if self._returned_at is not None:
            raise DomainInvariantViolation("Выдача уже закрыта")
        self._returned_at = now
        amount = Decimal("0")
        if now > self._period.due_at:
            amount += FINE_PER_DAY * (now - self._period.due_at).days
        if damaged:
            amount += DAMAGE_FINE
        self._fine = Fine(amount)

    # --- восстановление из БД (in-memory) ---
    @classmethod
    def restore(
        cls,
        loan_id: LoanId,
        book_id: BookId,
        reader_id: ReaderId,
        copy_id: CopyId,
        period: LoanPeriod,
        state_name: str,
        fine: Fine,
        returned_at: datetime | None,
        issued_at: datetime | None,
    ) -> "Loan":
        return cls(
            loan_id=loan_id,
            book_id=book_id,
            reader_id=reader_id,
            copy_id=copy_id,
            period=period,
            state=STATE_REGISTRY[state_name](),
            fine=fine,
            returned_at=returned_at,
            issued_at=issued_at,
        )