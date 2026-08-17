import uuid
from fastapi import APIRouter, Body, Depends, HTTPException
from app.modules.auth.service import get_current_user
from app.modules.orders.model import OrderOperationType, OrderStatus
from app.modules.user.model import User
from app.modules.orders.schema import (
    OrderBatchResponse,
    OrderCreatePayload,
    OrderItemReadNested,
    OrderResponse,
    OrderUpdate,
)
from app.modules.orders import service

router = APIRouter(prefix="/orders", tags=["Orders"])


def _to_response_orders(order) -> OrderResponse:
    """Monta o OrderResponse resolvendo os nomes a partir das relações de Order."""
    data = order.model_dump(exclude={"operation_type", "status", "items"})
    data["operation_type"] = OrderOperationType(order.operation_type)
    data["status"] = OrderStatus(order.status)

    items = [
        OrderItemReadNested(
            id=item.id,
            item_number=item.item_number,
            product_id=item.product_id,
            product_name_code=item.product.name_code if item.product else None,
            product_name=item.product.name if item.product else None,
            product_code=item.product.code if item.product else None,
            product_unit=item.product.unit if item.product else None,
            product_weight=item.product.weight_kg_per_unit if item.product else None,
            quantity=item.quantity,
            total_price=item.total_price,
            name=item.product.name if item.product else None,
            name_code=item.product.name_code if item.product else None,
        )
        for item in order.items
    ]

    return OrderResponse(
        **data,
        items=items,
        client_name=order.client.name if order.client else None,
        store_name=order.store.trade_name if order.store else None,
        saller_name=order.saller.name if order.saller else None,
        supervisor_name=order.supervisor.name if order.supervisor else None,
        manager_name=order.manager.name if order.manager else None,
    )


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    orders = await service.list_orders(offset, limit)
    return [_to_response_orders(order) for order in orders]


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    order: OrderCreatePayload, user: User = Depends(get_current_user)
):
    return await service.create_order(order)


@router.post("/batch", response_model=OrderBatchResponse, status_code=201)
async def create_orders_batch(
    orders: list[OrderCreatePayload] = Body(..., embed=True),
    user: User = Depends(get_current_user),
):
    created, failed = await service.create_orders_batch(orders)
    return OrderBatchResponse(created=created, failed=failed)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: uuid.UUID, user: User = Depends(get_current_user)):
    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: uuid.UUID,
    data: OrderUpdate,
    user: User = Depends(get_current_user),
):
    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return await service.update(order_id, data)


@router.delete("/{order_id}", status_code=204)
async def delete_order(order_id: uuid.UUID, user: User = Depends(get_current_user)):
    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    await service.delete(order_id)
