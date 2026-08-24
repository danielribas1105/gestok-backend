import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, String, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.orders.model import Order
    from app.modules.products.model import Product
    from app.modules.user.model import User


class MovementType(str, enum.Enum):
    IN = "in"
    OUT = "out"


class Inventory(SQLModel, table=True):
    __tablename__ = "inventory"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    product_id: uuid.UUID = Field(foreign_key="products.id", unique=True)
    current_quantity: float = Field(default=0.0)
    reserved_quantity: float = Field(default=0.0)
    available_quantity: float = Field(default=0.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    product: Optional["Product"] = Relationship(back_populates="inventory")


class StockMovement(SQLModel, table=True):
    __tablename__ = "stock_movements"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    product_id: uuid.UUID = Field(foreign_key="products.id")

    # referência real, só usada em saídas (OUT)
    order_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="orders.id", nullable=True, index=True
    )
    # código de exibição/auditoria: romaneio (IN) ou cópia do PEDIDO (OUT)
    code: str = Field(index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=True, index=True)

    movement_type: MovementType = Field(
        default=MovementType.OUT,
        sa_column=Column(
            String(10),
            nullable=False,
            server_default=MovementType.OUT.value,
        ),
    )
    quantity: int = Field()
    movement_date: datetime = Field(default_factory=datetime.utcnow)
    observations: Optional[str] = Field(default=None)

    # Relationship
    product: Optional["Product"] = Relationship(back_populates="stock_movements")
    order: Optional["Order"] = Relationship(back_populates="stock_movements")
    user: Optional["User"] = Relationship(back_populates="stock_movements")
