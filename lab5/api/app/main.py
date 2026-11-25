import asyncio
import logging
import time
from contextlib import asynccontextmanager # Превращения async-генератора в async-контекст-менеджер

from fastapi import FastAPI, HTTPException
from sqlalchemy import select, text

from .db import SessionLocal, engine
from .models import Account, Operation
from .rabbit import publisher
from .schemas import OperationIn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")


async def _wait_for_tables(timeout: float = 60.0) -> None: # Ждём, пока worker создаст таблицы
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            async with engine.connect() as conn: # Проверяем, есть ли таблица accounts.
                await conn.execute(text("SELECT 1 FROM accounts LIMIT 1"))
            return
        except Exception:
            await asyncio.sleep(1)
    logger.warning("Tables are still missing after %.1fs", timeout)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _wait_for_tables()
    try:
        await publisher._ensure()
    except Exception:
        logger.exception("Broker is not available on startup")
    yield
    await publisher.close() # корректно закрыть соединение.
    await engine.dispose() # закрыть пул соединений SQLAlchemy.


app = FastAPI(title="Loyalty API", lifespan=lifespan)


@app.post("/operations", status_code=202)
async def create_operation(op: OperationIn):
    payload = op.model_dump(mode="json") # превращает в dict
    ok = await publisher.publish_operation(payload, op.operation_id)# публикует в очередь. ok=False значит: две попытки провалились.
    if not ok:
        raise HTTPException(status_code=503, detail="Broker unavailable")
    return {"operation_id": op.operation_id} # тело ответа


@app.get("/operations/{operation_id}")
async def get_operation(operation_id: str):
    async with SessionLocal() as session: # гарантирует закрытие.
        row = await session.get(Operation, operation_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Not found")
        return {
            "operation_id": row.operation_id,
            "status": row.status,
            "points_delta": row.points_delta,
            "balance_after": row.balance_after,
            "reject_reason": row.reject_reason,
        }


@app.get("/accounts/{customer_id}")
async def get_account(customer_id: str):
    async with SessionLocal() as session:
        account = await session.get(Account, customer_id)
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")

        result = await session.execute(
            select(Operation)
            .where(Operation.customer_id == customer_id)
            .order_by(Operation.processed_at.desc())
            .limit(20)
        )
        operations = []
        for row in result.scalars().all():
            operations.append(
                {
                    "operation_id": row.operation_id,
                    "type": row.type,
                    "store_id": row.store_id,
                    "check_number": row.check_number,
                    "amount": str(row.amount) if row.amount is not None else None,
                    "points_delta": row.points_delta,
                    "balance_after": row.balance_after,
                    "status": row.status,
                    "reject_reason": row.reject_reason,
                    "occurred_at": row.occurred_at.isoformat(),
                    "processed_at": row.processed_at.isoformat(),
                }
            )

        return {
            "customer_id": account.customer_id,
            "balance": account.balance,
            "operations": operations,
        }


@app.get("/health")
async def health():
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    broker_ok = await publisher.is_healthy()

    if db_ok and broker_ok:
        return {"status": "ok", "db": True, "broker": True}
    raise HTTPException(
        status_code=503,
        detail={"status": "fail", "db": db_ok, "broker": broker_ok},
    )
