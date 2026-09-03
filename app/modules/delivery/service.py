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
        scheduled_at=delivery.scheduled_at,
        departed_at=delivery.departed_at,
        delivered_at=delivery.delivered_at,
        delivered_confirmed=delivery.delivered_confirmed,
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


async def _conclude_order_for_delivery(delivery: Delivery) -> None:
    """
    Ao concluir a entrega, fecha o pedido como CONCLUDED.
    NÃO dá baixa de estoque de novo — isso já aconteceu na criação
    da entrega (_apply_stock_movements_for_delivery), quando o pedido
    foi travado como PROCESSED.
    """
    order = delivery.order
    if not order:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Entrega {delivery.id} não possui pedido vinculado",
        )

    # Idempotência: se o pedido já está concluído, não faz nada
    if order.status == OrderStatus.CONCLUDED:
        return

    # Guard essencial: só pode concluir se o pedido já passou pela
    # baixa de estoque (PROCESSED). Se estiver PENDING (ou outro
    # status), algo está fora de ordem — bloqueia.
    if order.status != OrderStatus.PROCESSED:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Pedido {order.code} não está processado (status atual: {order.status}); "
            "não é possível concluir a entrega sem a baixa de estoque já ter sido feita",
        )

    order.status = OrderStatus.CONCLUDED
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


async def get_delivery_by_id(delivery_id: uuid.UUID) -> DeliveryRead:
    result = await db.session.execute(
        select(Delivery)
        .options(
            selectinload(Delivery.car).selectinload(Car.driver),
            selectinload(Delivery.user),
            selectinload(Delivery.order),
        )
        .where(Delivery.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega não encontrada")
    return _to_delivery_read(delivery)


async def update_delivery(delivery_id: uuid.UUID, data: DeliveryUpdate) -> DeliveryRead:
    result = await db.session.execute(
        select(Delivery)
        .options(
            selectinload(Delivery.car).selectinload(Car.driver),
            selectinload(Delivery.user),
            selectinload(Delivery.order),
        )
        .where(Delivery.id == delivery_id)
        .with_for_update()  # trava a linha contra updates concorrentes na mesma entrega
    )
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega não encontrada")

    update_data = data.model_dump(exclude_unset=True)
    new_status = update_data.get("status")

    # Transições relevantes
    is_departing = (
        new_status == DeliveryStatus.IN_TRANSIT
        and delivery.status != DeliveryStatus.IN_TRANSIT
    )
    # Só dispara a conclusão do pedido se o status está de fato
    # MUDANDO para CONCLUDED (evita reprocessar em updates repetidos)
    is_concluding = (
        new_status == DeliveryStatus.CONCLUDED
        and delivery.status != DeliveryStatus.CONCLUDED
    )

    for field, value in update_data.items():
        setattr(delivery, field, value)

    # Ao sair para trânsito pela primeira vez, registra departed_at
    # automaticamente no servidor (sobrescreve qualquer valor vindo
    # do client, para evitar inconsistência de horário/fuso)
    if delivery.departed_at is None:
        delivery.departed_at = datetime.now(timezone.utc)

    if is_concluding:
        delivery.delivered_at = datetime.now(timezone.utc)

    db.session.add(delivery)

    try:
        if is_concluding:
            await _conclude_order_for_delivery(delivery)

        await db.session.commit()  # ← um único commit, no final, com tudo validado
    except HTTPException:
        await db.session.rollback()
        raise

    await db.session.refresh(delivery, attribute_names=["car", "user", "order"])
    return _to_delivery_read(delivery)


""" async def confirm_delivery(session: Session, delivery_id: uuid.UUID) -> Delivery:
    delivery = get_delivery_by_id(delivery_id)

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
    return delivery """
