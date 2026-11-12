import asyncio
import json
import logging
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI, HTTPException

from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analytics")


stats = {"received": 0}
stores: dict[str, dict] = {}
_consumer_task = None


def _new_store(store_id: str) -> dict:
    return {
        "store_id": store_id,
        "applied_purchase": 0,
        "applied_return": 0,
        "applied_redeem": 0,
        "rejected": 0,
        "points_accrued": 0,
        "points_returned": 0,
        "points_redeemed": 0,
    }


async def _on_event(msg: aio_pika.IncomingMessage) -> None:
    async with msg.process():
        event = json.loads(msg.body)
        stats["received"] += 1

        st = stores.setdefault(event["store_id"], _new_store(event["store_id"]))

        if event["status"] == "applied":
            st[f"applied_{event['type']}"] += 1
            delta = event["points_delta"]
            if event["type"] == "purchase":
                st["points_accrued"] += delta
            elif event["type"] == "return":
                st["points_returned"] += abs(delta)
            elif event["type"] == "redeem":
                st["points_redeemed"] += abs(delta)
        else:
            st["rejected"] += 1


async def _run_consumer() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        "loyalty.events", aio_pika.ExchangeType.FANOUT, durable=True
    )
    queue = await channel.declare_queue(
        "analytics.events", durable=True, arguments={"x-queue-type": "quorum"}
    )
    await queue.bind(exchange)

    await queue.consume(_on_event)
    logger.info("Analytics consumer is running")

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


app = FastAPI(title="Loyalty Analytics", lifespan=lifespan)


@app.get("/stores")
async def list_stores():
    return list(stores.values())


@app.get("/stores/{store_id}")
async def get_store(store_id: str):
    st = stores.get(store_id)
    if st is None:
        raise HTTPException(status_code=404, detail="Store not found")
    return st


@app.get("/stats")
async def get_stats():
    return {"received": stats["received"]}
