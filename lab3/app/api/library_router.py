from __future__ import annotations

from uuid import UUID, uuid4

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends

from app.api.deps import get_clock, get_lending_process, get_loan_repo
from app.api.schemas import (
    CreateLoanRequest,
    ExtendLoanRequest,
    IssueLoanRequest,
    LoanResponse,
    ReturnLoanRequest,
)
from app.application.library_process import LendingProcess
from app.domain.common.exceptions import EntityNotFound
from app.domain.library.loan import Loan
from app.domain.library.value_objects import (
    BookId,
    CopyId,
    LoanId,
    LoanPeriod,
    ReaderId,
)
from app.infrastructure.repositories import InMemoryLoanRepository
from app.infrastructure.system_clock import SystemClock

router = APIRouter(prefix="/library", tags=["Library"])


def _serialize(loan: Loan) -> LoanResponse:
    return LoanResponse(
        id=loan.id.value,
        book_id=loan.book_id.value,
        reader_id=loan.reader_id.value,
        copy_id=loan.copy_id.value,
        state=loan.state_name,
        allowed_events=list(loan.allowed_events()),
        fine=str(loan.fine.amount),
        started_at=loan.period.started_at,
        due_at=loan.due_at,
        returned_at=loan.returned_at,
    )


@router.post("/loans", response_model=LoanResponse, status_code=201)
def create_loan(
    body: CreateLoanRequest,
    repo: InMemoryLoanRepository = Depends(get_loan_repo),
    clock: SystemClock = Depends(get_clock),
):
    now = clock.now()
    loan = Loan(
        loan_id=LoanId(uuid4()),
        book_id=BookId(body.book_id),
        reader_id=ReaderId(body.reader_id),
        copy_id=CopyId(body.copy_id),
        period=LoanPeriod(started_at=now, due_at=now + timedelta(days=14)),
    )
    repo.save(loan)
    return _serialize(loan)


@router.get("/loans/{loan_id}", response_model=LoanResponse)
def get_loan(
    loan_id: UUID,
    repo: InMemoryLoanRepository = Depends(get_loan_repo),
):
    try:
        loan = repo.get(LoanId(loan_id))
    except KeyError:
        raise EntityNotFound(f"Выдача {loan_id} не найдена")
    return _serialize(loan)


@router.post("/loans/{loan_id}/issue", response_model=LoanResponse)
def issue_loan(
    loan_id: UUID,
    body: IssueLoanRequest,
    repo: InMemoryLoanRepository = Depends(get_loan_repo),
    process: LendingProcess = Depends(get_lending_process),
    clock: SystemClock = Depends(get_clock),
):
    loan = repo.get(LoanId(loan_id))
    process.check_reader_debt(
        loan,
        has_overdue=body.has_overdue,
        has_unpaid_fine=body.has_unpaid_fine,
        now=clock.now(),
    )
    return _serialize(loan)


@router.post("/loans/{loan_id}/extend", response_model=LoanResponse)
def extend_loan(
    loan_id: UUID,
    body: ExtendLoanRequest,
    repo: InMemoryLoanRepository = Depends(get_loan_repo),
    process: LendingProcess = Depends(get_lending_process),
    clock: SystemClock = Depends(get_clock),
):
    loan = repo.get(LoanId(loan_id))
    process.extend_loan(loan, has_queue=body.has_queue, now=clock.now())
    return _serialize(loan)


@router.post("/loans/{loan_id}/return", response_model=LoanResponse)
def return_loan(
    loan_id: UUID,
    body: ReturnLoanRequest,
    repo: InMemoryLoanRepository = Depends(get_loan_repo),
    process: LendingProcess = Depends(get_lending_process),
    clock: SystemClock = Depends(get_clock),
):
    loan = repo.get(LoanId(loan_id))
    process.accept_return(loan, report_damaged=body.damaged, now=clock.now())
    return _serialize(loan)


@router.post("/loans/{loan_id}/cancel", response_model=LoanResponse)
def cancel_loan(
    loan_id: UUID,
    repo: InMemoryLoanRepository = Depends(get_loan_repo),
    clock: SystemClock = Depends(get_clock),
):
    loan = repo.get(LoanId(loan_id))
    loan.cancel_booking(clock.now())
    return _serialize(loan)