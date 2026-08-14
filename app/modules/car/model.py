from datetime import datetime
import enum
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column, DateTime, String, func, text

if TYPE_CHECKING:
    from app.modules.drivers.model import Driver
    from app.modules.delivery.model import Delivery


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
    plate: str = Field(sa_column_kwargs={"unique": True, "index": True})
    model: str = Field()
    capacity: float = Field()
    driver_id: uuid.UUID = Field(
        foreign_key="drivers.id",
        nullable=False,
        index=True,
        unique=True,
    )
    manufacture: Optional[int] = Field(default=None, nullable=True)
    km: Optional[int] = Field(default=None, nullable=True)
    fuel: CarFuel = Field(
        default=CarFuel.DIESEL,
        sa_column=Column(
            String(50),
            nullable=False,
            server_default=CarFuel.DIESEL.value,
        ),
    )
    strength: Optional[str] = Field(default=None, nullable=True)
    versatility: Optional[str] = Field(default=None, nullable=True)
    active: bool = Field(default=True, sa_column_kwargs={"server_default": "true"})
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    image: str | None = Field(default=None)

    # Relationship
    driver: Optional["Driver"] = Relationship(back_populates="car")
    deliveries: List["Delivery"] = Relationship(back_populates="car")
