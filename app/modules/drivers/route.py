from fastapi import APIRouter, Depends
from app.modules.auth.service import get_current_user
from app.modules.drivers.schema import DriverRead
from app.modules.car import service
from app.modules.user.model import User

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", response_model=list[DriverRead])
async def list_drivers(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_drivers(offset, limit)
