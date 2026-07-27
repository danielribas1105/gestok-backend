from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict

from app.modules.car.model import CarFuel
from app.modules.drivers.schema import DriverRead


class DriverInfo(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None = None
    driver_profile: Optional[DriverRead] = None

    model_config = ConfigDict(from_attributes=True)


class CarCreate(BaseModel):
    model: str
    plate: str
    driver_id: uuid.UUID
    manufacture: int | None = None
    km: int | None = None
    fuel: CarFuel = CarFuel.DIESEL
    strength: str | None = None
    capacity: int
    versatility: str | None = None
    active: bool = True
    image: str | None = None


class CarUpdate(BaseModel):
    model: Optional[str] = None
    plate: Optional[str] = None
    driver_id: Optional[uuid.UUID] = None
    manufacture: Optional[int] = None
    km: Optional[int] = None
    fuel: Optional[CarFuel] = None
    strength: Optional[str] = None
    capacity: Optional[int] = None
    versatility: Optional[str] = None
    active: Optional[bool] = None
    image: Optional[str] = None


class CarResponse(BaseModel):
    id: uuid.UUID
    model: str
    plate: str
    driver_id: uuid.UUID
    manufacture: int | None = None
    km: int | None = None
    fuel: CarFuel
    strength: str | None = None
    capacity: int | None = None
    versatility: str | None = None
    active: bool
    created_at: datetime | None = None
    image: str | None = None
    driver: Optional[DriverInfo] = None

    model_config = ConfigDict(from_attributes=True)
