from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict

from app.modules.car.model import CarFuel
from app.modules.drivers.schema import DriverRead


class CarCreate(BaseModel):
    plate: str
    model: str
    capacity: float
    driver_id: uuid.UUID
    manufacture: int | None = None
    km: int | None = None
    fuel: CarFuel = CarFuel.DIESEL
    strength: str | None = None
    versatility: str | None = None
    active: bool = True
    image: str | None = None


class CarUpdate(BaseModel):
    plate: Optional[str] = None
    model: Optional[str] = None
    capacity: Optional[float] = None
    driver_id: Optional[uuid.UUID] = None
    manufacture: Optional[int] = None
    km: Optional[int] = None
    fuel: Optional[CarFuel] = None
    strength: Optional[str] = None
    versatility: Optional[str] = None
    active: Optional[bool] = None
    image: Optional[str] = None


class CarRead(BaseModel):
    id: uuid.UUID
    plate: str
    model: str
    capacity: float | None = None
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

    model_config = ConfigDict(from_attributes=True)
