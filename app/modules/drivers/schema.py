from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict

from app.modules.drivers.model import TypeLicense


class DriverCreate(BaseModel):
    name: str
    code: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    license: Optional[str] = None
    type: TypeLicense = TypeLicense.B
    validity: Optional[datetime] = None
    ear: Optional[bool] = None
    active: bool = True
    image: Optional[str] = None


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
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
    code: str | None = None
    cpf: str | None = None
    phone: str | None = None
    license: str | None = None
    type: TypeLicense
    validity: datetime | None = None
    ear: bool | None = None
    active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
