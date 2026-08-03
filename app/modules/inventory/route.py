from fastapi import APIRouter, Depends
from app.modules.auth.service import get_current_user
from app.modules.inventory.schema import (
    InventoryCreate,
    InventoryRead,
    InventoryUpdate,
)
from app.modules.inventory import service
from app.modules.user.model import User

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=list[InventoryRead])
async def list_inventory(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_inventory(offset, limit)
