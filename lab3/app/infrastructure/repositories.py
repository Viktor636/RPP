from __future__ import annotations

from app.domain.library.loan import Loan
from app.domain.library.value_objects import LoanId
from app.domain.parking.session import ParkingSession
from app.domain.parking.value_objects import SessionId


class InMemoryLoanRepository:
    def __init__(self) -> None:
        self._data: dict[LoanId, Loan] = {}

    def save(self, loan: Loan) -> None:
        self._data[loan.id] = loan

    def get(self, loan_id: LoanId) -> Loan:
        return self._data[loan_id]

    def all(self) -> list[Loan]:
        return list(self._data.values())


class InMemoryParkingSessionRepository:
    def __init__(self) -> None:
        self._data: dict[SessionId, ParkingSession] = {}

    def save(self, session: ParkingSession) -> None:
        self._data[session.id] = session

    def get(self, session_id: SessionId) -> ParkingSession:
        return self._data[session_id]

    def all(self) -> list[ParkingSession]:
        return list(self._data.values())