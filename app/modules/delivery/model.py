import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, DateTime, String, func, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.orders.model import Order
    from app.modules.drivers.model import Driver
    from app.modules.car.model import Car


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
    driver_id: uuid.UUID = Field(foreign_key="drivers.id", nullable=False, index=True)
    car_id: uuid.UUID = Field(foreign_key="cars.id", nullable=False, index=True)

    status: DeliveryStatus = Field(
        default=DeliveryStatus.PENDING,
        sa_column=Column(
            String(20), nullable=False, server_default=DeliveryStatus.PENDING.value
        ),
    )
    confirmed_by_driver: bool = Field(default=False)
    confirmed_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    # Relationship
    order: Optional["Order"] = Relationship(back_populates="delivery")
    driver: Optional["Driver"] = Relationship(back_populates="deliveries")
    car: Optional["Car"] = Relationship(back_populates="deliveries")
