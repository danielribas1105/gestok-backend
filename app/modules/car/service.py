import uuid

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from app.modules.car.model import CapacityUnit, Car, CarCapacity
from app.modules.car.schema import (
    CarCreate,
    CarUpdate,
    CarCapacityUpdate,
)


def car_can_fit(car: Car, demand: dict[CapacityUnit, float]) -> bool:
    for cap in car.capacities:
        if cap.unit in demand and demand[cap.unit] > cap.value:
            return False
    return True


async def list_cars(offset: int = 0, limit: int = 20) -> list[Car]:
    result = await db.session.execute(
        select(Car)
        .options(selectinload(Car.driver), selectinload(Car.capacities))
        .offset(offset)
        .limit(limit)
        .order_by(Car.plate)
    )
    return result.scalars().all()


async def create_car(data: CarCreate) -> Car:
    payload = data.model_dump(exclude={"capacities"})
    car = Car(**payload)
    car.capacities = [
        CarCapacity(unit=cap.unit, value=cap.value) for cap in data.capacities
    ]
    db.session.add(car)
    try:
        await db.session.commit()
    except IntegrityError as e:
        await db.session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Placa já cadastrada, motorista já possui veículo vinculado, "
            "ou unidade de capacidade duplicada para o mesmo veículo.",
        ) from e
    return await get_car_by_id(car.id)


async def get_car_by_id(car_id: uuid.UUID) -> Car | None:
    result = await db.session.execute(
        select(Car)
        .options(selectinload(Car.driver), selectinload(Car.capacities))
        .where(Car.id == car_id)
    )
    return result.scalars().first()


def _apply_capacities_diff(car: Car, incoming: list[CarCapacityUpdate]) -> None:
    """Sincroniza car.capacities com a lista recebida no update.

    - item com id existente no carro -> atualiza unit/value
    - item com id inexistente no carro -> 400 (não deixa "adotar" capacidade de outro carro)
    - item sem id -> cria nova capacidade
    - capacidade existente cujo id não aparece na lista -> remove
    """
    existing_by_id: dict[uuid.UUID, CarCapacity] = {c.id: c for c in car.capacities}
    incoming_ids: set[uuid.UUID] = set()

    for item in incoming:
        if item.id is not None:
            cap = existing_by_id.get(item.id)
            if cap is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Capacidade {item.id} não pertence a este veículo.",
                )
            cap.unit = item.unit
            cap.value = item.value
            incoming_ids.add(item.id)
        else:
            car.capacities.append(CarCapacity(unit=item.unit, value=item.value))

    for cap_id, cap in existing_by_id.items():
        if cap_id not in incoming_ids:
            car.capacities.remove(cap)
            # com cascade="all, delete-orphan" na Relationship, remover da lista
            # já é suficiente para o SQLAlchemy gerar o DELETE no commit


async def update(car_id: uuid.UUID, data: CarUpdate) -> Car:
    car = await get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    update_data = data.model_dump(exclude_unset=True, exclude={"capacities"})
    for field, value in update_data.items():
        setattr(car, field, value)

    if data.capacities is not None:
        _apply_capacities_diff(car, data.capacities)

    try:
        await db.session.commit()
    except IntegrityError as e:
        await db.session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Placa já cadastrada, motorista já possui veículo vinculado, "
            "ou unidade de capacidade duplicada para o mesmo veículo.",
        ) from e
    return await get_car_by_id(car.id)


async def delete(car_id: uuid.UUID) -> None:
    car = await get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    await db.session.delete(car)
    await db.session.commit()
