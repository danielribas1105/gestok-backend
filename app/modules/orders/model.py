from datetime import datetime
import enum
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import Column, DateTime, String, func, text
from sqlmodel import Relationship, SQLModel, Field


if TYPE_CHECKING:
    from app.modules.inventory.model import StockMovement
    from app.modules.car.model import Car
    from app.modules.clients.model import Client
    from app.modules.user.model import User
    from app.modules.products.model import Product


class OrderType(str, enum.Enum):
    IN = "in"
    OUT = "out"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    CANCELED = "canceled"
    INTRANSIT = "in_transit"
    CONCLUDED = "concluded"


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    order_id: uuid.UUID = Field(foreign_key="orders.id", nullable=False, index=True)
    product_id: uuid.UUID = Field(foreign_key="products.id", nullable=False, index=True)
    quantity: int = Field(nullable=False)
    total_price: float = Field(nullable=False)

    # Relationship
    order: Optional["Order"] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship(back_populates="order_items")


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    code: str = Field(sa_column_kwargs={"unique": True, "index": True})
    client_id: uuid.UUID = Field(foreign_key="clients.id", nullable=False, index=True)
    car_id: uuid.UUID = Field(foreign_key="cars.id", nullable=False, index=True)
    created_by: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    observations: Optional[str] = Field(default=None)
    type: OrderType = Field(
        default=OrderType.OUT,
        sa_column=Column(
            String(10),
            nullable=False,
            server_default=OrderType.OUT.value,
        ),
    )
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        sa_column=Column(
            String(50),
            nullable=False,
            server_default=OrderStatus.PENDING.value,
        ),
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
    )

    # Relationship
    car: Optional["Car"] = Relationship(back_populates="car_orders")
    items: List["OrderItem"] = Relationship(back_populates="order")
    stock_movements: List["StockMovement"] = Relationship(back_populates="order")
    client: Optional["Client"] = Relationship(
        back_populates="client_orders",
        sa_relationship_kwargs={"foreign_keys": "[Order.client_id]"},
    )
    creator: Optional["User"] = Relationship(
        back_populates="created_orders",
        sa_relationship_kwargs={"foreign_keys": "[Order.created_by]"},
    )
