"""Одна настраиваемая заглушка авиапоставщика на FastAPI."""

from __future__ import annotations

import asyncio
import os
import random
from datetime import date

from fastapi import FastAPI, Query, Response

from flight_generator import generate_daily_flights

PROVIDER_ID = os.getenv("PROVIDER_ID", "1")
CARRIER = f"P{PROVIDER_ID}"
BASE_DELAY_MS = int(os.getenv("BASE_DELAY_MS", "300"))
DELAY_JITTER = float(os.getenv("DELAY_JITTER", "0.30"))
ERROR_RATE = float(os.getenv("ERROR_RATE", "0.05"))
SLOW_RATE = float(os.getenv("SLOW_RATE", "0.0"))
SLOW_DELAY_SECONDS = float(os.getenv("SLOW_DELAY_SECONDS", "3.0"))
FLIGHTS_PER_DAY = int(os.getenv("PROVIDER_FLIGHTS_PER_DAY", "500"))

app = FastAPI(title=f"Заглушка поставщика {CARRIER}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "provider": CARRIER}


@app.get("/flights")
async def get_flights(flight_date: date = Query(..., alias="date", description="Дата вылета YYYY-MM-DD")):
    """Эмулирует заданные для поставщика задержки и вероятность HTTP 500."""
    chance = random.random()
    if chance < ERROR_RATE:
        # Ошибка возвращается быстро, чтобы агрегатор мог повторить запрос.
        return Response(
            content='{"detail":"temporary provider error"}',
            status_code=500,
            media_type="application/json",
        )
    if chance < ERROR_RATE + SLOW_RATE:
        await asyncio.sleep(SLOW_DELAY_SECONDS)
    else:
        low = BASE_DELAY_MS * (1.0 - DELAY_JITTER) / 1000
        high = BASE_DELAY_MS * (1.0 + DELAY_JITTER) / 1000
        await asyncio.sleep(random.uniform(low, high))

    day_seed = flight_date.toordinal() * 100 + int(PROVIDER_ID)
    flights = generate_daily_flights(
        flight_date=flight_date,
        count=FLIGHTS_PER_DAY,
        seed=day_seed,
        carrier=CARRIER,
    )
    serialized = [
        {
            **flight,
            "departure_at": flight["departure_at"].isoformat(timespec="seconds"),
            "arrival_at": flight["arrival_at"].isoformat(timespec="seconds"),
            "price": float(flight["price"]),
        }
        for flight in flights
    ]
    return {"provider": CARRIER, "flights": serialized}
