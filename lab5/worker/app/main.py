import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import aio_pika
from sqlalchemy import select

from .config import settings
from .db import SessionLocal, engine
from .domain import OperationInput, PurchaseInfo, decide
from .models import Account, Base, Operation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

_publish_exchange = None


def _parse_operation(data: dict) -> OperationInput:
    amount = Decimal(data["amount"]) if data.get("amount") is not None else None
    points = int(data["points"]) if data.get("points") is not None else None
    return OperationInput(
        operation_id=data["operation_id"],
        type=data["type"],
        customer_id=data["customer_id"],
        store_id=data["store_id"],
        check_number=data["check_number"],
        amount=amount,
        points=points,
        occurred_at=data["occurred_at"],
    )


async def _load_purchase_context(session, op: OperationInput):
    if op.type == "purchase":
        result = await session.execute(
            select(Operation).where(
                Operation.check_number == op.check_number,
                Operation.type == "purchase",
                Operation.status == "applied",
            )
        )
        return result.scalar_one_or_none() is not None, None

    if op.type == "return":
        result = await session.execute(
            select(Operation).where(
                Operation.check_number == op.check_number,
                Operation.type == "purchase",
                Operation.status == "applied",
            )
        )
        purchase = result.scalar_one_or_none()
        if purchase is None:
            return False, None

        already = await session.execute(
            select(Operation).where(
                Operation.check_number == op.check_number,
                Operation.type == "return",
                Operation.status == "applied",
            )
        )
        already_returned = already.scalar_one_or_none() is not None
        return False, PurchaseInfo(
            customer_id=purchase.customer_id,
            points_awarded=purchase.points_delta,
            already_returned=already_returned,
        )

    return False, None


async def _process(msg: aio_pika.IncomingMessage) -> None:
    data = json.loads(msg.body)
    op = _parse_operation(data)

    event: Optional[dict] = None

    # ОДИН блок begin() на всю работу с БД — и проверка existing, и запись.
    async with SessionLocal() as session:
        async with session.begin():
            existing = await session.get(Operation, op.operation_id)
            if existing is not None:
                # уже обработано ранее (повторная доставка) — коммитим пустую транзакцию
                logger.info("Operation %s already processed, skipping", op.operation_id)
            else:
                account = await session.get(
                    Account, op.customer_id, with_for_update=True
                )
                if account is None:
                    account = Account(customer_id=op.customer_id, balance=0)
                    session.add(account)
                    await session.flush()

                balance = account.balance
                duplicate, purchase = await _load_purchase_context(session, op)
                decision = decide(op, balance, purchase, duplicate)

                new_balance = balance + decision.points_delta
                if decision.status == "applied":
                    account.balance = new_balance

                processed_at = datetime.now(timezone.utc)
                session.add(
                    Operation(
                        operation_id=op.operation_id,
                        type=op.type,
                        customer_id=op.customer_id,
                        store_id=op.store_id,
                        check_number=op.check_number,
                        amount=op.amount,
                        points_delta=decision.points_delta,
                        balance_after=new_balance
                        if decision.status == "applied"
                        else balance,
                        status=decision.status,
                        reject_reason=decision.reject_reason,
                        occurred_at=datetime.fromisoformat(op.occurred_at),
                        processed_at=processed_at,
                    )
                )

                event = {
                    "operation_id": op.operation_id,
                    "type": op.type,
                    "customer_id": op.customer_id,
                    "store_id": op.store_id,
                    "status": decision.status,
                    "points_delta": decision.points_delta,
                    "balance_after": new_balance
                    if decision.status == "applied"
                    else balance,
                    "reject_reason": decision.reject_reason,
                    "processed_at": processed_at.isoformat(),
                }

    # Если это была повторная доставка — публиковать нечего, просто ack
    if event is None:
        await msg.ack()
        return

    # Публикуем событие ПОСЛЕ коммита, с publisher confirms
    assert _publish_exchange is not None
    message = aio_pika.Message(
        body=json.dumps(event).encode("utf-8"),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        message_id=op.operation_id,
        content_type="application/json",
    )
    await _publish_exchange.publish(message, routing_key="", timeout=10)
    await msg.ack()


async def _on_operation(msg: aio_pika.IncomingMessage) -> None:
    try:
        await _process(msg)
    except Exception:
        logger.exception("Failed to process message %s", msg.message_id)
        try:
            await msg.nack(requeue=True)
        except Exception:
            pass


async def main() -> None:
    global _publish_exchange

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    connection = await aio_pika.connect_robust(settings.rabbitmq_url)

    consume_channel = await connection.channel()
    await consume_channel.set_qos(prefetch_count=1)

    exchange = await consume_channel.declare_exchange(
        "loyalty", aio_pika.ExchangeType.DIRECT, durable=True
    )
    queue = await consume_channel.declare_queue(
        "operations", durable=True, arguments={"x-queue-type": "quorum"}
    )
    await queue.bind(exchange, routing_key="operation")

    events_exchange = await consume_channel.declare_exchange(
        "loyalty.events", aio_pika.ExchangeType.FANOUT, durable=True
    )
    notifier_queue = await consume_channel.declare_queue(
        "notifier.events", durable=True, arguments={"x-queue-type": "quorum"}
    )
    analytics_queue = await consume_channel.declare_queue(
        "analytics.events", durable=True, arguments={"x-queue-type": "quorum"}
    )
    await notifier_queue.bind(events_exchange)
    await analytics_queue.bind(events_exchange)

    publish_channel = await connection.channel(publisher_confirms=True)
    _publish_exchange = await publish_channel.declare_exchange(
        "loyalty.events", aio_pika.ExchangeType.FANOUT, durable=True
    )

    await queue.consume(_on_operation)
    logger.info("Worker is ready")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
