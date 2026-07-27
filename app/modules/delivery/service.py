import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from fastapi_async_sqlalchemy import db
from sqlmodel import Session, select

from app.modules.delivery.model import Delivery, DeliveryStatus
from app.modules.delivery.schema import DeliveryCreate, DeliveryUpdate
from app.modules.orders.model import Order, OrderStatus
from app.modules.car.model import Car


async def list_deliveries(offset: int = 0, limit: int = 20) -> list[Delivery]:
    result = await db.session.execute(select(Delivery).offset(offset).limit(limit))
    return result.scalars().all()


def create_delivery(session: Session, data: DeliveryCreate) -> Delivery:
    order = session.get(Order, data.order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido não encontrado")

    car = session.get(Car, data.car_id)
    if not car:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carro não encontrado")

    if not car.driver_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Este carro não possui motorista vinculado",
        )

    existing = session.exec(
        select(Delivery).where(Delivery.order_id == data.order_id)
    ).first()
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Este pedido já possui uma entrega atribuída"
        )

    delivery = Delivery(
        order_id=data.order_id,
        car_id=data.car_id,
        driver_id=car.driver_id,  # derivado do carro
        status=DeliveryStatus.PENDING,
    )
    session.add(delivery)

    order.status = OrderStatus.INTRANSIT
    session.add(order)

    session.commit()
    session.refresh(delivery)
    return delivery


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
