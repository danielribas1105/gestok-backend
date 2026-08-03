from datetime import datetime
import enum
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import Column, DateTime, String, func, text
from sqlmodel import Relationship, SQLModel, Field, UniqueConstraint

if TYPE_CHECKING:
    from app.modules.delivery.model import Delivery
    from app.modules.inventory.model import StockMovement
    from app.modules.salesperson.model import Salesperson
    from app.modules.clients.model import Store, Client
    from app.modules.products.model import Product


class OrderOperationType(str, enum.Enum):
    SALE = "sale"
    TASTING = "tasting"
    BONUS = "bonus"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    BLOCKED = "blocked"
    IN_TRANSIT = "in_transit"
    CANCELED = "canceled"
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
    item_number: Optional[str] = Field(
        default=None
    )  # ITEM da planilha, mantém a ordem original
    quantity: int = Field(nullable=False)
    total_price: float = Field(nullable=False)
    row_hash: str = Field(sa_column_kwargs={"unique": True, "index": True})

    # Relationship
    order: Optional["Order"] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship(back_populates="order_items")


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("branch_code", "code", name="uq_orders_branch_code"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    branch_code: str = Field(index=True)  # FILIAL
    code: str = Field(index=True)  # PEDIDO
    issued_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )  # EMISSÃO PEDIDO — data de origem no ERP, distinta de created_at (data do INSERT)
    operation_type: OrderOperationType = Field(
        default=OrderOperationType.SALE,
        sa_column=Column(
            String(10),
            nullable=False,
            server_default=OrderOperationType.SALE.value,
        ),
    )
    release_reason: Optional[str] = Field(default=None)  # MOTIVO DE LIBERAÇÃO
    released_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )  # combina DT + HR LIBERAÇÃO em um único timestamp com timezone

    client_id: uuid.UUID = Field(foreign_key="clients.id", nullable=False, index=True)
    store_id: uuid.UUID = Field(foreign_key="stores.id", nullable=False, index=True)
    saller_id: uuid.UUID = Field(
        foreign_key="salesperson.id", nullable=False, index=True
    )
    supervisor_id: uuid.UUID = Field(
        foreign_key="salesperson.id", nullable=False, index=True
    )
    manager_id: uuid.UUID = Field(
        foreign_key="salesperson.id", nullable=False, index=True
    )
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        sa_column=Column(
            String(50),
            nullable=False,
            server_default=OrderStatus.PENDING.value,
        ),
    )
    observations: Optional[str] = Field(default=None)
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
    saller: Optional["Salesperson"] = Relationship(
        back_populates="saller_orders",
        sa_relationship_kwargs={"foreign_keys": "[Order.saller_id]"},
    )
    supervisor: Optional["Salesperson"] = Relationship(
        back_populates="supervisor_orders",
        sa_relationship_kwargs={"foreign_keys": "[Order.supervisor_id]"},
    )
    manager: Optional["Salesperson"] = Relationship(
        back_populates="manager_orders",
        sa_relationship_kwargs={"foreign_keys": "[Order.manager_id]"},
    )
    delivery: Optional["Delivery"] = Relationship(back_populates="order")
    items: List["OrderItem"] = Relationship(back_populates="order")
    stock_movements: List["StockMovement"] = Relationship(back_populates="order")
    client: Optional["Client"] = Relationship(
        back_populates="client_orders",
        sa_relationship_kwargs={"foreign_keys": "[Order.client_id]"},
    )
    store: Optional["Store"] = Relationship(back_populates="orders")
