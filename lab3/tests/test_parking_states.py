from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.common.exceptions import TransitionNotAllowed
from app.domain.parking.session import ParkingSession
from app.domain.parking.value_objects import (
    LicensePlate,
    SessionId,
    SpotId,
)


def make_session():
    return ParkingSession(
        session_id=SessionId(uuid4()),
        spot_id=SpotId(uuid4()),
        license_plate=LicensePlate("A123BC"),
        started_at=datetime(2026, 1, 1, 10, 0),
    )


def test_pay_then_exit():
    s = make_session()
    now = datetime(2026, 1, 1, 10, 0)
    s.pay(now, Decimal("100"))
    assert s.state_name == "Paid"
    s.exit(now + timedelta(minutes=5))
    assert s.state_name == "Completed"


def test_exit_window_expired_and_additional_pay_cycle():
    s = make_session()
    now = datetime(2026, 1, 1, 10, 0)
    s.pay(now, Decimal("100"))
    s.exit_window_expired(now + timedelta(minutes=20))
    assert s.state_name == "ExitWindowExpired"
    s.additional_pay(now + timedelta(minutes=21), Decimal("50"))
    assert s.state_name == "Paid"


def test_cannot_exit_without_pay():
    s = make_session()
    with pytest.raises(TransitionNotAllowed):
        s.exit(datetime(2026, 1, 1, 10, 5))


def test_long_term_notification():
    s = make_session()
    s.seven_days_passed(datetime(2026, 1, 8, 10, 0))
    assert s.state_name == "LongTerm"


def test_cannot_pay_from_completed():
    s = make_session()
    now = datetime(2026, 1, 1, 10, 0)
    s.pay(now, Decimal("100"))
    s.exit(now + timedelta(minutes=5))
    with pytest.raises(TransitionNotAllowed):
        s.pay(now + timedelta(minutes=6), Decimal("50"))