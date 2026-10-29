"""Построение прямых маршрутов и маршрутов максимум с двумя пересадками.

Модуль не обращается ни к сети, ни к БД: он работает только с переданными рейсами.
"""

from __future__ import annotations

import heapq
from bisect import bisect_left, bisect_right
from datetime import date, datetime, time, timedelta
from typing import Any

MIN_CONNECTION = timedelta(hours=1)
MAX_CONNECTION = timedelta(hours=6)
MAX_LEGS = 3  # прямой рейс + максимум две пересадки
TOP_ROUTES = 20


def _as_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _normalize_flight(flight: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(flight)
    normalized["departure_at"] = _as_datetime(flight["departure_at"])
    normalized["arrival_at"] = _as_datetime(flight["arrival_at"])
    normalized["price"] = float(flight["price"])
    return normalized


def build_routes(
    all_flights: list[dict[str, Any]],
    origin: str,
    destination: str,
    flight_date: date,
    limit: int = TOP_ROUTES,
) -> list[dict[str, Any]]:
    """Находит допустимые маршруты и возвращает limit самых дешёвых."""
    if origin == destination:
        return []

    day_start = datetime.combine(flight_date, time.min)
    day_end = day_start + timedelta(days=1)
    by_origin: dict[str, list[dict[str, Any]]] = {}

    for raw_flight in all_flights:
        flight = _normalize_flight(raw_flight)
        # Все рейсы в маршруте должны ВЫЛЕТАТЬ именно в день поиска.
        if not (day_start <= flight["departure_at"] < day_end):
            continue
        if flight["origin"] == flight["destination"]:
            continue
        by_origin.setdefault(flight["origin"], []).append(flight)

    departure_times: dict[str, list[datetime]] = {}
    for airport, airport_flights in by_origin.items():
        airport_flights.sort(key=lambda item: item["departure_at"])
        departure_times[airport] = [item["departure_at"] for item in airport_flights]

    # В куче сохраняем только limit самых дешёвых маршрутов.
    # Первый элемент с отрицательной ценой соответствует самому дорогому из сохранённых.
    best: list[tuple[float, int, dict[str, Any]]] = []
    sequence = 0

    def save_route(path: list[dict[str, Any]], total_price: float) -> None:
        nonlocal sequence
        first = path[0]
        last = path[-1]
        route = {
            "flights": [
                {
                    "carrier": item["carrier"],
                    "flight_number": item["flight_number"],
                    "origin": item["origin"],
                    "destination": item["destination"],
                    "departure_at": item["departure_at"].isoformat(timespec="seconds"),
                    "arrival_at": item["arrival_at"].isoformat(timespec="seconds"),
                    "price": round(item["price"], 2),
                }
                for item in path
            ],
            "total_price": round(total_price, 2),
            "stops": len(path) - 1,
            "duration_minutes": int((last["arrival_at"] - first["departure_at"]).total_seconds() // 60),
        }
        sequence += 1
        entry = (-total_price, sequence, route)
        if len(best) < limit:
            heapq.heappush(best, entry)
        elif total_price < -best[0][0]:
            heapq.heapreplace(best, entry)

    def walk(
        current_airport: str,
        previous_arrival: datetime | None,
        path: list[dict[str, Any]],
        visited_airports: set[str],
        total_price: float,
    ) -> None:
        if len(path) >= MAX_LEGS:
            return
        candidates = by_origin.get(current_airport, [])
        if not candidates:
            return

        if previous_arrival is None:
            left, right = 0, len(candidates)
        else:
            earliest = previous_arrival + MIN_CONNECTION
            latest = previous_arrival + MAX_CONNECTION
            times = departure_times[current_airport]
            left = bisect_left(times, earliest)
            right = bisect_right(times, latest)

        for flight in candidates[left:right]:
            next_airport = flight["destination"]
            if next_airport in visited_airports:
                continue
            if previous_arrival is not None:
                connection = flight["departure_at"] - previous_arrival
                if connection < MIN_CONNECTION or connection > MAX_CONNECTION:
                    continue

            new_path = [*path, flight]
            new_price = total_price + flight["price"]
            if next_airport == destination:
                save_route(new_path, new_price)
                continue
            walk(
                next_airport,
                flight["arrival_at"],
                new_path,
                visited_airports | {next_airport},
                new_price,
            )

    walk(origin, None, [], {origin}, 0.0)
    routes = [entry[2] for entry in best]
    routes.sort(key=lambda item: (item["total_price"], item["duration_minutes"], item["stops"]))
    return routes
