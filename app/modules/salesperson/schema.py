from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict

from app.modules.salesperson.model import SalespersonProfile


class SalespersonCreate(BaseModel):
    code: str
    name: str
    trade_name: str | None = None
    phone: str | None = None
    profile: SalespersonProfile = SalespersonProfile.SELLER
    active: bool = True


class SalespersonUpdate(BaseModel):
    name: Optional[str] = None
    trade_name: Optional[str] = None
    phone: Optional[str] = None
    profile: Optional[SalespersonProfile] = None
    active: Optional[bool] = None


class SalespersonRead(BaseModel):
    id: uuid.UUID
    code: str
    name: Optional[str] = None
    trade_name: Optional[str] = None
    phone: Optional[str] = None
    profile: SalespersonProfile
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
