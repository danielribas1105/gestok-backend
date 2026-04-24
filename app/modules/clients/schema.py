from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class ClientCreate(BaseModel):
    code: str
    name: str
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    insc_e: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    contact: Optional[str] = None
    active: bool = True


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    insc_e: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    contact: Optional[str] = None
    active: Optional[bool] = None


class ClientResponse(BaseModel):
    id: uuid.UUID
    name: str
    trade_name: str | None = None
    cnpj: str | None = None
    insc_e: str | None = None
    address: str | None = None
    region: str | None = None
    city: str | None = None
    state: str | None = None
    contact: str | None = None
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientsSchema(BaseModel):
    clients: list[ClientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
