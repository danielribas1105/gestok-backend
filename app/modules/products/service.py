import uuid

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import select
from app.modules.products.model import Product
from app.modules.products.schema import ProductCreate, ProductUpdate


async def list_products(offset: int = 0, limit: int = 20) -> list[Product]:
    result = await db.session.execute(select(Product).offset(offset).limit(limit))
    return result.scalars().all()


async def create_product(data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.session.add(product)
    await db.session.commit()
    await db.session.refresh(product)
    return product


async def get_product_by_id(product_id: uuid.UUID) -> Product | None:
    result = await db.session.execute(
        select(Product).where(Product.id == product_id)
    )
    return result.scalars().first()


async def update(product_id: uuid.UUID, data: ProductUpdate) -> Product:
    product = await get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.session.commit()
    await db.session.refresh(product)
    return product


async def delete(product_id: uuid.UUID) -> None:
    product = await get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product não encontrado")
    await db.session.delete(product)
    await db.session.commit()
