from typing import Protocol

from ..entities.models import Book, Loan
from ..value_objects.values import BookId, LoanId


class BookRepository(Protocol):

    def save(self, book: Book) -> None:
        ...

    def get(self, book_id: BookId) -> Book:
        ...


class LoanRepository(Protocol):

    def save(self, loan: Loan) -> None:
        ...

    def get(self, loan_id: LoanId) -> Loan:
        ...