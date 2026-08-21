import uuid
from fastapi import APIRouter, Body, Depends, HTTPException, status
from app.modules.auth.service import get_current_user, require_roles
from app.modules.orders.model import OrderOperationType, OrderStatus
from app.modules.user.model import User
from app.modules.orders.schema import (
    OrderBatchResponse,
    OrderCreatePayload,
    OrderItemReadNested,
    OrderItemStockStatus,
    OrderResponse,
    OrderStockHoldUpdate,
    OrderUpdate,
    ProductsQuantityCheckRequest,
    ProductsQuantityCheckResponse,
)
from app.modules.orders import service

router = APIRouter(prefix="/orders", tags=["Orders"])


def _to_response_orders(
    order, item_status_map: dict[uuid.UUID, OrderItemStockStatus] | None = None
) -> OrderResponse:
    item_status_map = item_status_map or {}
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
            product_volume=item.product.volume_m3_per_unit if item.product else None,
            product_boxes_pallet=(
                item.product.boxes_per_pallet if item.product else None
            ),
            quantity=item.quantity,
            total_price=item.total_price,
            name=item.product.name if item.product else None,
            name_code=item.product.name_code if item.product else None,
            stock_item_status=item_status_map.get(item.id),
        )
        for item in order.items
    ]

    order_stock_status = service.aggregate_order_stock_status(
        order,
        [s for item in order.items if (s := item_status_map.get(item.id)) is not None],
    )

    return OrderResponse(
        **data,
        items=items,
        stock_status=order_stock_status,
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
    item_status_map = await service.get_pending_orders_item_stock_status()
    return [_to_response_orders(order, item_status_map) for order in orders]


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


@router.post(
    "/products-quantity-check",
    response_model=ProductsQuantityCheckResponse,
)
async def products_quantity_check(
    payload: ProductsQuantityCheckRequest,
    user: User = Depends(get_current_user),
):
    items = await service.get_products_quantity_check(payload.item_ids)
    return ProductsQuantityCheckResponse(
        items=items,
        all_sufficient=all(item.is_sufficient for item in items),
    )


@router.patch("/{order_id}/stock-hold", response_model=OrderResponse)
async def set_order_stock_hold(
    order_id: uuid.UUID,
    payload: OrderStockHoldUpdate,
    user: User = Depends(require_roles("admin", "operator")),
):
    order = await service.set_order_stock_hold(
        order_id, payload.stock_hold, payload.reason
    )
    # recalcula o status pra devolver já atualizado (afeta outros pedidos também,
    # mas a resposta aqui é só do pedido alterado — o front deve invalidar a lista)
    return await get_order(order_id, user)


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
