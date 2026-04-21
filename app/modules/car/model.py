from datetime import datetime
import enum
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column, DateTime, String, func, text


if TYPE_CHECKING:
    from app.modules.drivers.model import Driver
    from app.modules.orders.model import Order


class CarFuel(str, enum.Enum):
    DIESEL = "diesel"
    GASOLINE = "gasoline"
    ETHANOL = "ethanol"
    ELECTRIC = "electric"
    GNV = "gnv"
    HYBRID = "hybrid"


class Car(SQLModel, table=True):
    __tablename__ = "cars"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    model: str = Field()
    license: str = Field(sa_column_kwargs={"unique": True, "index": True})
    manufacture: int | None = Field(default=None)
    km: int | None = Field(default=None)
    fuel: CarFuel = Field(
        default=CarFuel.DIESEL,
        sa_column=Column(
            String(50),
            nullable=False,
            server_default=CarFuel.DIESEL.value,
        ),
    )
    strength: str | None = Field(default=None)
    capacity: str | None = Field(default=None)
    versatility: str | None = Field(default=None)
    active: bool = Field(default=True, sa_column_kwargs={"server_default": "true"})
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    image: str | None = Field(default=None)

    # Relationship
    driver: Optional["Driver"] = Relationship(back_populates="car_driver")
    car_orders: List["Order"] = Relationship(back_populates="car")