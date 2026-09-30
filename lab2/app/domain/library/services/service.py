from datetime import datetime
from decimal import Decimal

from ..entities.models import Book, Loan
from ..exceptions.exceptions import DomainInvariantViolation
from ..value_objects.values import (
    BookId,
    CopyId,
    Fine,
    LoanId,
    LoanPeriod,
    ReaderId,
)


class LibraryService:

    @staticmethod
    def issue_book(
        book: Book,
        loan_id: LoanId,
        reader_id: ReaderId,
        copy_id: CopyId,
        started_at: datetime,
        due_at: datetime,
    ) -> Loan:

        if not book.can_borrow(copy_id):
            raise DomainInvariantViolation(
                "Экземпляр книги недоступен"
            )

        period = LoanPeriod(
            started_at=started_at,
            due_at=due_at,
        )

        book.borrow_copy(copy_id)

        return Loan(
            loan_id=loan_id,
            book_id=book.id,
            reader_id=reader_id,
            copy_id=copy_id,
            period=period,
        )

    @staticmethod
    def return_book(
        book: Book,
        loan: Loan,
        returned_at: datetime,
        fine_per_day: Decimal,
    ) -> Fine:

        if loan.is_returned:
            raise DomainInvariantViolation(
                "Эта выдача уже закрыта"
            )

        if fine_per_day < 0:
            raise DomainInvariantViolation(
                "Штраф за день не может быть отрицательным"
            )

        if returned_at < loan.due_at:
            overdue_days = 0
        else:
            overdue_days = (
                returned_at.date() - loan.due_at.date()
            ).days

        fine = Fine(
            Decimal(overdue_days) * fine_per_day
        )

        loan.return_book(
            returned_at=returned_at,
            fine=fine,
        )

        book.return_copy(loan.copy_id)

        return fine