import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import text
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
    name: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    value: float = Field(nullable=False)

    # Relationship
    order_items: List["OrderItem"] = Relationship(back_populates="product")
    inventory: Optional["Inventory"] = Relationship(back_populates="product")
    stock_movements: List["StockMovement"] = Relationship(back_populates="product")
