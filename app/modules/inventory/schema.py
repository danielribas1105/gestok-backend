from datetime import datetime
from typing import Optional
import uuid
from sqlmodel import SQLModel

from app.modules.products.schema import ProductResponse


class InventoryBase(SQLModel):
    product_id: uuid.UUID
    quantity: int
 
 
class InventoryCreate(InventoryBase):
    """Criação manual de um registro inicial de estoque."""
    pass
 
 
class InventoryUpdate(SQLModel):
    """
    Ajuste manual de estoque (ex: inventário físico, correção).
    Distinto das atualizações automáticas disparadas por Orders.
    """
    quantity: int
    reason: Optional[str] = None  # auditoria do ajuste
 
 
class InventoryRead(InventoryBase):
    id: uuid.UUID
    last_updated_at: Optional[datetime]
 
    class Config:
        from_attributes = True
 
 
class InventoryReadWithProduct(InventoryRead):
    """Visão completa do estoque com dados do produto embutidos."""
    product: ProductResponse
 
    class Config:
        from_attributes = True