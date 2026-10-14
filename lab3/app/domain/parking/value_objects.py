from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.domain.common.exceptions import InvalidValueObject


@dataclass(frozen=True)
class SpotId:
    value: UUID

    def __post_init__(self):
        if not isinstance(self.value, UUID):
            raise InvalidValueObject("SpotId должен содержать UUID")


@dataclass(frozen=True)
class SessionId:
    value: UUID

    def __post_init__(self):
        if not isinstance(self.value, UUID):
            raise InvalidValueObject("SessionId должен содержать UUID")


@dataclass(frozen=True)
class LicensePlate:
    value: str

    def __post_init__(self):
        v = (self.value or "").strip().upper()
        if not v:
            raise InvalidValueObject("Номер автомобиля не может быть пустым")
        if len(v) > 20:
            raise InvalidValueObject("Слишком длинный номер автомобиля")
        object.__setattr__(self, "value", v)


@dataclass(frozen=True)
class Money:
    amount: Decimal

    def __post_init__(self):
        if self.amount < Decimal("0"):
            raise InvalidValueObject("Стоимость не может быть отрицательной")


@dataclass(frozen=True)
class HourlyRate:
    value: Decimal

    def __post_init__(self):
        if self.value < Decimal("0"):
            raise InvalidValueObject("Тариф не может быть отрицательным")


@dataclass(frozen=True)
class ExitWindow:
    """Окно выезда — 15 минут с момента оплаты."""
    opened_at: datetime
    closes_at: datetime

    def __post_init__(self):
        if self.closes_at <= self.opened_at:
            raise InvalidValueObject("Окно выезда должно закрываться позже открытия")