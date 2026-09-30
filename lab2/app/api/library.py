from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.domain.library.entities.models import Book
from app.domain.library.services.service import LibraryService
from app.domain.library.value_objects.values import (
    BookId,
    CopyId,
    LoanId,
    ReaderId,
)
from app.infrastructure.repositories.in_memory import (
    InMemoryBookRepository,
    InMemoryLoanRepository,
)


router = APIRouter(
    prefix="/library",
    tags=["Library"],
)

book_repository = InMemoryBookRepository()
loan_repository = InMemoryLoanRepository()


class CreateBookRequest(BaseModel):
    title: str
    copies: int


class IssueBookRequest(BaseModel):
    reader_id: UUID
    copy_id: UUID


@router.post("/books")
def create_book(data: CreateBookRequest):

    if data.copies <= 0:
        raise HTTPException(
            status_code=400,
            detail="Количество экземпляров должно быть больше 0",
        )

    copies = {
        CopyId(uuid4())
        for _ in range(data.copies)
    }

    book = Book(
        book_id=BookId(uuid4()),
        title=data.title,
        copies=copies,
    )

    book_repository.save(book)

    return book.snapshot()


@router.post("/books/{book_id}/issue")
def issue_book(
    book_id: UUID,
    data: IssueBookRequest,
):

    try:
        book = book_repository.get(
            BookId(book_id)
        )

        now = datetime.now()

        loan = LibraryService.issue_book(
            book=book,
            loan_id=LoanId(uuid4()),
            reader_id=ReaderId(data.reader_id),
            copy_id=CopyId(data.copy_id),
            started_at=now,
            due_at=now + timedelta(days=14),
        )

        book_repository.save(book)
        loan_repository.save(loan)

        return loan.snapshot()

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Книга не найдена",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/loans/{loan_id}/return")
def return_book(loan_id: UUID):

    try:
        loan = loan_repository.get(
            LoanId(loan_id)
        )

        book = book_repository.get(
            loan.book_id
        )

        fine = LibraryService.return_book(
            book=book,
            loan=loan,
            returned_at=datetime.now(),
            fine_per_day=Decimal("50"),
        )

        book_repository.save(book)
        loan_repository.save(loan)

        return {
            "loan": loan.snapshot(),
            "fine": str(fine.amount),
        }

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Выдача или книга не найдена",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )