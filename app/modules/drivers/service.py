import uuid

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import select
from app.modules.drivers.model import Driver
from app.modules.drivers.schema import DriverCreate, DriverUpdate


async def list_drivers(offset: int = 0, limit: int = 20) -> list[Driver]:
    result = await db.session.execute(select(Driver).offset(offset).limit(limit))
    drivers = result.scalars().all()
    return drivers


async def create_driver(data: DriverCreate) -> Driver:
    driver = Driver(**data.model_dump())
    db.session.add(driver)
    await db.session.commit()
    await db.session.refresh(driver)
    return driver


async def get_driver_by_id(driver_id: uuid.UUID) -> Driver | None:
    result = await db.session.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalars().first()

    return driver


async def update(driver_id: str, data: DriverUpdate) -> Driver:
    driver = await get_driver_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)
    await db.session.commit()
    await db.session.refresh(driver)
    return driver


async def delete(driver_id: str) -> None:
    driver = await get_driver_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")
    await db.session.delete(driver)
    await db.session.commit()
