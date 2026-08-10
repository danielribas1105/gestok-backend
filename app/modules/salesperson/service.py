import uuid

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy.future import select
from app.modules.salesperson.model import Salesperson
from app.modules.salesperson.schema import (
    SalespersonCreate,
    SalespersonUpdate,
)


async def list_salesperson(offset: int = 0, limit: int = 20) -> list[Salesperson]:
    result = await db.session.execute(
        select(Salesperson).offset(offset).limit(limit).order_by(Salesperson.name)
    )
    return result.scalars().all()


async def create_salesperson(data: SalespersonCreate) -> Salesperson:
    salesperson = Salesperson(**data.model_dump())
    db.session.add(salesperson)
    await db.session.commit()
    await db.session.refresh(salesperson)
    return salesperson


async def get_salesperson_by_id(salesperson_id: uuid.UUID) -> Salesperson | None:
    salesperson = await db.session.execute(
        select(Salesperson).where(Salesperson.id == salesperson_id)
    )
    return salesperson.scalars().first()


async def update(salesperson_id: uuid.UUID, data: SalespersonUpdate) -> Salesperson:
    salesperson = await get_salesperson_by_id(salesperson_id)
    if not salesperson:
        raise HTTPException(status_code=404, detail="Vendedor não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(salesperson, field, value)
    await db.session.commit()
    await db.session.refresh(salesperson)
    return salesperson


async def delete(salesperson_id: uuid.UUID) -> None:
    salesperson = await get_salesperson_by_id(salesperson_id)
    if not salesperson:
        raise HTTPException(status_code=404, detail="Vendedor não encontrado")
    await db.session.delete(salesperson)
    await db.session.commit()
