from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class ClientCreate(BaseModel):
    code: str
    name: str


class ClientUpdate(BaseModel):
    name: Optional[str] = None


class ClientRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class ClientReadWithStores(ClientRead):
    stores: list["StoreRead"] = []


class ClientsSchema(BaseModel):
    clients: list[ClientRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class StoreCreate(BaseModel):
    code: str
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    insc_e: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    contact: Optional[str] = None
    active: bool = True


class StoreUpdate(BaseModel):
    code: Optional[str] = None
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    insc_e: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    contact: Optional[str] = None
    active: Optional[bool] = None


class StoreRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    code: str
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    insc_e: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    contact: Optional[str] = None
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StoresSchema(BaseModel):
    stores: list[StoreRead]
    total: int
    page: int
    page_size: int
    total_pages: int


ClientReadWithStores.model_rebuild()
