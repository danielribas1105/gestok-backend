from datetime import datetime

from fastapi import Depends
from fastapi_async_sqlalchemy import db
from sqlalchemy import select
from sqlalchemy.orm import contains_eager, selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.modules.auth.service import get_current_user
from app.modules.inventory.model import Inventory, MovementType, StockMovement
from app.modules.inventory.schema import InventoryUpdateBatch
from app.modules.products.model import Product
from app.modules.user.model import User


async def list_inventory(offset: int = 0, limit: int = 20) -> list[Inventory]:
    result = await db.session.execute(
        select(Inventory)
        .join(Inventory.product)
        .options(contains_eager(Inventory.product))
        .order_by(Product.name)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def _apply_stock_movement(item: InventoryUpdateBatch, user: User) -> Inventory:
    """Cria o StockMovement e ajusta o saldo de Inventory para um item do lote.
    Não faz commit — a transação é controlada por quem chama."""

    result = await db.session.execute(
        select(Inventory)
        .where(Inventory.product_id == item.product_id)
        .with_for_update()
    )
    inventory = result.scalar_one_or_none()

    if inventory is None:
        inventory = Inventory(product_id=item.product_id)
        db.session.add(inventory)
        await db.session.flush()  # garante defaults/id antes de usar

    delta = item.quantity if item.movement_type == MovementType.IN else -item.quantity

    if (
        item.movement_type == MovementType.OUT
        and inventory.current_quantity + delta < 0
    ):
        raise ValueError(
            f"Saldo insuficiente para o produto {item.product_id}: "
            f"disponível {inventory.current_quantity}, solicitado {item.quantity}"
        )

    movement = StockMovement(
        product_id=item.product_id,
        order_id=item.order_id,
        code=item.code,
        user_id=user.id,
        movement_type=item.movement_type,
        quantity=item.quantity,
        observations=item.observations,
    )
    db.session.add(movement)

    inventory.current_quantity += delta
    inventory.available_quantity = (
        inventory.current_quantity - inventory.reserved_quantity
    )
    inventory.last_updated = datetime.utcnow()

    return inventory


async def update_inventory_batch(
    items: list[InventoryUpdateBatch],
    user: User,
) -> tuple[list[Inventory], list[dict]]:
    created: list[Inventory] = []
    failed: list[dict] = []

    for item in items:
        try:
            async with db.session.begin_nested():  # savepoint isolado por item
                inventory = await _apply_stock_movement(item, user)
            created.append(inventory)
        except (SQLAlchemyError, ValueError) as exc:
            # begin_nested já reverteu o savepoint deste item ao sair por exceção
            failed.append({"product_id": str(item.product_id), "error": str(exc)})

    await db.session.commit()

    # garante `product` carregado para TODOS os itens de `created`,
    # independente de terem sido criados ou apenas atualizados acima
    if created:
        result = await db.session.execute(
            select(Inventory)
            .where(Inventory.id.in_([inv.id for inv in created]))
            .options(selectinload(Inventory.product))
        )
        created = result.scalars().all()

    return created, failed
