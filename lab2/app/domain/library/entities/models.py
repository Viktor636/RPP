from datetime import datetime
from decimal import Decimal

from ..exceptions.exceptions import DomainInvariantViolation
from ..value_objects.values import (
    BookId,
    CopyId,
    Fine,
    LoanId,
    LoanPeriod,
    ReaderId,
)


class Book:
    """
    Aggregate Root книги.
    """

    def __init__(
        self,
        book_id: BookId,
        title: str,
        copies: set[CopyId],
        borrowed_copies: set[CopyId] | None = None,
    ):
        if not title.strip():
            raise DomainInvariantViolation(
                "Название книги не может быть пустым"
            )

        if not copies:
            raise DomainInvariantViolation(
                "У книги должен быть хотя бы один экземпляр"
            )

        borrowed_copies = borrowed_copies or set()

        if not borrowed_copies.issubset(copies):
            raise DomainInvariantViolation(
                "Выданный экземпляр должен принадлежать книге"
            )

        self._id = book_id
        self._title = title
        self._copies = set(copies)
        self._borrowed_copies = set(borrowed_copies)

    @property
    def id(self) -> BookId:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def available_copies(self) -> int:
        return len(self._copies - self._borrowed_copies)

    def can_borrow(self, copy_id: CopyId) -> bool:
        return (
            copy_id in self._copies
            and copy_id not in self._borrowed_copies
        )

    def borrow_copy(self, copy_id: CopyId) -> None:
        if copy_id not in self._copies:
            raise DomainInvariantViolation(
                "Такого экземпляра книги не существует"
            )

        if copy_id in self._borrowed_copies:
            raise DomainInvariantViolation(
                "Этот экземпляр уже выдан"
            )

        self._borrowed_copies.add(copy_id)

    def return_copy(self, copy_id: CopyId) -> None:
        if copy_id not in self._borrowed_copies:
            raise DomainInvariantViolation(
                "Этот экземпляр сейчас не выдан"
            )

        self._borrowed_copies.remove(copy_id)

    def snapshot(self) -> dict:
        return {
            "id": str(self._id.value),
            "title": self._title,
            "copies": [
                str(copy.value)
                for copy in self._copies
            ],
            "borrowed_copies": [
                str(copy.value)
                for copy in self._borrowed_copies
            ],
            "available_copies": self.available_copies,
        }


class Loan:
    """
    Aggregate Root выдачи книги.

    Связь с Book осуществляется через book_id,
    а не через объект Book.
    """

    def __init__(
        self,
        loan_id: LoanId,
        book_id: BookId,
        reader_id: ReaderId,
        copy_id: CopyId,
        period: LoanPeriod,
        fine: Fine | None = None,
        returned_at: datetime | None = None,
    ):
        if (
            returned_at is not None
            and returned_at < period.started_at
        ):
            raise DomainInvariantViolation(
                "Возврат не может быть раньше выдачи"
            )

        self._id = loan_id
        self._book_id = book_id
        self._reader_id = reader_id
        self._copy_id = copy_id
        self._period = period
        self._fine = fine or Fine(Decimal("0"))
        self._returned_at = returned_at

    @property
    def id(self) -> LoanId:
        return self._id

    @property
    def book_id(self) -> BookId:
        return self._book_id

    @property
    def reader_id(self) -> ReaderId:
        return self._reader_id

    @property
    def copy_id(self) -> CopyId:
        return self._copy_id

    @property
    def due_at(self) -> datetime:
        return self._period.due_at

    @property
    def is_returned(self) -> bool:
        return self._returned_at is not None

    @property
    def fine(self) -> Fine:
        return self._fine

    def return_book(
        self,
        returned_at: datetime,
        fine: Fine,
    ) -> None:
        if self.is_returned:
            raise DomainInvariantViolation(
                "Выдача уже закрыта"
            )

        if returned_at < self._period.started_at:
            raise DomainInvariantViolation(
                "Возврат не может быть раньше выдачи"
            )

        self._returned_at = returned_at
        self._fine = fine

    def snapshot(self) -> dict:
        return {
            "id": str(self._id.value),
            "book_id": str(self._book_id.value),
            "reader_id": str(self._reader_id.value),
            "copy_id": str(self._copy_id.value),
            "started_at": self._period.started_at.isoformat(),
            "due_at": self._period.due_at.isoformat(),
            "returned_at": (
                self._returned_at.isoformat()
                if self._returned_at
                else None
            ),
            "fine": str(self._fine.amount),
        }