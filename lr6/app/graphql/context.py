"""Загрузчики и context_getter. Новые DataLoader на каждый запрос."""
from strawberry.dataloader import DataLoader
from strawberry.fastapi import BaseContext

from app import db


async def _load_restaurants(ids: list[int]):
    mapping = await db.get_restaurants(ids)
    return [mapping.get(i) for i in ids]


async def _load_dishes(ids: list[int]):
    mapping = await db.get_dishes(ids)
    return [mapping.get(i) for i in ids]


async def _load_items(order_ids: list[int]):
    mapping = await db.get_items_by_orders(order_ids)
    return [mapping.get(oid, []) for oid in order_ids]


class Context(BaseContext):
    def __init__(self) -> None:
        super().__init__()
        self.restaurant_loader = DataLoader(load_fn=_load_restaurants)
        self.dish_loader = DataLoader(load_fn=_load_dishes)
        self.items_loader = DataLoader(load_fn=_load_items)


async def get_context() -> Context:
    return Context()
