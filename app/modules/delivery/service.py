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
from app.modules.inventory.model import Inventory, StockMovement, MovementType


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


async def _apply_stock_movements_for_delivery(delivery: Delivery, order: Order) -> None:
    """
    Registra as saídas (OUT) em stock_movements, atualiza o inventário
    (estoque real e reservado) e trava o pedido como PROCESSED — a partir
    daqui ele não pode mais ser colocado em hold nem selecionado numa
    nova checagem/entrega.

    IMPORTANTE: só deve ser chamada depois que a Delivery já foi criada/persistida.
    """
    if order.stock_hold:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Pedido {order.code} está em hold e não pode gerar saída de estoque",
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Pedido {order.code} não está pendente (status atual: {order.status}) "
            "e não pode gerar uma nova entrega",
        )

    if not order.items:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Pedido {order.code} não possui itens para gerar saída de estoque",
        )

    for item in order.items:
        result = await db.session.execute(
            select(Inventory)
            .where(Inventory.product_id == item.product_id)
            .with_for_update()
        )
        inventory = result.scalar_one_or_none()

        if not inventory:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"Inventário não encontrado para o produto {item.product_id}",
            )

        if inventory.available_quantity < item.quantity:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Reserva insuficiente para o produto {item.product_id}: "
                f"reservado={inventory.reserved_quantity}, solicitado={item.quantity}",
            )

        inventory.current_quantity -= item.quantity
        inventory.reserved_quantity -= item.quantity
        inventory.available_quantity = (
            inventory.current_quantity - inventory.reserved_quantity
        )
        inventory.last_updated = datetime.now(timezone.utc)
        db.session.add(inventory)

        movement = StockMovement(
            product_id=item.product_id,
            order_id=order.id,
            code=order.code,
            user_id=delivery.user_id,
            movement_type=MovementType.OUT,
            quantity=item.quantity,
            movement_date=datetime.now(timezone.utc),
            observations=f"Saída de estoque referente à entrega {delivery.id}",
        )
        db.session.add(movement)

    # Pedido processado: sai da fila de pendentes, não pode mais ser
    # colocado em hold nem selecionado numa nova checagem de estoque/entrega
    order.status = OrderStatus.PROCESSED
    order.processed_at = datetime.now(timezone.utc)
    db.session.add(order)


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
    # 1. Cria as deliveries primeiro — a baixa de estoque depende delas existirem
    deliveries = [Delivery(**item.model_dump()) for item in data]
    db.session.add_all(deliveries)
    # await db.session.commit()
    await db.session.flush()  # ainda dentro da mesma transação, reversível

    ids = [d.id for d in deliveries]

    result = await db.session.execute(
        select(Delivery)
        .options(
            selectinload(Delivery.car).selectinload(Car.driver),
            selectinload(Delivery.user),
            selectinload(Delivery.order).selectinload(Order.items),
        )
        .where(Delivery.id.in_(ids))
    )
    created = result.scalars().all()

    # 2. Só agora, com as deliveries já persistidas, aplica a baixa de
    # estoque e trava o(s) pedido(s) como PROCESSED
    try:
        for delivery in created:
            if not delivery.order:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Entrega {delivery.id} não possui pedido vinculado",
                )
            await _apply_stock_movements_for_delivery(delivery, delivery.order)

        await db.session.commit()
    except HTTPException:
        await db.session.rollback()
        raise

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
