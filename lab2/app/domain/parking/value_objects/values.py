from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from ..exceptions.exceptions import InvalidValueObject


@dataclass(frozen=True)
class SpotId:
    value: UUID

    def __post_init__(self):
        if not isinstance(self.value, UUID):
            raise InvalidValueObject(
                "SpotId должен содержать UUID"
            )


@dataclass(frozen=True)
class SessionId:
    value: UUID

    def __post_init__(self):
        if not isinstance(self.value, UUID):
            raise InvalidValueObject(
                "SessionId должен содержать UUID"
            )


@dataclass(frozen=True)
class LicensePlate:
    value: str

    def __post_init__(self):
        value = self.value.strip().upper()

        if not value:
            raise InvalidValueObject(
                "Номер автомобиля не может быть пустым"
            )

        if len(value) > 20:
            raise InvalidValueObject(
                "Слишком длинный номер автомобиля"
            )

        object.__setattr__(self, "value", value)


@dataclass(frozen=True)
class Money:
    amount: Decimal

    def __post_init__(self):
        if self.amount < 0:
            raise InvalidValueObject(
                "Стоимость не может быть отрицательной"
            )


@dataclass(frozen=True)
class HourlyRate:
    value: Decimal

    def __post_init__(self):
        if self.value < 0:
            raise InvalidValueObject(
                "Тариф не может быть отрицательным"
            )