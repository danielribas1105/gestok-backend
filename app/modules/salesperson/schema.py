from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr

from app.modules.salesperson.model import SalespersonProfile


class SalespersonCreate(BaseModel):
    code: str
    name: str
    trade_name: str | None = None
    email: EmailStr | None = None
    cpf: str | None = None
    phone: str | None = None
    profile: SalespersonProfile = SalespersonProfile.SELLER
    active: bool = True


class SalespersonUpdate(BaseModel):
    validity: Optional[datetime] = None
    ear: Optional[bool] = None


class SalespersonRead(BaseModel):
    id: uuid.UUID
    code: str
    name: Optional[str] = None
    trade_name: Optional[str] = None
    email: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    profile: SalespersonProfile
    active: bool

    model_config = {"from_attributes": True}
