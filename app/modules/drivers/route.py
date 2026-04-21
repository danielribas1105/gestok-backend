import uuid

from fastapi import APIRouter, Depends, HTTPException
from app.modules.auth.service import get_current_user
from app.modules.drivers.model import Car
from app.modules.drivers.schema import CarCreate, CarResponse, CarUpdate
from app.modules.drivers import service
from app.modules.user.model import User

router = APIRouter(prefix="/cars", tags=["Cars"])


@router.get("", response_model=list[CarResponse])
async def list_cars(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_cars(offset, limit)


@router.post("", response_model=CarResponse, status_code=201)
async def create_car(car: CarCreate, user: User = Depends(get_current_user)):
    return await service.create_car(car)


@router.get("/{car_id}", response_model=CarResponse)
async def get_car(car_id: uuid.UUID, user: User = Depends(get_current_user)):
    car = await service.get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    return car


@router.put("/{car_id}", response_model=CarResponse)
async def update_car(
    car_id: uuid.UUID,
    data: CarUpdate,
    user: User = Depends(get_current_user),
):
    return await service.update(car_id, data)


@router.delete("/{car_id}", status_code=204)
async def delete_car(car_id: uuid.UUID, user: User = Depends(get_current_user)):
    await service.delete(car_id)


# Atualização parcial
""" @router.patch("/{car_id}/assign-driver", response_model=schema.CarResponse)
def assign_driver(id: str, driver_id: str, session: Session = Depends(get_db)):
    # Verifica se o carro existe
    car = session.get(Car, id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    # Verifica se o user existe
    user = session.get(User, driver_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Atualiza o motorista
    car.driver_id = driver_id
    session.add(car)
    session.commit()
    session.refresh(car)

    return car """
