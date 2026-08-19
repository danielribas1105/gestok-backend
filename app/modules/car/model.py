from datetime import datetime
import enum
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column, DateTime, String, UniqueConstraint, func, text

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


class CapacityUnit(str, enum.Enum):
    M3 = "m3"  # volume — vans/baús maiores, carga paletizada
    BOXES = "boxes"  # quantidade de caixas — veículos menores, não paletizados
    KG = "kg"  # peso — quando o limitante é peso, não espaço
    PALLETS = "pallets"  # quantidade de pallets


class CarCapacity(SQLModel, table=True):
    __tablename__ = "car_capacities"
    __table_args__ = (UniqueConstraint("car_id", "unit", name="uq_car_capacity_unit"),)

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    car_id: uuid.UUID = Field(foreign_key="cars.id", nullable=False, index=True)
    unit: CapacityUnit = Field(
        default=CapacityUnit.M3,
        sa_column=Column(
            String(20), nullable=False, server_default=CapacityUnit.M3.value
        ),
    )
    value: float = Field(default=None, nullable=True)

    # Relationship
    car: "Car" = Relationship(back_populates="capacities")


class Car(SQLModel, table=True):
    __tablename__ = "cars"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    plate: str = Field(sa_column_kwargs={"unique": True, "index": True})
    model: str = Field()
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
    active: bool = Field(default=True, sa_column_kwargs={"server_default": "true"})
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    image: str | None = Field(default=None)

    # Relationship
    driver: Optional["Driver"] = Relationship(back_populates="car")
    deliveries: List["Delivery"] = Relationship(back_populates="car")
    capacities: List["CarCapacity"] = Relationship(
        back_populates="car",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
