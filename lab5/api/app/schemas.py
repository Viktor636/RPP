from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, model_validator


class OperationIn(BaseModel):
    operation_id: str
    type: Literal["purchase", "return", "redeem"]
    customer_id: str
    store_id: str
    check_number: str
    amount: Optional[Decimal] = None
    points: Optional[int] = None
    occurred_at: datetime

    @model_validator(mode="after")
    def _validate(self) -> "OperationIn":
        if self.type in ("purchase", "redeem"):
            if self.amount is None:
                raise ValueError("amount is required for purchase/redeem")
            if self.amount <= 0:
                raise ValueError("amount must be positive")
        if self.type == "return" and self.amount is not None:
            raise ValueError("amount must be absent for return")

        if self.type == "redeem":
            if self.points is None:
                raise ValueError("points is required for redeem")
            if not isinstance(self.points, int) or self.points <= 0:
                raise ValueError("points must be a positive integer")
        else:
            if self.points is not None:
                raise ValueError("points must be absent for purchase/return")

        return self
