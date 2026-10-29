"""Заполняет собственную базу 1500 детерминированными рейсами на день."""

from __future__ import annotations

import os
from datetime import date, timedelta
from itertools import islice

from sqlalchemy import insert, text

from app.db import engine, flights, metadata
from app.flight_generator import generate_daily_flights


def chunks(items, size: int):
    iterator = iter(items)
    while batch := list(islice(iterator, size)):
        yield batch


def main() -> None:
    start_date = date.fromisoformat(os.getenv("SCHEDULE_START_DATE", "2026-10-26"))
    days = int(os.getenv("SCHEDULE_DAYS", "120"))
    per_day = int(os.getenv("OWN_FLIGHTS_PER_DAY", "1500"))
    metadata.create_all(engine)

    print(f"Сброс таблицы flights; начало={start_date}, дней={days}, рейсов/день={per_day}")
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE flights RESTART IDENTITY"))
        buffered: list[dict] = []
        total = 0
        for offset in range(days):
            flight_date = start_date + timedelta(days=offset)
            day_flights = generate_daily_flights(
                flight_date=flight_date,
                count=per_day,
                seed=20261026 + offset,
                carrier="OWN",
            )
            buffered.extend(day_flights)
            if len(buffered) >= 5000:
                connection.execute(insert(flights), buffered)
                total += len(buffered)
                buffered = []
        if buffered:
            connection.execute(insert(flights), buffered)
            total += len(buffered)

    print(f"Готово: загружено {total} рейсов.")


if __name__ == "__main__":
    main()
