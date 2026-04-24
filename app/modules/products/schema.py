from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    code: str
    name: str
    unit: str
    value: float
    description: Optional[str] = None
    active: bool = True
    image: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[float] = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    value: float

    model_config = ConfigDict(from_attributes=True)


class ProductReadWithStock(ProductResponse):
    """
    Produto com a quantidade atual em estoque,
    resolvida via JOIN com Inventory.
    """

    stock_quantity: int = 0

    class Config:
        from_attributes = True
