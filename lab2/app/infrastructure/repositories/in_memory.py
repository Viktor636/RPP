from app.domain.library.entities.models import Book, Loan
from app.domain.library.value_objects.values import BookId, LoanId

from app.domain.parking.entities.models import (
    ParkingSession,
    ParkingSpot,
)
from app.domain.parking.value_objects.values import (
    SessionId,
    SpotId,
)


class InMemoryBookRepository:

    def __init__(self):
        self._data: dict[BookId, Book] = {}

    def save(self, book: Book) -> None:
        self._data[book.id] = book

    def get(self, book_id: BookId) -> Book:
        return self._data[book_id]


class InMemoryLoanRepository:

    def __init__(self):
        self._data: dict[LoanId, Loan] = {}

    def save(self, loan: Loan) -> None:
        self._data[loan.id] = loan

    def get(self, loan_id: LoanId) -> Loan:
        return self._data[loan_id]


class InMemoryParkingSpotRepository:

    def __init__(self):
        self._data: dict[SpotId, ParkingSpot] = {}

    def save(self, spot: ParkingSpot) -> None:
        self._data[spot.id] = spot

    def get(self, spot_id: SpotId) -> ParkingSpot:
        return self._data[spot_id]


class InMemoryParkingSessionRepository:

    def __init__(self):
        self._data: dict[SessionId, ParkingSession] = {}

    def save(self, session: ParkingSession) -> None:
        self._data[session.id] = session

    def get(self, session_id: SessionId) -> ParkingSession:
        return self._data[session_id]