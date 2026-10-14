from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.common.exceptions import (
    DomainInvariantViolation,
    EntityNotFound,
    InvalidValueObject,
    TransitionNotAllowed,
)


def _payload(code: str, message: str) -> dict:
    return {"error": code, "message": message}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(TransitionNotAllowed)
    async def _transition(_: Request, exc: TransitionNotAllowed):
        return JSONResponse(
            status_code=409,
            content=_payload("transition_not_allowed", str(exc)),
        )

    @app.exception_handler(DomainInvariantViolation)
    async def _invariant(_: Request, exc: DomainInvariantViolation):
        return JSONResponse(
            status_code=422,
            content=_payload("invariant_violation", str(exc)),
        )

    @app.exception_handler(InvalidValueObject)
    async def _vo(_: Request, exc: InvalidValueObject):
        return JSONResponse(
            status_code=422,
            content=_payload("invalid_value", str(exc)),
        )

    @app.exception_handler(EntityNotFound)
    async def _nf(_: Request, exc: EntityNotFound):
        return JSONResponse(
            status_code=404,
            content=_payload("not_found", str(exc)),
        )