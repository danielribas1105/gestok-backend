import uuid

from fastapi import APIRouter, Depends, HTTPException
from app.modules.auth.service import get_current_user
from app.modules.car.schema import CarCreate, CarRead, CarUpdate
from app.modules.car import service
from app.modules.user.model import User

router = APIRouter(prefix="/cars", tags=["Cars"])


@router.get("", response_model=list[CarRead])
async def list_cars(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_cars(offset, limit)


@router.post("", response_model=CarRead, status_code=201)
async def create_car(car: CarCreate, user: User = Depends(get_current_user)):
    return await service.create_car(car)


@router.get("/{car_id}", response_model=CarRead)
async def get_car(car_id: uuid.UUID, user: User = Depends(get_current_user)):
    car = await service.get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    return car


@router.put("/{car_id}", response_model=CarRead)
async def update_car(
    car_id: uuid.UUID,
    data: CarUpdate,
    user: User = Depends(get_current_user),
):
    return await service.update(car_id, data)


@router.delete("/{car_id}", status_code=204)
async def delete_car(car_id: uuid.UUID, user: User = Depends(get_current_user)):
    await service.delete(car_id)
