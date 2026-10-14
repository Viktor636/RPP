from __future__ import annotations

from fastapi import Request

from app.application.library_process import LendingProcess
from app.application.parking_process import ParkingProcess
from app.infrastructure.repositories import (
    InMemoryLoanRepository,
    InMemoryParkingSessionRepository,
)
from app.infrastructure.system_clock import SystemClock


def get_loan_repo(request: Request) -> InMemoryLoanRepository:
    return request.app.state.loan_repo


def get_lending_process(request: Request) -> LendingProcess:
    return request.app.state.lending_process


def get_parking_repo(request: Request) -> InMemoryParkingSessionRepository:
    return request.app.state.parking_repo


def get_parking_process(request: Request) -> ParkingProcess:
    return request.app.state.parking_process


def get_clock(request: Request) -> SystemClock:
    return request.app.state.clock