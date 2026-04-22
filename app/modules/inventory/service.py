from fastapi_async_sqlalchemy import db
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.inventory.model import Inventory
from app.modules.orders.model import Order


async def list_inventory(offset: int = 0, limit: int = 20) -> list[Inventory]:
    result = await db.session.execute(select(Inventory).offset(offset).limit(limit))
    inventory = result.scalars().all()
    return inventory
