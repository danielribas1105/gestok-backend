from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.inventory.model import Inventory
from app.modules.orders.model import Order


async def get_inventory_paginated(
   db: AsyncSession,
   page: int = 1,
   page_size: int = 20,
   search: str | None = None
):
   query = select(Inventory)
   count_query = select(func.count()).select_from(Inventory)

   if search:
      search_filter = or_(
         Inventory.id.ilike(f"%{search}%"),  # type: ignore
         Inventory.product_id.ilike(f"%{search}%")  # type: ignore
      )
      query = query.where(search_filter)
      count_query = count_query.where(search_filter)

   query = query.order_by(func.lower(Inventory.product_id))
   total = await db.scalar(count_query) or 0

   offset = (page - 1) * page_size
   result = await db.execute(query.offset(offset).limit(page_size))
   inventory = result.scalars().all()

   return {
      "inventory": inventory,
      "total": total,
      "page": page,
      "page_size": page_size,
      "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
   }