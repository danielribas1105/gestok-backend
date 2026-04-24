from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict

from app.modules.car.model import CarFuel


class DriverCreate(BaseModel):
    name: str
    cpf: Optional[str] = None
    license: Optional[str] = None
    type: Optional[str] = None
    validity: Optional[datetime] = None
    phone: Optional[str] = None
    active: bool = True
    image: Optional[str] = None


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    cpf: Optional[str] = None
    license: Optional[str] = None
    type: Optional[int] = None
    validity: Optional[datetime] = None
    active: Optional[bool] = None
    image: Optional[str] = None


class DriverResponse(BaseModel):
    id: uuid.UUID
    name: str
    cpf: str | None = None
    license: str
    type: str | None = None
    validity: datetime | None = None
    active: bool
    created_at: datetime
    image: str | None = None

    model_config = ConfigDict(from_attributes=True)
