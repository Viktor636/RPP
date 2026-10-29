"""Детерминированная генерация рейсов для БД и заглушек поставщиков."""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

AIRPORTS: tuple[str, ...] = (
    "SVO", "DME", "VKO", "LED", "OVB", "KJA", "KZN", "SVX", "AER", "KHV",
    "VVO", "UFA", "GOJ", "ROV", "KRR", "CEK", "OMS", "IKT", "UUS", "PKC",
    "MRV", "MMK", "ARH", "HTA", "BAX", "NOZ", "YKS", "MJZ", "REN", "PEE",
)


def generate_daily_flights(
    *,
    flight_date: date,
    count: int,
    seed: int,
    carrier: str,
) -> list[dict[str, Any]]:
    """Возвращает одинаковый набор рейсов при одинаковых аргументах."""
    rng = random.Random(seed)
    day_start = datetime.combine(flight_date, time.min)
    result: list[dict[str, Any]] = []

    for number in range(1, count + 1):
        origin_index = rng.randrange(len(AIRPORTS))
        destination_index = rng.randrange(len(AIRPORTS) - 1)
        if destination_index >= origin_index:
            destination_index += 1

        origin = AIRPORTS[origin_index]
        destination = AIRPORTS[destination_index]
        departure_at = day_start + timedelta(minutes=rng.randrange(24 * 60))
        arrival_at = departure_at + timedelta(minutes=rng.randint(60, 360))
        price = Decimal(rng.randint(2500, 45000)).quantize(Decimal("0.01"))
        date_key = flight_date.strftime("%Y%m%d")

        result.append(
            {
                "carrier": carrier,
                "flight_number": f"{carrier}-{date_key}-{number:04d}",
                "origin": origin,
                "destination": destination,
                "departure_at": departure_at,
                "arrival_at": arrival_at,
                "price": price,
            }
        )

    return result
