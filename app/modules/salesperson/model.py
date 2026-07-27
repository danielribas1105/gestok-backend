import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Column, DateTime, String, func, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.orders.model import Order


class SalespersonProfile(str, enum.Enum):
    SELLER = "seller"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"


class Salesperson(SQLModel, table=True):
    __tablename__ = "salesperson"  # type: ignore

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    code: str = Field(unique=True, index=True)
    name: str
    trade_name: Optional[str] = Field(default=None, nullable=True)
    email: Optional[str] = Field(default=None, nullable=True)
    cpf: Optional[str] = Field(default=None, nullable=True)
    phone: Optional[str] = Field(default=None, nullable=True)
    profile: SalespersonProfile = Field(
        default=SalespersonProfile.SELLER,
        sa_column=Column(
            String(50),
            nullable=False,
            server_default=SalespersonProfile.SELLER.value,
        ),
    )
    active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    image: Optional[str] = Field(default=None, nullable=True)

    # Relationship
    saller_orders: List["Order"] = Relationship(
        back_populates="saller",
        sa_relationship_kwargs={"foreign_keys": "[Order.saller_id]"},
    )
    supervisor_orders: List["Order"] = Relationship(
        back_populates="supervisor",
        sa_relationship_kwargs={"foreign_keys": "[Order.supervisor_id]"},
    )
    manager_orders: List["Order"] = Relationship(
        back_populates="manager",
        sa_relationship_kwargs={"foreign_keys": "[Order.manager_id]"},
    )
