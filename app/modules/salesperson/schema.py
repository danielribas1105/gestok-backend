from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.modules.salesperson.model import SalespersonProfile


class SalespersonCreate(BaseModel):
    code: str
    name: str
    trade_name: str | None = None
    email: EmailStr | None = None
    cpf: str | None = None
    phone: str | None = None
    profile: SalespersonProfile.SELLER
    active: bool = True


class SalespersonUpdate(BaseModel):
    license: Optional[str] = None
    validity: Optional[datetime] = None
    ear: Optional[bool] = None


class SalespersonRead(BaseModel):
    license: str
    validity: Optional[datetime] = None
    ear: Optional[bool] = None

    model_config = {"from_attributes": True}
