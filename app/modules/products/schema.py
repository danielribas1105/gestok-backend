from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    code: str
    description: str
    unit: str
    value: float
    active: bool = True
    image: Optional[str] = None


class ProductUpdate(BaseModel):
    description: Optional[str] = None
    unit: Optional[str] = None
    value: Optional[float] = None
    active: Optional[bool] = None
    image: Optional[str] = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    code: str
    description: str
    unit: str
    value: float
    active: bool
    image: str

    model_config = ConfigDict(from_attributes=True)


class ProductReadWithStock(ProductResponse):
    """
    Produto com a quantidade atual em estoque,
    resolvida via JOIN com Inventory.
    """

    stock_quantity: int = 0

    class Config:
        from_attributes = True
