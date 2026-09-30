from datetime import datetime
from decimal import Decimal
from math import ceil

from ..entities.models import ParkingSession, ParkingSpot
from ..value_objects.values import (
    HourlyRate,
    LicensePlate,
    Money,
    SessionId,
)


class ParkingService:

    @staticmethod
    def start_session(
        spot: ParkingSpot,
        session_id: SessionId,
        license_plate: LicensePlate,
        started_at: datetime,
    ) -> ParkingSession:

        spot.occupy(session_id)

        return ParkingSession(
            session_id=session_id,
            spot_id=spot.id,
            license_plate=license_plate,
            started_at=started_at,
        )

    @staticmethod
    def finish_session(
        spot: ParkingSpot,
        session: ParkingSession,
        finished_at: datetime,
        rate: HourlyRate,
    ) -> Money:

        duration = (
            finished_at - session.started_at
        ).total_seconds()

        hours = max(1, ceil(duration / 3600))

        cost = Money(
            Decimal(hours) * rate.value
        )

        session.close(
            finished_at=finished_at,
            cost=cost,
        )

        spot.release()

        return cost