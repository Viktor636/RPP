from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.common.exceptions import DomainInvariantViolation
from app.domain.library.events import (
    BookIssued,
    BookReturned,
    DomainEvent,
    ReaderCardBlocked,
    ReminderSent,
)
from app.domain.library.loan import Loan

THREE_WORKING_DAYS = timedelta(days=3)
REMINDER_BEFORE_DUE = timedelta(days=2)
THIRTY_DAYS = timedelta(days=30)


class LendingProcess:
    """Процесс выдачи книги. Состояние Loan меняется только через события агрегата."""

    def __init__(self, events: list[DomainEvent] | None = None) -> None:
        self._events: list[DomainEvent] = events or []

    @property
    def events(self) -> list[DomainEvent]:
        return self._events

    # --- Предикаты шлюзов ---
    @staticmethod
    def has_debt(has_overdue: bool, has_unpaid_fine: bool) -> bool:
        return has_overdue or has_unpaid_fine

    @staticmethod
    def booking_expired(created_at: datetime, now: datetime) -> bool:
        return now > created_at + THREE_WORKING_DAYS

    @staticmethod
    def is_book_damaged(report_damaged: bool) -> bool:
        return report_damaged

    @staticmethod
    def is_overdue(loan: Loan, now: datetime) -> bool:
        return now > loan.due_at

    @staticmethod
    def is_thirty_days_overdue(loan: Loan, now: datetime) -> bool:
        return now > loan.due_at + THIRTY_DAYS

    # --- Задачи BPMN ---
    def check_reader_debt(
        self,
        loan: Loan,
        has_overdue: bool,
        has_unpaid_fine: bool,
        now: datetime,
    ) -> None:
        if self.has_debt(has_overdue, has_unpaid_fine):
            loan.reject(now)
        else:
            loan.issue(now)
            self._events.append(
                BookIssued(
                    occurred_at=now,
                    loan_id=loan.id.value,
                    book_id=loan.book_id.value,
                )
            )

    def handle_booking_timeout(
        self, loan: Loan, created_at: datetime, now: datetime
    ) -> None:
        if self.booking_expired(created_at, now):
            loan.cancel_booking(now)

    def send_reminder(self, loan: Loan, now: datetime) -> None:
        if loan.state_name not in ("Issued", "Extended"):
            return
        if now >= loan.due_at - REMINDER_BEFORE_DUE:
            self._events.append(
                ReminderSent(
                    occurred_at=now,
                    loan_id=loan.id.value,
                    reader_id=loan.reader_id.value,
                )
            )

    def extend_loan(self, loan: Loan, has_queue: bool, now: datetime) -> None:
        if has_queue:
            raise DomainInvariantViolation("Продление невозможно: есть очередь")
        loan.extend(now)

    def accept_return(self, loan: Loan, report_damaged: bool, now: datetime) -> None:
        if self.is_book_damaged(report_damaged):
            loan.return_damaged(now)
        else:
            loan.return_ok(now)
        self._events.append(
            BookReturned(
                occurred_at=now,
                loan_id=loan.id.value,
                with_damage=report_damaged,
            )
        )

    def on_due_date_passed(self, loan: Loan, now: datetime) -> None:
        loan.on_due_date_passed(now)

    def escalate_overdue(self, loan: Loan, now: datetime) -> None:
        if self.is_thirty_days_overdue(loan, now):
            loan.on_thirty_days_passed(now)
            self._events.append(
                ReaderCardBlocked(
                    occurred_at=now,
                    reader_id=loan.reader_id.value,
                    loan_id=loan.id.value,
                )
            )