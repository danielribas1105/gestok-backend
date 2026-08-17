from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.car.model import CarFuel, CapacityUnit
from app.modules.drivers.schema import DriverRead

# ---------------------------------------------------------------------------
# CarCapacity
# ---------------------------------------------------------------------------


class CarCapacityCreate(BaseModel):
    unit: CapacityUnit
    value: float

    @field_validator("value")
    @classmethod
    def value_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("value deve ser maior que zero")
        return v


class CarCapacityUpdate(BaseModel):
    id: Optional[uuid.UUID] = None  # presente = update; ausente = create
    unit: CapacityUnit
    value: float

    @field_validator("value")
    @classmethod
    def value_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("value deve ser maior que zero")
        return v


class CarCapacityRead(BaseModel):
    id: uuid.UUID
    unit: CapacityUnit
    value: float

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Car
# ---------------------------------------------------------------------------


class CarCreate(BaseModel):
    plate: str
    model: str
    driver_id: uuid.UUID
    manufacture: int | None = None
    km: int | None = None
    fuel: CarFuel = CarFuel.DIESEL
    strength: str | None = None
    versatility: str | None = None
    active: bool = True
    image: str | None = None
    capacities: list[CarCapacityCreate] = []

    @field_validator("capacities")
    @classmethod
    def unique_units(cls, v: list[CarCapacityCreate]) -> list[CarCapacityCreate]:
        units = [c.unit for c in v]
        if len(units) != len(set(units)):
            raise ValueError(
                "cada unidade de capacidade só pode aparecer uma vez por veículo"
            )
        return v


class CarUpdate(BaseModel):
    plate: Optional[str] = None
    model: Optional[str] = None
    driver_id: Optional[uuid.UUID] = None
    manufacture: Optional[int] = None
    km: Optional[int] = None
    fuel: Optional[CarFuel] = None
    strength: Optional[str] = None
    versatility: Optional[str] = None
    active: Optional[bool] = None
    image: Optional[str] = None
    # lista completa: itens com id -> update; sem id -> create;
    # ids existentes que não vierem na lista -> a service deve remover
    capacities: Optional[list[CarCapacityUpdate]] = None

    @field_validator("capacities")
    @classmethod
    def unique_units(
        cls, v: Optional[list[CarCapacityUpdate]]
    ) -> Optional[list[CarCapacityUpdate]]:
        if v is None:
            return v
        units = [c.unit for c in v]
        if len(units) != len(set(units)):
            raise ValueError(
                "cada unidade de capacidade só pode aparecer uma vez por veículo"
            )
        return v


class CarRead(BaseModel):
    id: uuid.UUID
    plate: str
    model: str
    driver_id: uuid.UUID
    manufacture: int | None = None
    km: int | None = None
    fuel: CarFuel
    strength: str | None = None
    versatility: str | None = None
    active: bool
    created_at: datetime | None = None
    image: str | None = None
    driver: Optional[DriverRead] = None
    capacities: list[CarCapacityRead] = []

    model_config = ConfigDict(from_attributes=True)
