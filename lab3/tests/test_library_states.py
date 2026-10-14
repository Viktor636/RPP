from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.common.exceptions import TransitionNotAllowed
from app.domain.library.loan import Loan
from app.domain.library.value_objects import (
    BookId,
    CopyId,
    LoanId,
    LoanPeriod,
    ReaderId,
)


def make_loan():
    now = datetime(2026, 1, 1, 10, 0)
    return Loan(
        loan_id=LoanId(uuid4()),
        book_id=BookId(uuid4()),
        reader_id=ReaderId(uuid4()),
        copy_id=CopyId(uuid4()),
        period=LoanPeriod(started_at=now, due_at=now),
    )


def test_issue_then_extend_then_return():
    loan = make_loan()
    now = datetime(2026, 1, 1, 10, 0)
    loan.issue(now)
    assert loan.state_name == "Issued"
    loan.extend(now + timedelta(days=1))
    assert loan.state_name == "Extended"
    loan.return_ok(now + timedelta(days=5))
    assert loan.state_name == "ReturnedOk"
    assert loan.fine.amount == 0


def test_cannot_return_twice():
    loan = make_loan()
    now = datetime(2026, 1, 1)
    loan.issue(now)
    loan.return_ok(now + timedelta(days=1))
    with pytest.raises(TransitionNotAllowed):
        loan.return_ok(now + timedelta(days=2))


def test_overdue_then_fine():
    loan = make_loan()
    now = datetime(2026, 1, 1)
    loan.issue(now)
    loan.on_due_date_passed(now + timedelta(days=15))
    assert loan.state_name == "Overdue"
    loan.return_ok(now + timedelta(days=17))
    assert loan.state_name == "ReturnedFine"
    assert loan.fine.amount > 0


def test_cannot_issue_from_returned():
    loan = make_loan()
    now = datetime(2026, 1, 1)
    loan.issue(now)
    loan.return_ok(now + timedelta(days=3))
    with pytest.raises(TransitionNotAllowed):
        loan.issue(now + timedelta(days=4))