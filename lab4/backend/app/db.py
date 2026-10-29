"""Синхронный доступ к PostgreSQL через SQLAlchemy Core и psycopg."""

from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    MetaData,
    Numeric,
    String,
    Table,
    create_engine,
    select,
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://app:app@localhost:5432/flights_db",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=20,
)
metadata = MetaData()
flights = Table(
    "flights",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("carrier", String(32), nullable=False),
    Column("flight_number", String(32), nullable=False),
    Column("origin", String(3), nullable=False),
    Column("destination", String(3), nullable=False),
    Column("departure_at", DateTime, nullable=False),
    Column("arrival_at", DateTime, nullable=False),
    Column("price", Numeric(10, 2), nullable=False),
    Index("ix_flights_departure_at", "departure_at"),
    Index("ix_flights_origin_departure", "origin", "departure_at"),
)


def get_local_flights(flight_date: date) -> list[dict[str, Any]]:
    """Выбирает рейсы за дату диапазонным условием, использующим индекс."""
    start = datetime.combine(flight_date, time.min)
    end = start + timedelta(days=1)
    statement = (
        select(
            flights.c.carrier,
            flights.c.flight_number,
            flights.c.origin,
            flights.c.destination,
            flights.c.departure_at,
            flights.c.arrival_at,
            flights.c.price,
        )
        .where(flights.c.departure_at >= start, flights.c.departure_at < end)
    )

    with engine.connect() as connection:
        rows = connection.execute(statement).mappings().all()

    return [
        {
            **dict(row),
            "price": float(Decimal(row["price"])),
        }
        for row in rows
    ]
