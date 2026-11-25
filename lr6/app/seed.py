"""Команда заполнения БД: python -m app.seed."""
import asyncio
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.db.models import Base, Dish, Order, OrderItem, Restaurant
from app.db.session import SessionLocal, engine

STATUSES = ["CREATED", "ACCEPTED", "READY", "DELIVERED", "CANCELLED"]


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        already = await session.scalar(select(Restaurant).limit(1))
        if already is not None:
            print("База уже заполнена, пропускаем сидирование.")
            return

        # 5 ресторанов
        restaurants: list[Restaurant] = []
        for i in range(1, 6):
            r = Restaurant(
                name=f"Ресторан {i}",
                address=f"ул. Примерная, д. {i * 10}",
            )
            session.add(r)
            restaurants.append(r)
        await session.flush()

        # по 10 блюд в каждом
        dishes_by_restaurant: dict[int, list[Dish]] = {}
        for r in restaurants:
            dishes: list[Dish] = []
            for j in range(1, 11):
                d = Dish(
                    restaurant_id=r.id,
                    name=f"Блюдо {r.id}-{j}",
                    price=Decimal(random.randint(150, 1500)),
                )
                session.add(d)
                dishes.append(d)
            dishes_by_restaurant[r.id] = dishes
        await session.flush()

        # 100 заказов, по 20 в каждом состоянии
        for i in range(100):
            status = STATUSES[i % 5]
            r = random.choice(restaurants)
            n_items = random.randint(1, 10)
            chosen = random.sample(dishes_by_restaurant[r.id], n_items)

            items_data: list[tuple[int, int, Decimal]] = []
            total = Decimal("0")
            for d in chosen:
                qty = random.randint(1, 20)
                items_data.append((d.id, qty, d.price))
                total += d.price * qty

            created_at = datetime.now(timezone.utc) - timedelta(
                minutes=random.randint(0, 60 * 24 * 30)
            )

            order = Order(
                restaurant_id=r.id,
                customer_name=f"Клиент {i + 1}",
                delivery_address=f"Адрес доставки {i + 1}",
                status=status,
                cancel_reason=(
                    "Клиент передумал" if status == "CANCELLED" else None
                ),
                total=total,
                created_at=created_at,
            )
            session.add(order)
            await session.flush()

            for dish_id, qty, price in items_data:
                session.add(
                    OrderItem(
                        order_id=order.id,
                        dish_id=dish_id,
                        quantity=qty,
                        price=price,
                    )
                )

        await session.commit()
        print("Готово: 5 ресторанов, 50 блюд, 100 заказов.")


if __name__ == "__main__":
    asyncio.run(main())
