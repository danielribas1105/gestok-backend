import uuid

from fastapi import APIRouter, Depends, HTTPException
from app.modules.auth.service import get_current_user
from app.modules.drivers.schema import DriverCreate, DriverRead, DriverUpdate
from app.modules.drivers import service
from app.modules.user.model import User

router = APIRouter(prefix="/drivers", tags=["Drivers"])


# 1. Static routes
@router.get("", response_model=list[DriverRead])
async def list_drivers(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_drivers(offset, limit)


# 2. Root routes
@router.post("", response_model=DriverRead, status_code=201)
async def create_driver(driver: DriverCreate, user: User = Depends(get_current_user)):
    return await service.create_driver(driver)


# 3. Routes with dynamic parameters
@router.get("/{driver_id}", response_model=DriverRead)
async def get_driver_by_id(
    driver_id: uuid.UUID, user: User = Depends(get_current_user)
):
    driver = await service.get_driver_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")
    return driver


@router.put("/{driver_id}", response_model=DriverRead)
async def update_driver(
    driver_id: uuid.UUID,
    data: DriverUpdate,
    user: User = Depends(get_current_user),
):
    """
    Update drivers
    """
    return await service.update_driver(driver_id, data)


@router.delete("/{driver_id}", status_code=204)
async def delete_driver(driver_id: uuid.UUID, user: User = Depends(get_current_user)):
    await service.delete_driver(driver_id)
