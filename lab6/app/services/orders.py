"""Бизнес-операции. Модуль НЕ импортирует strawberry."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app import db, events
from app.db.models import Dish, Order, OrderItem, Restaurant
from app.db.session import SessionLocal
from app.services.errors import (
    NotFound,
    OrderValidationError,
    TransitionNotAllowed,
)

# Допустимые переходы из таблицы 3
TRANSITIONS: dict[str, dict[str, str]] = {
    "accept": {"CREATED": "ACCEPTED"},
    "mark_ready": {"ACCEPTED": "READY"},
    "mark_delivered": {"READY": "DELIVERED"},
    "cancel": {"CREATED": "CANCELLED", "ACCEPTED": "CANCELLED"},
}


async def _transition(
    order_id: int,
    event_name: str,
    cancel_reason: str | None = None,
) -> Order:
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            raise NotFound(f"Заказ {order_id} не найден")

        target = TRANSITIONS[event_name].get(order.status)
        if target is None:
            raise TransitionNotAllowed(
                f"Событие {event_name} недопустимо в состоянии {order.status}"
            )

        order.status = target
        if event_name == "cancel":
            order.cancel_reason = cancel_reason

        await session.commit()
# ПОСЛЕ функция передает событие 
    await events.publish(events.OrderStatusChanged(order_id=order_id, status=target))
    return await db.get_order(order_id)


async def accept(order_id: int) -> Order:
    return await _transition(order_id, "accept")


async def mark_ready(order_id: int) -> Order:
    return await _transition(order_id, "mark_ready")


async def mark_delivered(order_id: int) -> Order:
    return await _transition(order_id, "mark_delivered")


async def cancel(order_id: int, reason: str) -> Order:
    if not reason or len(reason) < 3 or len(reason) > 200:
        raise OrderValidationError(
            "Причина отмены должна содержать от 3 до 200 символов"
        )
    return await _transition(order_id, "cancel", cancel_reason=reason)


async def create_order(
    restaurant_id: int,
    customer_name: str,
    delivery_address: str,
    items: list[tuple[int, int]],
) -> Order:
    if not customer_name:
        raise OrderValidationError("Имя клиента обязательно")
    if not delivery_address:
        raise OrderValidationError("Адрес доставки обязателен")
    if not items or len(items) < 1 or len(items) > 10:
        raise OrderValidationError("В заказе должно быть от 1 до 10 позиций")

    for _dish_id, qty in items:
        if qty < 1 or qty > 20:
            raise OrderValidationError("Количество порций должно быть от 1 до 20")

    async with SessionLocal() as session:
        restaurant = await session.get(Restaurant, restaurant_id)
        if restaurant is None:
            raise NotFound(f"Ресторан {restaurant_id} не найден")

        dish_ids = [dish_id for dish_id, _ in items]
        result = await session.execute(select(Dish).where(Dish.id.in_(dish_ids)))
        dishes = {d.id: d for d in result.scalars().all()}

        for dish_id, _qty in items:
            dish = dishes.get(dish_id)
            if dish is None:
                raise NotFound(f"Блюдо {dish_id} не найдено")
            if dish.restaurant_id != restaurant_id:
                raise OrderValidationError(
                    f"Блюдо {dish_id} не принадлежит ресторану {restaurant_id}"
                )

        total = Decimal("0")
        for dish_id, qty in items:
            total += dishes[dish_id].price * qty

        order = Order(
            restaurant_id=restaurant_id,
            customer_name=customer_name,
            delivery_address=delivery_address,
            status="CREATED",
            cancel_reason=None,
            total=total,
            created_at=datetime.now(timezone.utc),
        )
        session.add(order)
        await session.flush()

        for dish_id, qty in items:
            session.add(
                OrderItem(
                    order_id=order.id,
                    dish_id=dish_id,
                    quantity=qty,
                    price=dishes[dish_id].price,
                )
            )

        await session.commit()
        order_id = order.id

    return await db.get_order(order_id)
