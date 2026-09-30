from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.domain.parking.entities.models import ParkingSpot
from app.domain.parking.services.service import ParkingService
from app.domain.parking.value_objects.values import (
    HourlyRate,
    LicensePlate,
    SessionId,
    SpotId,
)
from app.infrastructure.repositories.in_memory import (
    InMemoryParkingSessionRepository,
    InMemoryParkingSpotRepository,
)


router = APIRouter(
    prefix="/parking",
    tags=["Parking"],
)

spot_repository = InMemoryParkingSpotRepository()
session_repository = InMemoryParkingSessionRepository()


class EnterRequest(BaseModel):
    license_plate: str


class ExitRequest(BaseModel):
    hourly_rate: Decimal


@router.post("/spots")
def create_spot():

    spot = ParkingSpot(
        spot_id=SpotId(uuid4())
    )

    spot_repository.save(spot)

    return spot.snapshot()


@router.post("/spots/{spot_id}/enter")
def enter_parking(
    spot_id: UUID,
    data: EnterRequest,
):

    try:
        spot = spot_repository.get(
            SpotId(spot_id)
        )

        session = ParkingService.start_session(
            spot=spot,
            session_id=SessionId(uuid4()),
            license_plate=LicensePlate(
                data.license_plate
            ),
            started_at=datetime.now(),
        )

        spot_repository.save(spot)
        session_repository.save(session)

        return session.snapshot()

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Парковочное место не найдено",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/sessions/{session_id}/exit")
def exit_parking(
    session_id: UUID,
    data: ExitRequest,
):

    try:
        session = session_repository.get(
            SessionId(session_id)
        )

        spot = spot_repository.get(
            session.spot_id
        )

        cost = ParkingService.finish_session(
            spot=spot,
            session=session,
            finished_at=datetime.now(),
            rate=HourlyRate(data.hourly_rate),
        )

        spot_repository.save(spot)
        session_repository.save(session)

        return {
            "session": session.snapshot(),
            "cost": str(cost.amount),
        }

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Сессия или парковочное место не найдены",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )