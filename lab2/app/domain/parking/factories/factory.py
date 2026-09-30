from uuid import UUID

from ..entities.models import ParkingSpot
from ..value_objects.values import SessionId, SpotId


class ParkingSpotFactory:

    @staticmethod
    def from_state(data: dict) -> ParkingSpot:

        session_id = (
            SessionId(UUID(data["session_id"]))
            if data["session_id"]
            else None
        )

        return ParkingSpot(
            spot_id=SpotId(UUID(data["id"])),
            occupied=data["occupied"],
            session_id=session_id,
        )