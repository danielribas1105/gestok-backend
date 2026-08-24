import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from fastapi_async_sqlalchemy import db
from sqlmodel import Session, select

from app.modules.delivery.model import Delivery, DeliveryStatus
from app.modules.delivery.schema import DeliveryCreate, DeliveryRead, DeliveryUpdate
from app.modules.orders.model import Order, OrderStatus
from app.modules.car.model import Car


def _to_delivery_read(delivery: Delivery) -> DeliveryRead:
    return DeliveryRead(
        id=delivery.id,
        order_id=delivery.order_id,
        car_id=delivery.car_id,
        user_id=delivery.user_id,
        weight=delivery.weight,
        invoice=delivery.invoice,
        status=delivery.status,
        observations=delivery.observations,
        created_at=delivery.created_at,
        departed_at=delivery.departed_at,
        delivery_at=delivery.delivery_at,
        delivery_confirmed=delivery.delivery_confirmed,
        car=f"{delivery.car.plate} - {delivery.car.model}" if delivery.car else None,
        driver=(
            delivery.car.driver.name if delivery.car and delivery.car.driver else None
        ),
        user=delivery.user.name if delivery.user else None,
        order_code=delivery.order.code if delivery.order else None,
    )


async def list_delivery(offset: int = 0, limit: int = 20) -> list[DeliveryRead]:
    result = await db.session.execute(
        select(Delivery)
        .options(
            selectinload(Delivery.car).selectinload(Car.driver),
            selectinload(Delivery.user),
            selectinload(Delivery.order),
        )
        .offset(offset)
        .limit(limit)
    )
    deliveries = result.scalars().all()
    return [_to_delivery_read(d) for d in deliveries]


async def create_delivery(data: list[DeliveryCreate]) -> list[DeliveryRead]:
    deliveries = [Delivery(**item.model_dump()) for item in data]
    db.session.add_all(deliveries)
    await db.session.commit()

    ids = [d.id for d in deliveries]

    result = await db.session.execute(
        select(Delivery)
        .options(
            selectinload(Delivery.car).selectinload(Car.driver),
            selectinload(Delivery.user),
            selectinload(Delivery.order),
        )
        .where(Delivery.id.in_(ids))
    )
    created = result.scalars().all()

    return [_to_delivery_read(d) for d in created]


def get_delivery(session: Session, delivery_id: uuid.UUID) -> Delivery:
    delivery = session.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega não encontrada")
    return delivery


def update_delivery(
    session: Session, delivery_id: uuid.UUID, data: DeliveryUpdate
) -> Delivery:
    delivery = get_delivery(session, delivery_id)
    update_data = data.model_dump(exclude_unset=True)

    # Se o carro for trocado, o motorista é re-derivado junto
    if "car_id" in update_data:
        car = session.get(Car, update_data["car_id"])
        if not car:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Carro não encontrado")
        if not car.driver_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Este carro não possui motorista vinculado",
            )
        delivery.driver_id = car.driver_id

    for key, value in update_data.items():
        setattr(delivery, key, value)

    session.add(delivery)
    session.commit()
    session.refresh(delivery)
    return delivery


def confirm_delivery(session: Session, delivery_id: uuid.UUID) -> Delivery:
    delivery = get_delivery(session, delivery_id)

    if delivery.status == DeliveryStatus.CONFIRMED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Entrega já confirmada")

    delivery.confirmed_by_driver = True
    delivery.confirmed_at = datetime.now(timezone.utc)
    delivery.status = DeliveryStatus.CONFIRMED
    session.add(delivery)

    order = session.get(Order, delivery.order_id)
    if order:
        order.status = OrderStatus.CONCLUDED
        session.add(order)

    session.commit()
    session.refresh(delivery)
    return delivery
