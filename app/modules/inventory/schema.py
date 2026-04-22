from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict

from app.modules.products.schema import ProductResponse


class InventoryBase(BaseModel):
    product_id: uuid.UUID
    quantity: int


class InventoryCreate(InventoryBase):
    """Criação manual de um registro inicial de estoque."""

    pass


class InventoryUpdate(BaseModel):
    """
    Ajuste manual de estoque (ex: inventário físico, correção).
    Distinto das atualizações automáticas disparadas por Orders.
    """

    quantity: int
    reason: Optional[str] = None  # auditoria do ajuste


class InventoryResponse(InventoryBase):
    id: uuid.UUID
    last_updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class InventoryResponseWithProduct(InventoryResponse):
    """Visão completa do estoque com dados do produto embutidos."""

    product: ProductResponse

    model_config = ConfigDict(from_attributes=True)
