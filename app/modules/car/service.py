import uuid

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import select
from app.modules.car.model import Car
from app.modules.car.schema import CarCreate, CarUpdate


async def list_cars(offset: int = 0, limit: int = 20) -> list[Car]:
    result = await db.session.execute(select(Car).offset(offset).limit(limit))
    cars = result.scalars().all()
    print(f"Cars {cars}")
    return cars


async def create_car(data: CarCreate) -> Car:
    car = Car(**data.model_dump())
    db.session.add(car)
    await db.session.commit()
    await db.session.refresh(car)
    return car


async def get_car_by_id(car_id: uuid.UUID) -> Car | None:
    result = await db.session.execute(select(Car).where(Car.id == car_id))
    car = result.scalars().first()

    return car


async def update(car_id: str, data: CarUpdate) -> Car:
    car = await get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(car, field, value)
    await db.session.commit()
    await db.session.refresh(car)
    return car


async def delete(car_id: str) -> None:
    car = await get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    await db.session.delete(car)
    await db.session.commit()
