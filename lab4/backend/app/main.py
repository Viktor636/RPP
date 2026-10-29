"""Версия 3.3: синхронный FastAPI-сервис поиска авиамаршрутов."""

from __future__ import annotations

import os
import time
from datetime import date
from typing import Any

import requests
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from app.db import get_local_flights
from app.route_builder import build_routes

PROVIDER_TIMEOUT = float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "2.0"))
RETRY_DELAY = float(os.getenv("PROVIDER_RETRY_DELAY_SECONDS", "0.2"))
PROVIDERS = [
    ("provider1", os.getenv("PROVIDER1_URL", "http://localhost:8101")),
    ("provider2", os.getenv("PROVIDER2_URL", "http://localhost:8102")),
    ("provider3", os.getenv("PROVIDER3_URL", "http://localhost:8103")),
]

app = FastAPI(title="Агрегатор авиаперелётов", version="3.3-sync")


class ProviderUnavailable(Exception):
    """Поставщик не ответил в отведённые две секунды либо вернул ошибку."""


def fetch_provider_flights(provider_url: str, flight_date: date) -> list[dict[str, Any]]:
    """Запрашивает одного поставщика; бюджет 2 секунды включает возможный повтор."""
    deadline = time.monotonic() + PROVIDER_TIMEOUT
    for attempt in range(2):
        remaining = deadline - time.monotonic()
        if remaining <= 0.01:
            raise ProviderUnavailable("Истекло общее время ожидания поставщика")

        try:
            response = requests.get(
                f"{provider_url}/flights",
                params={"date": flight_date.isoformat()},
                timeout=remaining,
            )
        except requests.RequestException as exc:
            # Тайм-аут/сетевая ошибка не повторяются: повтор предусмотрен для HTTP 500.
            raise ProviderUnavailable(str(exc)) from exc

        if response.status_code >= 500:
            if attempt == 0:
                remaining = deadline - time.monotonic()
                if remaining > RETRY_DELAY + 0.05:
                    time.sleep(RETRY_DELAY)
                    continue
            raise ProviderUnavailable(f"HTTP {response.status_code}")

        if response.status_code >= 400:
            raise ProviderUnavailable(f"HTTP {response.status_code}")

        try:
            payload = response.json()
            provider_flights = payload["flights"]
            if not isinstance(provider_flights, list):
                raise ValueError("Поле flights должно быть списком")
            return provider_flights
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderUnavailable(f"Некорректный ответ: {exc}") from exc

    raise ProviderUnavailable("Поставщик не ответил")


def search_sync(origin: str, destination: str, flight_date: date) -> dict[str, Any]:
    """Бизнес-процесс синхронного поиска; отдельная функция для профилирования."""
    started = time.perf_counter()
    local_flights = get_local_flights(flight_date)
    all_flights = list(local_flights)
    unavailable: list[str] = []

    # В версии 3.3 поставщики опрашиваются последовательно.
    for provider_name, provider_url in PROVIDERS:
        try:
            all_flights.extend(fetch_provider_flights(provider_url, flight_date))
        except ProviderUnavailable:
            unavailable.append(provider_name)

    processing_time_ms = round((time.perf_counter() - started) * 1000, 2)
    if not local_flights and len(unavailable) == len(PROVIDERS):
        return {
            "http_status": 503,
            "origin": origin,
            "destination": destination,
            "date": flight_date.isoformat(),
            "routes": [],
            "unavailable_providers": unavailable,
            "processing_time_ms": processing_time_ms,
            "message": "Поиск временно недоступен: база не содержит рейсов, поставщики не ответили.",
        }

    routes = build_routes(all_flights, origin, destination, flight_date, limit=20)
    return {
        "http_status": 200,
        "origin": origin,
        "destination": destination,
        "date": flight_date.isoformat(),
        "routes": routes,
        "unavailable_providers": unavailable,
        "processing_time_ms": round((time.perf_counter() - started) * 1000, 2),
        "message": None,
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Лёгкий health endpoint без обращений к внешним сервисам и PostgreSQL."""
    return {"status": "ok"}


@app.get("/search")
def search(
    origin: str = Query(..., min_length=3, max_length=3, description="Код аэропорта вылета, например OVB"),
    destination: str = Query(..., min_length=3, max_length=3, description="Код аэропорта прилёта, например SVO"),
    date: date = Query(..., description="Дата вылета в формате YYYY-MM-DD"),
):
    origin = origin.upper()
    destination = destination.upper()
    if origin == destination:
        return JSONResponse(status_code=422, content={"detail": "Аэропорты вылета и прилёта должны отличаться."})

    payload = search_sync(origin, destination, date)
    status_code = int(payload.pop("http_status"))
    return JSONResponse(status_code=status_code, content=payload)
