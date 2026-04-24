from datetime import datetime
import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Column, DateTime, func, text
from sqlmodel import Relationship, SQLModel, Field


if TYPE_CHECKING:
    from app.modules.orders.model import OrderItem
    from app.modules.inventory.model import Inventory, StockMovement


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    code: str = Field(sa_column_kwargs={"unique": True, "index": True})
    description: Optional[str] = Field(default=None)
    unit: str = Field(nullable=False)
    value: float = Field(nullable=False)
    active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    image: Optional[str] = Field(default=None, nullable=True)

    # Relationship
    order_items: List["OrderItem"] = Relationship(back_populates="product")
    inventory: Optional["Inventory"] = Relationship(back_populates="product")
    stock_movements: List["StockMovement"] = Relationship(back_populates="product")
