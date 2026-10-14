from __future__ import annotations

from abc import ABC
from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.common.exceptions import TransitionNotAllowed

if TYPE_CHECKING:
    from app.domain.library.loan import Loan


class LoanState(ABC):
    name: str = "Unknown"

    def on_issue(self, loan: "Loan", now: datetime) -> "LoanState":
        raise TransitionNotAllowed(self.name, "issue")

    def on_reject(self, loan: "Loan", now: datetime) -> "LoanState":
        raise TransitionNotAllowed(self.name, "reject")

    def on_cancel_booking(self, loan: "Loan", now: datetime) -> "LoanState":
        raise TransitionNotAllowed(self.name, "cancel_booking")

    def on_extend(self, loan: "Loan", now: datetime) -> "LoanState":
        raise TransitionNotAllowed(self.name, "extend")

    def on_return_ok(self, loan: "Loan", now: datetime) -> "LoanState":
        raise TransitionNotAllowed(self.name, "return_ok")

    def on_return_damaged(self, loan: "Loan", now: datetime) -> "LoanState":
        raise TransitionNotAllowed(self.name, "return_damaged")

    def on_due_date_passed(self, loan: "Loan", now: datetime) -> "LoanState":
        raise TransitionNotAllowed(self.name, "due_date_passed")

    def on_thirty_days_passed(self, loan: "Loan", now: datetime) -> "LoanState":
        raise TransitionNotAllowed(self.name, "thirty_days_passed")

    def allowed_events(self) -> tuple[str, ...]:
        return ()


class Reserved(LoanState):
    name = "Reserved"

    def on_issue(self, loan: "Loan", now: datetime) -> "LoanState":
        loan._record_issue(now)
        return Issued()

    def on_reject(self, loan: "Loan", now: datetime) -> "LoanState":
        return Rejected()

    def on_cancel_booking(self, loan: "Loan", now: datetime) -> "LoanState":
        return Cancelled()

    def allowed_events(self) -> tuple[str, ...]:
        return ("issue", "reject", "cancel_booking")


class Issued(LoanState):
    name = "Issued"

    def on_extend(self, loan: "Loan", now: datetime) -> "LoanState":
        loan._extend_period(now, days=7)
        return Extended()

    def on_return_ok(self, loan: "Loan", now: datetime) -> "LoanState":
        loan._close(now, damaged=False)
        return ReturnedOk()

    def on_return_damaged(self, loan: "Loan", now: datetime) -> "LoanState":
        loan._close(now, damaged=True)
        return ReturnedDamaged()

    def on_due_date_passed(self, loan: "Loan", now: datetime) -> "LoanState":
        return Overdue()

    def allowed_events(self) -> tuple[str, ...]:
        return ("extend", "return_ok", "return_damaged", "due_date_passed")


class Extended(LoanState):
    name = "Extended"

    def on_return_ok(self, loan: "Loan", now: datetime) -> "LoanState":
        loan._close(now, damaged=False)
        return ReturnedOk()

    def on_return_damaged(self, loan: "Loan", now: datetime) -> "LoanState":
        loan._close(now, damaged=True)
        return ReturnedDamaged()

    def on_due_date_passed(self, loan: "Loan", now: datetime) -> "LoanState":
        return Overdue()

    def allowed_events(self) -> tuple[str, ...]:
        return ("return_ok", "return_damaged", "due_date_passed")


class Overdue(LoanState):
    name = "Overdue"

    def on_return_ok(self, loan: "Loan", now: datetime) -> "LoanState":
        loan._close(now, damaged=False)
        return ReturnedFine()

    def on_return_damaged(self, loan: "Loan", now: datetime) -> "LoanState":
        loan._close(now, damaged=True)
        return ReturnedDamaged()

    def on_thirty_days_passed(self, loan: "Loan", now: datetime) -> "LoanState":
        return Blocked()

    def allowed_events(self) -> tuple[str, ...]:
        return ("return_ok", "return_damaged", "thirty_days_passed")


class ReturnedOk(LoanState):
    name = "ReturnedOk"


class ReturnedFine(LoanState):
    name = "ReturnedFine"


class ReturnedDamaged(LoanState):
    name = "ReturnedDamaged"


class Cancelled(LoanState):
    name = "Cancelled"


class Rejected(LoanState):
    name = "Rejected"


class Blocked(LoanState):
    name = "Blocked"


STATE_REGISTRY: dict[str, type[LoanState]] = {
    cls.name: cls for cls in (
        Reserved, Issued, Extended, Overdue,
        ReturnedOk, ReturnedFine, ReturnedDamaged,
        Cancelled, Rejected, Blocked,
    )
}