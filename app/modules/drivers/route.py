import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.modules.auth.service import get_current_user
from app.modules.drivers.schema import DriverCreate, DriverResponse, DriverUpdate
from app.modules.drivers import service
from app.modules.user.model import User

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", response_model=list[DriverResponse])
async def list_drivers(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_drivers(offset, limit)


@router.post("", response_model=DriverResponse, status_code=201)
async def create_driver(driver: DriverCreate, user: User = Depends(get_current_user)):
    return await service.create_driver(driver)


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: uuid.UUID, user: User = Depends(get_current_user)):
    driver = await service.get_driver_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")
    return driver


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: uuid.UUID,
    data: DriverUpdate,
    user: User = Depends(get_current_user),
):
    return await service.update(driver_id, data)


@router.delete("/{driver_id}", status_code=204)
async def delete_driver(driver_id: uuid.UUID, user: User = Depends(get_current_user)):
    await service.delete(driver_id)


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
