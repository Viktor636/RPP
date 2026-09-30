from datetime import datetime

from ..exceptions.exceptions import DomainInvariantViolation
from ..value_objects.values import (
    HourlyRate,
    LicensePlate,
    Money,
    SessionId,
    SpotId,
)


class ParkingSpot:
    """
    Aggregate Root парковочного места.
    """

    def __init__(
        self,
        spot_id: SpotId,
        occupied: bool = False,
        session_id: SessionId | None = None,
    ):
        if occupied and session_id is None:
            raise DomainInvariantViolation(
                "Занятое место должно иметь сессию"
            )

        if not occupied and session_id is not None:
            raise DomainInvariantViolation(
                "Свободное место не может иметь сессию"
            )

        self._id = spot_id
        self._occupied = occupied
        self._session_id = session_id

    @property
    def id(self) -> SpotId:
        return self._id

    @property
    def is_occupied(self) -> bool:
        return self._occupied

    def occupy(self, session_id: SessionId) -> None:
        if self._occupied:
            raise DomainInvariantViolation(
                "Парковочное место уже занято"
            )

        self._occupied = True
        self._session_id = session_id

    def release(self) -> None:
        if not self._occupied:
            raise DomainInvariantViolation(
                "Парковочное место уже свободно"
            )

        self._occupied = False
        self._session_id = None

    def snapshot(self) -> dict:
        return {
            "id": str(self._id.value),
            "occupied": self._occupied,
            "session_id": (
                str(self._session_id.value)
                if self._session_id
                else None
            ),
        }


class ParkingSession:
    """
    Aggregate Root парковочной сессии.
    """

    def __init__(
        self,
        session_id: SessionId,
        spot_id: SpotId,
        license_plate: LicensePlate,
        started_at: datetime,
        finished_at: datetime | None = None,
        cost: Money | None = None,
    ):
        if (
            finished_at is not None
            and finished_at < started_at
        ):
            raise DomainInvariantViolation(
                "Время выезда не может быть раньше въезда"
            )

        self._id = session_id
        self._spot_id = spot_id
        self._license_plate = license_plate
        self._started_at = started_at
        self._finished_at = finished_at
        self._cost = cost

    @property
    def id(self) -> SessionId:
        return self._id

    @property
    def spot_id(self) -> SpotId:
        return self._spot_id

    @property
    def started_at(self) -> datetime:
        return self._started_at

    @property
    def is_closed(self) -> bool:
        return self._finished_at is not None

    def close(
        self,
        finished_at: datetime,
        cost: Money,
    ) -> None:

        if self.is_closed:
            raise DomainInvariantViolation(
                "Сессия уже закрыта"
            )

        if finished_at < self._started_at:
            raise DomainInvariantViolation(
                "Время выезда не может быть раньше въезда"
            )

        self._finished_at = finished_at
        self._cost = cost

    def snapshot(self) -> dict:
        return {
            "id": str(self._id.value),
            "spot_id": str(self._spot_id.value),
            "license_plate": self._license_plate.value,
            "started_at": self._started_at.isoformat(),
            "finished_at": (
                self._finished_at.isoformat()
                if self._finished_at
                else None
            ),
            "cost": (
                str(self._cost.amount)
                if self._cost
                else None
            ),
        }