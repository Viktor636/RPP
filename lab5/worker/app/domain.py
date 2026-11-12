from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR
from typing import Optional


@dataclass(frozen=True)
class OperationInput:
    operation_id: str
    type: str
    customer_id: str
    store_id: str
    check_number: str
    amount: Optional[Decimal]
    points: Optional[int]
    occurred_at: str


@dataclass(frozen=True)
class PurchaseInfo:
    customer_id: str
    points_awarded: int
    already_returned: bool


@dataclass(frozen=True)
class Decision:
    status: str
    points_delta: int
    reject_reason: Optional[str]


def compute_purchase_points(amount: Decimal) -> int:
    raw = (amount * Decimal("0.05")).to_integral_value(rounding=ROUND_FLOOR)
    return int(raw)


def decide(
    op: OperationInput,
    balance: int,
    purchase: Optional[PurchaseInfo] = None,
    duplicate_purchase: bool = False,
) -> Decision:
    if op.type == "purchase":
        if duplicate_purchase:
            return Decision("rejected", 0, "duplicate_purchase")
        assert op.amount is not None
        return Decision("applied", compute_purchase_points(op.amount), None)

    if op.type == "return":
        if purchase is None:
            return Decision("rejected", 0, "purchase_not_found")
        if purchase.customer_id != op.customer_id:
            return Decision("rejected", 0, "customer_mismatch")
        if purchase.already_returned:
            return Decision("rejected", 0, "already_returned")
        return Decision("applied", -purchase.points_awarded, None)

    if op.type == "redeem":
        assert op.amount is not None and op.points is not None
        limit = op.amount * Decimal("30") / Decimal("100")
        if Decimal(op.points) > limit:
            return Decision("rejected", 0, "limit_exceeded")
        if op.points > balance:
            return Decision("rejected", 0, "insufficient_balance")
        return Decision("applied", -op.points, None)

    raise ValueError(f"unknown operation type: {op.type}")
