import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.modules.auth.service import get_current_user
from app.modules.user.model import User
from app.modules.orders.schema import (
    OrderCreate,
    OrderResponse,
    OrderUpdate,
)
from app.modules.orders import service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_orders(offset, limit)


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderCreate, user: User = Depends(get_current_user)):
    return await service.create_order(order)


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
