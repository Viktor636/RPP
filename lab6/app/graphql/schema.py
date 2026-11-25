"""Схема GraphQL. Обработчики только вызывают db / services."""
import enum
import functools
from typing import AsyncGenerator, Optional

import strawberry
from graphql import GraphQLError
from strawberry.types import Info

from app import db, events, services


def _handle_errors(func):
    """Превращает исключения services в стандартные GraphQL-ошибки."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except services.NotFound as exc:
            raise GraphQLError(
                str(exc), extensions={"code": "NOT_FOUND"}
            ) from exc
        except services.TransitionNotAllowed as exc:
            raise GraphQLError(
                str(exc), extensions={"code": "TRANSITION_NOT_ALLOWED"}
            ) from exc
        except services.OrderValidationError as exc:
            raise GraphQLError(
                str(exc), extensions={"code": "VALIDATION_ERROR"}
            ) from exc
        except GraphQLError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise GraphQLError(
                "Internal error", extensions={"code": "INTERNAL_ERROR"}
            ) from exc

    return wrapper


@strawberry.enum
class OrderStatus(enum.Enum):
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# ---------- Типы схемы ----------
@strawberry.type
class Dish:
    id: int
    name: str

    @strawberry.field
    def price(self) -> float:
        return float(self.price)

    @strawberry.field
    async def restaurant(self, info: Info) -> "Restaurant":
        return await info.context.restaurant_loader.load(self.restaurant_id)


@strawberry.type
class Restaurant:
    id: int
    name: str
    address: str

    @strawberry.field
    async def dishes(self, info: Info) -> list[Dish]:
        return await db.get_dishes_by_restaurant(self.id)


@strawberry.type
class OrderItem:
    quantity: int

    @strawberry.field
    def price(self) -> float:
        return float(self.price)

    @strawberry.field
    def amount(self) -> float:
        return float(self.price) * self.quantity

    @strawberry.field
    async def dish(self, info: Info) -> Dish:
        return await info.context.dish_loader.load(self.dish_id)


@strawberry.type
class Order:
    id: int
    customer_name: str
    delivery_address: str
    cancel_reason: Optional[str]

    @strawberry.field
    def total(self) -> float:
        return float(self.total)

    @strawberry.field
    def created_at(self) -> str:
        return self.created_at.isoformat()

    @strawberry.field
    async def status(self) -> OrderStatus:
        return OrderStatus(self.status)

    @strawberry.field
    async def restaurant(self, info: Info) -> Restaurant:
        return await info.context.restaurant_loader.load(self.restaurant_id)

    @strawberry.field
    async def items(self, info: Info) -> list[OrderItem]:
        return await info.context.items_loader.load(self.id)


# ---------- Входные типы ----------
@strawberry.input
class OrderItemInput:
    dish_id: int
    quantity: int


@strawberry.input
class CreateOrderInput:
    restaurant_id: int
    customer_name: str
    delivery_address: str
    items: list[OrderItemInput]


# ---------- Query ----------
@strawberry.type
class Query:
    @strawberry.field
    async def order(self, id: strawberry.ID) -> Optional[Order]:
        return await db.get_order(int(id))

    @strawberry.field
    async def orders(self, status: Optional[OrderStatus] = None) -> list[Order]:
        return await db.list_orders(status.value if status else None)

    @strawberry.field
    async def restaurants(self) -> list[Restaurant]:
        return await db.list_restaurants()


# ---------- Mutation ----------
@strawberry.type
class Mutation:
    @strawberry.mutation
    @_handle_errors
    async def create_order(self, input: CreateOrderInput) -> Order:
        items = [(it.dish_id, it.quantity) for it in input.items]
        return await services.create_order(
            restaurant_id=input.restaurant_id,
            customer_name=input.customer_name,
            delivery_address=input.delivery_address,
            items=items,
        )

    @strawberry.mutation
    @_handle_errors
    async def accept_order(self, id: strawberry.ID) -> Order:
        return await services.accept(int(id))

    @strawberry.mutation
    @_handle_errors
    async def mark_order_ready(self, id: strawberry.ID) -> Order:
        return await services.mark_ready(int(id))

    @strawberry.mutation
    @_handle_errors
    async def mark_order_delivered(self, id: strawberry.ID) -> Order:
        return await services.mark_delivered(int(id))

    @strawberry.mutation
    @_handle_errors
    async def cancel_order(self, id: strawberry.ID, reason: str) -> Order:
        return await services.cancel(int(id), reason)


# ---------- Subscription ----------
@strawberry.type
class Subscription:
    @strawberry.subscription
    async def order_status_changed(
        self, info: Info, order_id: strawberry.ID
    ) -> AsyncGenerator[Order, None]:
        oid = int(order_id)
        order = await db.get_order(oid)
        if order is None:
            raise GraphQLError(
                f"Заказ {oid} не найден",
                extensions={"code": "NOT_FOUND"},
            )

        queue = await events.subscribe(oid)
        try:
            yield order
            if order.status in ("DELIVERED", "CANCELLED"):
                return
            while True:
                event = await queue.get()
                order = await db.get_order(oid)
                if order is None:
                    break
                yield order
                if event.status in ("DELIVERED", "CANCELLED"):
                    break
        finally:
            await events.unsubscribe(oid, queue)


schema = strawberry.Schema(
    query=Query, mutation=Mutation, subscription=Subscription
)
