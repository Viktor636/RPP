import asyncio
import json
import logging

import aio_pika

from .config import settings

logger = logging.getLogger(__name__)


class Publisher:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._connection = None
        self._channel = None
        self._exchange = None

    async def _ensure(self) -> None:
        if (
            self._connection is not None
            and not self._connection.is_closed
            and self._channel is not None
            and not self._channel.is_closed
            and self._exchange is not None
        ):
            return

        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel(publisher_confirms=True)
        self._exchange = await self._channel.declare_exchange(
            "loyalty", aio_pika.ExchangeType.DIRECT, durable=True
        )
        queue = await self._channel.declare_queue(
            "operations", durable=True, arguments={"x-queue-type": "quorum"}
        )
        await queue.bind(self._exchange, routing_key="operation")

    async def _reset(self) -> None:
        try:
            if self._connection is not None and not self._connection.is_closed:
                await self._connection.close()
        except Exception:
            pass
        self._connection = None
        self._channel = None
        self._exchange = None

    async def publish_operation(self, payload: dict, operation_id: str) -> bool:
        async with self._lock:
            for _ in range(2):
                try:
                    await self._ensure()
                    message = aio_pika.Message(
                        body=json.dumps(payload).encode("utf-8"),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        message_id=operation_id,
                        content_type="application/json",
                    )
                    await self._exchange.publish(
                        message, routing_key="operation", timeout=5
                    )
                    return True
                except Exception:
                    logger.exception("Publish failed, retrying after reset")
                    await self._reset()
            return False

    async def is_healthy(self) -> bool:
        async with self._lock:
            try:
                await self._ensure()
                return self._connection is not None and not self._connection.is_closed
            except Exception:
                return False

    async def close(self) -> None:
        async with self._lock:
            await self._reset()


publisher = Publisher()
