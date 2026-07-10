import uuid

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from app.modules.car.model import Car
from app.modules.car.schema import CarCreate, CarUpdate
from app.modules.user.model import User


async def list_cars(offset: int = 0, limit: int = 20) -> list[Car]:
    result = await db.session.execute(
        select(Car)
        .options(selectinload(Car.driver).selectinload(User.driver_profile))
        .offset(offset)
        .limit(limit)
    )
    cars = result.scalars().all()
    return cars


async def create_car(data: CarCreate) -> Car:
    car = Car(**data.model_dump())
    db.session.add(car)
    try:
        await db.session.commit()
    except IntegrityError as e:
        await db.session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Placa já cadastrada ou motorista já possui veículo vinculado.",
        ) from e
    return await get_car_by_id(car.id)


async def get_car_by_id(car_id: uuid.UUID) -> Car | None:
    result = await db.session.execute(
        select(Car)
        .options(selectinload(Car.driver).selectinload(User.driver_profile))
        .where(Car.id == car_id)
    )
    return result.scalars().first()


async def update(car_id: uuid.UUID, data: CarUpdate) -> Car:
    car = await get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(car, field, value)
    await db.session.commit()
    return await get_car_by_id(car.id)


async def delete(car_id: uuid.UUID) -> None:
    car = await get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    await db.session.delete(car)
    await db.session.commit()
