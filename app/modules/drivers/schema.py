from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel

from app.modules.drivers.model import TypeLicense


class DriverCreate(BaseModel):
    name: str
    cpf: Optional[str] = None
    phone: Optional[str] = None
    license: str
    type: TypeLicense = TypeLicense.B
    validity: Optional[datetime] = None
    ear: Optional[bool] = None
    active: bool = True
    image: Optional[str] = None


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    license: Optional[str] = None
    type: Optional[TypeLicense] = None
    validity: Optional[datetime] = None
    ear: Optional[bool] = None
    active: Optional[bool] = None


class DriverRead(BaseModel):
    id: uuid.UUID
    name: str
    cpf: str | None = None
    phone: str | None = None
    license: str
    type: TypeLicense
    validity: datetime | None = None
    ear: bool
    active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
