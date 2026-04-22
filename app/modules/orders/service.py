from datetime import datetime, timezone
import uuid
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from app.modules.orders.model import Order
from app.modules.orders.schema import OrderCreate, OrderUpdate


async def list_orders(offset: int = 0, limit: int = 20) -> list[Order]:
    result = await db.session.execute(select(Order).offset(offset).limit(limit))
    return result.scalars().all()


async def create_order(data: OrderCreate) -> Order:
    order = Order(
        **data.model_dump(exclude_none=True),
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(order)
    await db.session.commit()
    await db.session.refresh(order)
    return order


async def get_order_by_id(order_id: uuid.UUID) -> Order:
    result = await db.session.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()

    return order


async def update(order_id: uuid.UUID, data: OrderUpdate) -> Order:
    order = await get_order_by_id(order_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    order.updated_at = datetime.now(timezone.utc)
    await db.session.commit()
    await db.session.refresh(order)
    return order


async def delete(order_id: uuid.UUID) -> None:
    order = await get_order_by_id(order_id)
    await db.session.delete(order)
    await db.session.commit()
