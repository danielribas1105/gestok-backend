from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    code: Optional[str] = None
    name: str
    unit: str
    active: bool = True
    image: Optional[str] = None
    updated_at: Optional[datetime] = None


class ProductUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    unit: Optional[str] = None
    active: Optional[bool] = None
    image: Optional[str] = None
    updated_at: Optional[datetime] | None = None


class ProductRead(BaseModel):
    id: uuid.UUID
    name_code: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None
    unit: Optional[str] = None
    active: Optional[bool] = None
    image: Optional[str] = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductReadWithStock(ProductRead):
    """
    Produto com a quantidade atual em estoque,
    resolvida via JOIN com Inventory.
    """

    stock_quantity: int = 0

    class Config:
        from_attributes = True
