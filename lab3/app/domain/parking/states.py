from __future__ import annotations

from abc import ABC
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.domain.common.exceptions import TransitionNotAllowed

if TYPE_CHECKING:
    from app.domain.parking.session import ParkingSession


class SessionState(ABC):
    name: str = "Unknown"

    def on_pay(self, s: "ParkingSession", now: datetime, amount: Decimal) -> "SessionState":
        raise TransitionNotAllowed(self.name, "pay")

    def on_additional_pay(self, s: "ParkingSession", now: datetime, amount: Decimal) -> "SessionState":
        raise TransitionNotAllowed(self.name, "additional_pay")

    def on_exit_window_expired(self, s: "ParkingSession", now: datetime) -> "SessionState":
        raise TransitionNotAllowed(self.name, "exit_window_expired")

    def on_seven_days_passed(self, s: "ParkingSession", now: datetime) -> "SessionState":
        raise TransitionNotAllowed(self.name, "seven_days_passed")

    def on_exit(self, s: "ParkingSession", now: datetime) -> "SessionState":
        raise TransitionNotAllowed(self.name, "exit")

    def on_cancel(self, s: "ParkingSession", now: datetime) -> "SessionState":
        raise TransitionNotAllowed(self.name, "cancel")

    def allowed_events(self) -> tuple[str, ...]:
        return ()


class Active(SessionState):
    name = "Active"

    def on_pay(self, s, now, amount):
        s._record_payment(now, amount)
        return Paid()

    def on_seven_days_passed(self, s, now):
        s._flag_long_term(now)
        return LongTerm()

    def on_cancel(self, s, now):
        return Cancelled()

    def allowed_events(self):
        return ("pay", "seven_days_passed", "cancel")


class Paid(SessionState):
    name = "Paid"

    def on_exit(self, s, now):
        s._complete(now)
        return Completed()

    def on_exit_window_expired(self, s, now):
        return ExitWindowExpired()

    def on_seven_days_passed(self, s, now):
        s._flag_long_term(now)
        return LongTerm()

    def on_cancel(self, s, now):
        return Cancelled()

    def allowed_events(self):
        return ("exit", "exit_window_expired", "seven_days_passed", "cancel")


class ExitWindowExpired(SessionState):
    name = "ExitWindowExpired"

    def on_additional_pay(self, s, now, amount):
        s._record_payment(now, amount)
        return Paid()

    def on_seven_days_passed(self, s, now):
        s._flag_long_term(now)
        return LongTerm()

    def on_cancel(self, s, now):
        return Cancelled()

    def allowed_events(self):
        return ("additional_pay", "seven_days_passed", "cancel")


class LongTerm(SessionState):
    name = "LongTerm"

    def on_pay(self, s, now, amount):
        s._record_payment(now, amount)
        return Paid()

    def on_cancel(self, s, now):
        return Cancelled()

    def allowed_events(self):
        return ("pay", "cancel")


class Completed(SessionState):
    name = "Completed"


class Cancelled(SessionState):
    name = "Cancelled"


SESSION_STATE_REGISTRY: dict[str, type[SessionState]] = {
    cls.name: cls for cls in (
        Active, Paid, ExitWindowExpired, LongTerm, Completed, Cancelled,
    )
}