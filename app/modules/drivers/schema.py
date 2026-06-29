from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.modules.drivers.model import TypeLicense


class DriverProfileCreate(BaseModel):
    license: str
    type: TypeLicense = TypeLicense.B
    validity: Optional[datetime] = None
    ear: Optional[bool] = None


class DriverProfileUpdate(BaseModel):
    license: Optional[str] = None
    type: Optional[TypeLicense] = None
    validity: Optional[datetime] = None
    ear: Optional[bool] = None


class DriverProfileResponse(BaseModel):
    license: str
    type: TypeLicense
    validity: Optional[datetime] = None
    ear: Optional[bool] = None

    model_config = {"from_attributes": True}
