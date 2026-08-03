from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlalchemy import Column, DateTime, func, text
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

if TYPE_CHECKING:
    from app.modules.orders.model import Order


class Store(SQLModel, table=True):
    __tablename__ = "stores"
    __table_args__ = (
        UniqueConstraint("client_id", "code", name="uq_stores_client_code"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    client_id: uuid.UUID = Field(foreign_key="clients.id", nullable=False, index=True)
    code: str = Field(index=True)  # LOJA — único apenas dentro do cliente
    trade_name: Optional[str] = Field(default=None, nullable=True)
    cnpj: Optional[str] = Field(default=None, nullable=True)
    insc_e: Optional[str] = Field(default=None, nullable=True)
    address: Optional[str] = Field(default=None, nullable=True)
    region: Optional[str] = Field(default=None, nullable=True)
    zip_code: Optional[str] = Field(default=None, nullable=True)
    city: Optional[str] = Field(default=None, nullable=True)
    state: Optional[str] = Field(default=None, nullable=True)
    phone: Optional[str] = Field(default=None, nullable=True)
    contact: Optional[str] = Field(default=None, nullable=True)
    active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    # Relationship
    client: Optional["Client"] = Relationship(back_populates="stores")
    orders: List["Order"] = Relationship(back_populates="store")


class Client(SQLModel, table=True):
    __tablename__ = "clients"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    code: str = Field(sa_column_kwargs={"unique": True, "index": True})
    name: str = Field()

    # Relationship
    client_orders: List["Order"] = Relationship(back_populates="client")
    stores: List["Store"] = Relationship(back_populates="client")
