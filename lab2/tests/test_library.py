from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.library.entities.models import Book
from app.domain.library.exceptions.exceptions import (
    DomainInvariantViolation,
)
from app.domain.library.services.service import LibraryService
from app.domain.library.value_objects.values import (
    BookId,
    CopyId,
    LoanId,
    ReaderId,
)


def test_cannot_borrow_same_copy_twice():

    copy_id = CopyId(uuid4())

    book = Book(
        book_id=BookId(uuid4()),
        title="Python",
        copies={copy_id},
    )

    book.borrow_copy(copy_id)

    with pytest.raises(DomainInvariantViolation):
        book.borrow_copy(copy_id)


def test_return_book_creates_fine():

    copy_id = CopyId(uuid4())

    book = Book(
        book_id=BookId(uuid4()),
        title="DDD",
        copies={copy_id},
    )

    started_at = datetime.now()
    due_at = started_at + timedelta(days=7)

    loan = LibraryService.issue_book(
        book=book,
        loan_id=LoanId(uuid4()),
        reader_id=ReaderId(uuid4()),
        copy_id=copy_id,
        started_at=started_at,
        due_at=due_at,
    )

    returned_at = due_at + timedelta(days=2)

    fine = LibraryService.return_book(
        book=book,
        loan=loan,
        returned_at=returned_at,
        fine_per_day=Decimal("50"),
    )

    assert fine.amount == Decimal("100")