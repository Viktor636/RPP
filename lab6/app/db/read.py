"""Функции чтения данных. Модуль НЕ импортирует strawberry."""
from sqlalchemy import select

from app.db.models import Dish, Order, OrderItem, Restaurant
from app.db.session import SessionLocal


# ---- чтение по одному идентификатору ----
async def get_restaurant(id: int) -> Restaurant | None:
    async with SessionLocal() as session:
        return await session.get(Restaurant, id)


async def get_dish(id: int) -> Dish | None:
    async with SessionLocal() as session:
        return await session.get(Dish, id)


async def get_order(id: int) -> Order | None:
    async with SessionLocal() as session:
        return await session.get(Order, id)


async def get_items(order_id: int) -> list[OrderItem]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        return list(result.scalars().all())


# ---- чтение по спискам идентификаторов (один SQL-запрос каждая) ----
async def get_restaurants(ids: list[int]) -> dict[int, Restaurant]:
    if not ids:
        return {} # При пустом in возвращаем пустой словарь
    async with SessionLocal() as session:
        result = await session.execute(
            select(Restaurant).where(Restaurant.id.in_(ids))
        )
        return {r.id: r for r in result.scalars().all()}


async def get_dishes(ids: list[int]) -> dict[int, Dish]:
    if not ids:
        return {}
    async with SessionLocal() as session:
        result = await session.execute(
            select(Dish).where(Dish.id.in_(ids))
        )
        return {d.id: d for d in result.scalars().all()}


async def get_items_by_orders(order_ids: list[int]) -> dict[int, list[OrderItem]]:
    if not order_ids:
        return {}
    async with SessionLocal() as session:
        result = await session.execute(
            select(OrderItem).where(OrderItem.order_id.in_(order_ids))
        )
        out: dict[int, list[OrderItem]] = {oid: [] for oid in order_ids}
        for item in result.scalars().all():
            out[item.order_id].append(item)
        return out


# ---- список заказов ----
async def list_orders(status: str | None = None) -> list[Order]:
    async with SessionLocal() as session:
        stmt = select(Order).order_by(Order.created_at.desc()) # Сортировка по убыванию
        if status:
            stmt = stmt.where(Order.status == status)
        result = await session.execute(stmt)
        return list(result.scalars().all())


# ---- вспомогательные функции (для связанных полей схемы) ----
async def list_restaurants() -> list[Restaurant]:
    async with SessionLocal() as session:
        result = await session.execute(select(Restaurant).order_by(Restaurant.id))
        return list(result.scalars().all())


async def get_dishes_by_restaurant(restaurant_id: int) -> list[Dish]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Dish).where(Dish.restaurant_id == restaurant_id).order_by(Dish.id)
        )
        return list(result.scalars().all())
