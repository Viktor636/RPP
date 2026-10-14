from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from math import ceil

from app.domain.common.exceptions import DomainInvariantViolation
from app.domain.parking.events import (
    DomainEvent,
    LongTermParkingDetected,
    SessionCompleted,
    SessionPaid,
    SessionStarted,
)
from app.domain.parking.session import ParkingSession
from app.domain.parking.value_objects import HourlyRate


class ParkingProcess:
    """Процесс платной парковки."""

    def __init__(self, events: list[DomainEvent] | None = None) -> None:
        self._events: list[DomainEvent] = events or []

    @property
    def events(self) -> list[DomainEvent]:
        return self._events

    # --- предикаты шлюзов ---
    @staticmethod
    def is_blocked(license_plate: str, blocklist: set[str]) -> bool:
        return license_plate in blocklist

    @staticmethod
    def is_paid(session: ParkingSession) -> bool:
        return session.state_name == "Paid"

    @staticmethod
    def in_exit_window(session: ParkingSession, now: datetime) -> bool:
        w = session.exit_window
        return w is not None and now <= w.closes_at

    # --- задачи BPMN ---
    def start_session(self, session: ParkingSession, now: datetime) -> None:
        self._events.append(
            SessionStarted(
                occurred_at=now,
                session_id=session.id.value,
                spot_id=session.spot_id.value,
            )
        )

    def pay(self, session: ParkingSession, amount: Decimal, now: datetime) -> None:
        session.pay(now, amount)
        self._events.append(
            SessionPaid(
                occurred_at=now,
                session_id=session.id.value,
                amount=str(amount),
            )
        )

    def additional_pay(self, session: ParkingSession, amount: Decimal, now: datetime) -> None:
        session.additional_pay(now, amount)
        self._events.append(
            SessionPaid(
                occurred_at=now,
                session_id=session.id.value,
                amount=str(amount),
            )
        )

    def check_exit_window(self, session: ParkingSession, now: datetime) -> None:
        if session.state_name == "Paid" and not self.in_exit_window(session, now):
            session.exit_window_expired(now)

    def check_long_term(self, session: ParkingSession, now: datetime) -> None:
        if session.state_name in ("Active", "Paid", "ExitWindowExpired"):
            if (now - session.started_at).days >= 7:
                session.seven_days_passed(now)
                self._events.append(
                    LongTermParkingDetected(
                        occurred_at=now,
                        session_id=session.id.value,
                    )
                )

    def complete_exit(self, session: ParkingSession, now: datetime) -> None:
        if session.state_name == "Paid" and not self.in_exit_window(session, now):
            raise DomainInvariantViolation("Окно выезда истекло, требуется доплата")
        session.exit(now)
        self._events.append(
            SessionCompleted(
                occurred_at=now,
                session_id=session.id.value,
                spot_id=session.spot_id.value,
                total=str(session.total_paid.amount),
            )
        )

    @staticmethod
    def calculate_cost(
        session: ParkingSession, rate: HourlyRate, now: datetime
    ) -> Decimal:
        seconds = (now - session.started_at).total_seconds()
        hours = max(1, ceil(seconds / 3600))
        return Decimal(hours) * rate.value