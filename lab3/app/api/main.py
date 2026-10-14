from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.library_router import router as library_router
from app.api.parking_router import router as parking_router
from app.api.schemas import TickRequest
from app.application.library_process import LendingProcess
from app.application.parking_process import ParkingProcess
from app.infrastructure.repositories import (
    InMemoryLoanRepository,
    InMemoryParkingSessionRepository,
)
from app.infrastructure.system_clock import SystemClock


def create_app() -> FastAPI:
    app = FastAPI(title="LR3 — Lifecycle", version="0.1.0")

    # --- composition root ---
    app.state.loan_repo = InMemoryLoanRepository()
    app.state.parking_repo = InMemoryParkingSessionRepository()
    app.state.lending_process = LendingProcess()
    app.state.parking_process = ParkingProcess()
    app.state.clock = SystemClock()

    register_exception_handlers(app)

    app.include_router(library_router)
    app.include_router(parking_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/internal/tick")
    def tick(body: TickRequest | None = None):
        now: datetime = body.now if (body and body.now) else app.state.clock.now()

        lending: LendingProcess = app.state.lending_process
        for loan in list(app.state.loan_repo.all()):
            try:
                lending.on_due_date_passed(loan, now)
            except Exception:
                pass
            try:
                lending.escalate_overdue(loan, now)
            except Exception:
                pass

        parking: ParkingProcess = app.state.parking_process
        for s in list(app.state.parking_repo.all()):
            try:
                parking.check_exit_window(s, now)
            except Exception:
                pass
            try:
                parking.check_long_term(s, now)
            except Exception:
                pass

        return {"ticked_at": now.isoformat()}

    return app