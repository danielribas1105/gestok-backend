from fastapi import APIRouter, Body, Depends
from app.modules.auth.service import get_current_user
from app.modules.inventory.schema import (
    InventoryBatchRead,
    InventoryRead,
    InventoryUpdateBatch,
)
from app.modules.inventory import service
from app.modules.user.model import User

router = APIRouter(prefix="/inventory", tags=["Inventory"])


def _to_response_inventory(item) -> InventoryRead:
    """Monta o InventoryResponse resolvendo os nomes a partir das relações de Inventory."""
    data = item.model_dump()

    return InventoryRead(
        **data,
        product_code=item.product.code if item.product else None,
        product_name=item.product.name if item.product else None,
    )


@router.get("", response_model=list[InventoryRead])
async def list_inventory(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    inventory = await service.list_inventory(offset, limit)
    return [_to_response_inventory(item) for item in inventory]


@router.post("/batch", response_model=InventoryBatchRead, status_code=201)
async def update_inventory_batch(
    inventory: list[InventoryUpdateBatch] = Body(..., embed=True),
    user: User = Depends(get_current_user),
):
    created, failed = await service.update_inventory_batch(inventory)
    return InventoryBatchRead(created=created, failed=failed)
