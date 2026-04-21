import uuid

from fastapi import APIRouter, Depends, HTTPException
from app.modules.auth.service import get_current_user
from app.modules.products.schema import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.modules.products import service
from app.modules.user.model import User

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_products(offset, limit)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate, user: User = Depends(get_current_user)
):
    return await service.create_product(product)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID, user: User = Depends(get_current_user)):
    product = await service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    user: User = Depends(get_current_user),
):
    return await service.update(product_id, data)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: uuid.UUID, user: User = Depends(get_current_user)
):
    await service.delete(product_id)
