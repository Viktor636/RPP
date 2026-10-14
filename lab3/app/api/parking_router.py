from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_clock, get_parking_process, get_parking_repo
from app.api.schemas import PayRequest, SessionResponse, StartSessionRequest
from app.application.parking_process import ParkingProcess
from app.domain.common.exceptions import EntityNotFound
from app.domain.parking.session import ParkingSession
from app.domain.parking.value_objects import LicensePlate, SessionId, SpotId
from app.infrastructure.repositories import InMemoryParkingSessionRepository
from app.infrastructure.system_clock import SystemClock

router = APIRouter(prefix="/parking", tags=["Parking"])


def _serialize(s: ParkingSession) -> SessionResponse:
    return SessionResponse(
        id=s.id.value,
        spot_id=s.spot_id.value,
        license_plate=s.license_plate.value,
        state=s.state_name,
        allowed_events=list(s.allowed_events()),
        started_at=s.started_at,
        finished_at=s.finished_at,
        total_paid=str(s.total_paid.amount),
        exit_window_closes_at=s.exit_window.closes_at if s.exit_window else None,
    )


@router.post("/sessions", response_model=SessionResponse, status_code=201)
def start_session(
    body: StartSessionRequest,
    repo: InMemoryParkingSessionRepository = Depends(get_parking_repo),
    process: ParkingProcess = Depends(get_parking_process),
    clock: SystemClock = Depends(get_clock),
):
    plate = LicensePlate(body.license_plate)
    if ParkingProcess.is_blocked(plate.value, set(body.blocklist)):
        raise HTTPException(
            status_code=409,
            detail={"error": "blocked", "message": "Номер в списке заблокированных"},
        )
    now = clock.now()
    session = ParkingSession(
        session_id=SessionId(uuid4()),
        spot_id=SpotId(body.spot_id),
        license_plate=plate,
        started_at=now,
    )
    repo.save(session)
    process.start_session(session, now)
    return _serialize(session)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
    repo: InMemoryParkingSessionRepository = Depends(get_parking_repo),
):
    try:
        s = repo.get(SessionId(session_id))
    except KeyError:
        raise EntityNotFound(f"Сессия {session_id} не найдена")
    return _serialize(s)


@router.post("/sessions/{session_id}/pay", response_model=SessionResponse)
def pay(
    session_id: UUID,
    body: PayRequest,
    repo: InMemoryParkingSessionRepository = Depends(get_parking_repo),
    process: ParkingProcess = Depends(get_parking_process),
    clock: SystemClock = Depends(get_clock),
):
    s = repo.get(SessionId(session_id))
    process.pay(s, Decimal(body.amount), clock.now())
    return _serialize(s)


@router.post("/sessions/{session_id}/additional_pay", response_model=SessionResponse)
def additional_pay(
    session_id: UUID,
    body: PayRequest,
    repo: InMemoryParkingSessionRepository = Depends(get_parking_repo),
    process: ParkingProcess = Depends(get_parking_process),
    clock: SystemClock = Depends(get_clock),
):
    s = repo.get(SessionId(session_id))
    process.additional_pay(s, Decimal(body.amount), clock.now())
    return _serialize(s)


@router.post("/sessions/{session_id}/exit", response_model=SessionResponse)
def exit_session(
    session_id: UUID,
    repo: InMemoryParkingSessionRepository = Depends(get_parking_repo),
    process: ParkingProcess = Depends(get_parking_process),
    clock: SystemClock = Depends(get_clock),
):
    s = repo.get(SessionId(session_id))
    now = clock.now()
    process.check_exit_window(s, now)
    process.complete_exit(s, now)
    return _serialize(s)


@router.post("/sessions/{session_id}/cancel", response_model=SessionResponse)
def cancel_session(
    session_id: UUID,
    repo: InMemoryParkingSessionRepository = Depends(get_parking_repo),
    clock: SystemClock = Depends(get_clock),
):
    s = repo.get(SessionId(session_id))
    s.cancel(clock.now())
    return _serialize(s)