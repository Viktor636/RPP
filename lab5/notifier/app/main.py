import asyncio
import json
import logging
import random
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import aio_pika
from fastapi import FastAPI, Query

from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notifier")


notifications: dict[str, list[dict]] = defaultdict(list)
stats = {"received": 0, "sent": 0}
_consumer_task = None


def _build_text(event: dict) -> str:
    if event["status"] == "applied":
        delta = event["points_delta"]
        if delta >= 0:
            return f"Начислено {delta} баллов, баланс {event['balance_after']}"
        return f"Списано {abs(delta)} баллов, баланс {event['balance_after']}"
    return f"Операция отклонена: {event['reject_reason']}"


async def _on_event(msg: aio_pika.IncomingMessage) -> None:
    async with msg.process():
        event = json.loads(msg.body)
        stats["received"] += 1
        customer_id = event["customer_id"]

        if customer_id in settings.unsubscribed:
            return

        delay = random.randint(settings.min_delay_ms, settings.max_delay_ms) / 1000
        await asyncio.sleep(delay)

        text = _build_text(event)
        logger.info("Notification to %s: %s", customer_id, text)

        notifications[customer_id].append(
            {
                "operation_id": event["operation_id"],
                "text": text,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        stats["sent"] += 1


async def _run_consumer() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        "loyalty.events", aio_pika.ExchangeType.FANOUT, durable=True
    )
    queue = await channel.declare_queue(
        "notifier.events", durable=True, arguments={"x-queue-type": "quorum"}
    )
    await queue.bind(exchange)

    await queue.consume(_on_event)
    logger.info("Notifier consumer is running")

    try:
        await asyncio.Future()
    finally:
        await connection.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer_task
    _consumer_task = asyncio.create_task(_run_consumer())
    yield
    if _consumer_task is not None:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except (asyncio.CancelledError, Exception):
            pass


app = FastAPI(title="Loyalty Notifier", lifespan=lifespan)


@app.get("/notifications")
async def get_notifications(customer_id: str = Query(...)):
    return notifications.get(customer_id, [])


@app.get("/stats")
async def get_stats():
    return {"received": stats["received"], "sent": stats["sent"]}
