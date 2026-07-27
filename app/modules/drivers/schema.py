from datetime import datetime
from typing import Optional
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
    license: Optional[str] = None
    type: Optional[TypeLicense] = None
    validity: Optional[datetime] = None
    ear: Optional[bool] = None


class DriverRead(BaseModel):
    license: str
    type: TypeLicense
    validity: Optional[datetime] = None
    ear: Optional[bool] = None

    model_config = {"from_attributes": True}
