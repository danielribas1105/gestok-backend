import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, DateTime, String, func, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.orders.model import Order
    from app.modules.car.model import Car
    from app.modules.user.model import User


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    RETURN = "return"
    CANCELED = "canceled"
    CONCLUDED = "concluded"


class Delivery(SQLModel, table=True):
    __tablename__ = "deliveries"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    order_id: uuid.UUID = Field(
        foreign_key="orders.id", nullable=False, index=True, unique=True
    )
    car_id: uuid.UUID = Field(foreign_key="cars.id", nullable=False, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)

    weight: Optional[float] = Field(default=None, nullable=True)  # Cargo weight
    invoice: Optional[str] = Field(default=None)  # Invoice number
    status: DeliveryStatus = Field(
        default=DeliveryStatus.PENDING,
        sa_column=Column(
            String(20), nullable=False, server_default=DeliveryStatus.PENDING.value
        ),
    )
    observations: Optional[str] = Field(default=None)

    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    departed_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )  # Load out date
    delivery_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    delivery_confirmed: bool = Field(default=False)

    # Relationship
    order: Optional["Order"] = Relationship(back_populates="delivery")
    car: Optional["Car"] = Relationship(back_populates="deliveries")
    user: Optional["User"] = Relationship(back_populates="deliveries")
