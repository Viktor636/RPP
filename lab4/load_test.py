"""Нагрузочный скрипт: замкнутый/открытый профиль + замеры GET /health."""

from __future__ import annotations

import argparse
import asyncio
import math
import random
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx


@dataclass
class Metrics:
    latencies_ms: list[float] = field(default_factory=list)
    errors: int = 0

    def add(self, elapsed_ms: float, failed: bool) -> None:
        self.latencies_ms.append(elapsed_ms)
        if failed:
            self.errors += 1

    def summary(self, measurement_seconds: float) -> dict[str, float | int]:
        values = sorted(self.latencies_ms)
        count = len(values)
        if not count:
            return {"count": 0, "rps": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "max_ms": 0.0, "errors_pct": 0.0}

        def percentile(p: float) -> float:
            index = max(0, min(count - 1, math.ceil(count * p) - 1))
            return values[index]

        return {
            "count": count,
            "rps": round(count / measurement_seconds, 2),
            "p50_ms": round(percentile(0.50), 2),
            "p95_ms": round(percentile(0.95), 2),
            "p99_ms": round(percentile(0.99), 2),
            "max_ms": round(values[-1], 2),
            "errors_pct": round(100 * self.errors / count, 2),
        }


async def timed_get(client: httpx.AsyncClient, url: str, params: Optional[dict], metrics: Metrics, record_after: float, stop_at: float) -> None:
    started = time.perf_counter()
    wall_start = asyncio.get_running_loop().time()
    failed = False
    try:
        response = await client.get(url, params=params)
        failed = response.status_code >= 400
    except (httpx.HTTPError, asyncio.TimeoutError):
        failed = True
    elapsed_ms = (time.perf_counter() - started) * 1000
    if wall_start >= record_after and wall_start <= stop_at:
        metrics.add(elapsed_ms, failed)


async def closed_worker(
    client: httpx.AsyncClient,
    url: str,
    params: dict,
    metrics: Metrics,
    record_after: float,
    stop_at: float,
) -> None:
    loop = asyncio.get_running_loop()
    while loop.time() < stop_at:
        await timed_get(client, url, params, metrics, record_after, stop_at)


async def open_scheduler(
    client: httpx.AsyncClient,
    url: str,
    params: dict,
    metrics: Metrics,
    rate: float,
    record_after: float,
    stop_at: float,
) -> None:
    loop = asyncio.get_running_loop()
    pending: set[asyncio.Task] = set()
    while loop.time() < stop_at:
        task = asyncio.create_task(timed_get(client, url, params, metrics, record_after, stop_at))
        pending.add(task)
        task.add_done_callback(pending.discard)
        await asyncio.sleep(random.expovariate(rate))
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


async def health_sampler(
    client: httpx.AsyncClient,
    base_url: str,
    metrics: Metrics,
    record_after: float,
    stop_at: float,
) -> None:
    """Запускает проверку /health каждые 100 мс, не дожидаясь предыдущей."""
    loop = asyncio.get_running_loop()
    pending: set[asyncio.Task] = set()
    next_tick = loop.time()
    while next_tick < stop_at:
        task = asyncio.create_task(timed_get(client, f"{base_url}/health", None, metrics, record_after, stop_at))
        pending.add(task)
        task.add_done_callback(pending.discard)
        next_tick += 0.1
        await asyncio.sleep(max(0.0, next_tick - loop.time()))
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


async def run(args: argparse.Namespace) -> None:
    base_url = args.url.rstrip("/")
    search_url = f"{base_url}/search"
    params = {"origin": args.origin, "destination": args.destination, "date": args.date}
    timeout = httpx.Timeout(args.timeout)
    limits = httpx.Limits(max_connections=2000, max_keepalive_connections=500)
    search_metrics = Metrics()
    health_metrics = Metrics()

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        loop = asyncio.get_running_loop()
        started = loop.time()
        record_after = started + args.warmup
        stop_at = record_after + args.duration
        health_task = asyncio.create_task(health_sampler(client, base_url, health_metrics, record_after, stop_at))

        if args.mode == "closed":
            tasks = [
                asyncio.create_task(closed_worker(client, search_url, params, search_metrics, record_after, stop_at))
                for _ in range(args.clients)
            ]
            await asyncio.gather(*tasks)
        else:
            await open_scheduler(
                client, search_url, params, search_metrics, args.rate, record_after, stop_at
            )

        await health_task

    print(f"Режим: {args.mode}; прогрев: {args.warmup} с; измерение: {args.duration} с")
    if args.mode == "closed":
        print(f"Число клиентов C: {args.clients}")
    else:
        print(f"Целевая интенсивность: {args.rate} запросов/с")
    print("/search:", search_metrics.summary(args.duration))
    print("/health:", health_metrics.summary(args.duration))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000", help="Базовый URL сервиса поиска")
    parser.add_argument("--mode", choices=("closed", "open"), default="closed")
    parser.add_argument("--clients", type=int, default=10, help="Число клиентов для замкнутого режима")
    parser.add_argument("--rate", type=float, default=5.0, help="Запросов/с для открытого режима")
    parser.add_argument("--duration", type=float, default=60.0, help="Длительность измерения, секунд")
    parser.add_argument("--warmup", type=float, default=10.0, help="Длительность прогрева, секунд")
    parser.add_argument("--timeout", type=float, default=30.0, help="Тайм-аут запроса, секунд")
    parser.add_argument("--origin", default="OVB")
    parser.add_argument("--destination", default="SVO")
    parser.add_argument("--date", default="2026-10-26")
    args = parser.parse_args()
    if args.clients < 1 or args.rate <= 0 or args.duration <= 0 or args.warmup < 0:
        parser.error("clients/rate/duration должны быть положительными, warmup не может быть отрицательным")
    return args


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
