from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from app.domain.common.exceptions import DomainInvariantViolation
from app.domain.parking.states import (
    Active,
    Cancelled,
    Completed,
    ExitWindowExpired,
    LongTerm,
    Paid,
    SESSION_STATE_REGISTRY,
    SessionState,
)
from app.domain.parking.value_objects import (
    ExitWindow,
    LicensePlate,
    Money,
    SessionId,
    SpotId,
)

EXIT_WINDOW_MINUTES = 15


class ParkingSession:
    """Aggregate Root: парковочная сессия."""

    def __init__(
        self,
        session_id: SessionId,
        spot_id: SpotId,
        license_plate: LicensePlate,
        started_at: datetime,
        state: SessionState | None = None,
        exit_window: ExitWindow | None = None,
        total_paid: Money | None = None,
        finished_at: datetime | None = None,
    ) -> None:
        self._id = session_id
        self._spot_id = spot_id
        self._plate = license_plate
        self._started_at = started_at
        self._state: SessionState = state or Active()
        self._exit_window = exit_window
        self._total_paid = total_paid or Money(Decimal("0"))
        self._finished_at = finished_at

    # --- read-only ---
    @property
    def id(self) -> SessionId: return self._id

    @property
    def spot_id(self) -> SpotId: return self._spot_id

    @property
    def license_plate(self) -> LicensePlate: return self._plate

    @property
    def started_at(self) -> datetime: return self._started_at

    @property
    def finished_at(self) -> datetime | None: return self._finished_at

    @property
    def exit_window(self) -> ExitWindow | None: return self._exit_window

    @property
    def total_paid(self) -> Money: return self._total_paid

    @property
    def state(self) -> SessionState: return self._state

    @property
    def state_name(self) -> str: return self._state.name

    def allowed_events(self) -> tuple[str, ...]:
        return self._state.allowed_events()

    # --- события ---
    def _apply(self, event: str, now: datetime, **kwargs) -> None:
        method = getattr(self._state, f"on_{event}")
        self._state = method(self, now, **kwargs)

    def pay(self, now: datetime, amount: Decimal) -> None:
        self._apply("pay", now, amount=amount)

    def additional_pay(self, now: datetime, amount: Decimal) -> None:
        self._apply("additional_pay", now, amount=amount)

    def exit_window_expired(self, now: datetime) -> None:
        self._apply("exit_window_expired", now)

    def seven_days_passed(self, now: datetime) -> None:
        self._apply("seven_days_passed", now)

    def exit(self, now: datetime) -> None:
        self._apply("exit", now)

    def cancel(self, now: datetime) -> None:
        self._apply("cancel", now)

    # --- внутренние ---
    def _record_payment(self, now: datetime, amount: Decimal) -> None:
        if amount < Decimal("0"):
            raise DomainInvariantViolation("Сумма платежа не может быть отрицательной")
        self._total_paid = Money(self._total_paid.amount + amount)
        self._exit_window = ExitWindow(
            opened_at=now,
            closes_at=now + timedelta(minutes=EXIT_WINDOW_MINUTES),
        )

    def _flag_long_term(self, now: datetime) -> None:
        # Побочный эффект: сервис публикует LongTermParkingDetected
        pass

    def _complete(self, now: datetime) -> None:
        if self._exit_window is None:
            raise DomainInvariantViolation("Нельзя завершить сессию без оплаты")
        if now > self._exit_window.closes_at:
            raise DomainInvariantViolation("Окно выезда истекло, требуется доплата")
        self._finished_at = now

    @classmethod
    def restore(
        cls,
        session_id: SessionId,
        spot_id: SpotId,
        license_plate: LicensePlate,
        started_at: datetime,
        state_name: str,
        exit_window: ExitWindow | None,
        total_paid: Money,
        finished_at: datetime | None,
    ) -> "ParkingSession":
        return cls(
            session_id=session_id,
            spot_id=spot_id,
            license_plate=license_plate,
            started_at=started_at,
            state=SESSION_STATE_REGISTRY[state_name](),
            exit_window=exit_window,
            total_paid=total_paid,
            finished_at=finished_at,
        )