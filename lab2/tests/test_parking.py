from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.parking.entities.models import ParkingSpot
from app.domain.parking.exceptions.exceptions import (
    DomainInvariantViolation,
)
from app.domain.parking.services.service import ParkingService
from app.domain.parking.value_objects.values import (
    HourlyRate,
    LicensePlate,
    SessionId,
    SpotId,
)


def test_cannot_occupy_occupied_spot():

    spot = ParkingSpot(
        spot_id=SpotId(uuid4())
    )

    spot.occupy(SessionId(uuid4()))

    with pytest.raises(DomainInvariantViolation):
        spot.occupy(SessionId(uuid4()))


def test_parking_cost_rounds_hours_up():

    spot = ParkingSpot(
        spot_id=SpotId(uuid4())
    )

    started_at = datetime.now()

    session = ParkingService.start_session(
        spot=spot,
        session_id=SessionId(uuid4()),
        license_plate=LicensePlate("A123BC"),
        started_at=started_at,
    )

    cost = ParkingService.finish_session(
        spot=spot,
        session=session,
        finished_at=started_at + timedelta(
            hours=1,
            minutes=10,
        ),
        rate=HourlyRate(Decimal("100")),
    )

    assert cost.amount == Decimal("200")