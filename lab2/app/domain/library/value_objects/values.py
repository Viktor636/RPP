from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ..exceptions.exceptions import InvalidValueObject


@dataclass(frozen=True)
class BookId:
    value: UUID

    def __post_init__(self):
        if not isinstance(self.value, UUID):
            raise InvalidValueObject("BookId должен содержать UUID")


@dataclass(frozen=True)
class CopyId:
    value: UUID

    def __post_init__(self):
        if not isinstance(self.value, UUID):
            raise InvalidValueObject("CopyId должен содержать UUID")


@dataclass(frozen=True)
class ReaderId:
    value: UUID

    def __post_init__(self):
        if not isinstance(self.value, UUID):
            raise InvalidValueObject("ReaderId должен содержать UUID")


@dataclass(frozen=True)
class LoanId:
    value: UUID

    def __post_init__(self):
        if not isinstance(self.value, UUID):
            raise InvalidValueObject("LoanId должен содержать UUID")


@dataclass(frozen=True)
class Fine:
    amount: Decimal

    def __post_init__(self):
        if self.amount < Decimal("0"):
            raise InvalidValueObject(
                "Штраф не может быть отрицательным"
            )


@dataclass(frozen=True)
class LoanPeriod:
    started_at: datetime
    due_at: datetime

    def __post_init__(self):
        if self.due_at <= self.started_at:
            raise InvalidValueObject(
                "Срок возврата должен быть позже даты выдачи"
            )