from typing import Protocol

from ..entities.models import ParkingSession, ParkingSpot
from ..value_objects.values import SessionId, SpotId


class ParkingSpotRepository(Protocol):

    def save(self, spot: ParkingSpot) -> None:
        ...

    def get(self, spot_id: SpotId) -> ParkingSpot:
        ...


class ParkingSessionRepository(Protocol):

    def save(self, session: ParkingSession) -> None:
        ...

    def get(self, session_id: SessionId) -> ParkingSession:
        ...