"""Передача событий внутри процесса через asyncio.Queue."""
import asyncio
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class OrderStatusChanged:
    order_id: int
    status: str


_subscribers: dict[int, set[asyncio.Queue]] = defaultdict(set)


async def subscribe(order_id: int) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers[order_id].add(queue)
    return queue


async def unsubscribe(order_id: int, queue: asyncio.Queue) -> None:
    subs = _subscribers.get(order_id)
    if not subs:
        return
    subs.discard(queue)
    if not subs:
        _subscribers.pop(order_id, None)


async def publish(event: OrderStatusChanged) -> None:
    for queue in list(_subscribers.get(event.order_id, ())):
        await queue.put(event)
