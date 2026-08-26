from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, model_validator

from app.modules.inventory.model import MovementType
from app.modules.products.schema import ProductRead


class InventoryBase(BaseModel):
    product_id: uuid.UUID


class InventoryCreate(InventoryBase):
    """Criação manual de um registro inicial de estoque."""

    quantity: int


"""
Ajuste manual de estoque (ex: inventário físico, correção).
Distinto das atualizações automáticas disparadas por Orders.
"""
""" class InventoryUpdate(BaseModel):
    quantity: int
    reason: Optional[str] = None """


class InventoryUpdateBatch(InventoryBase):
    code: str
    movement_type: MovementType
    quantity: int
    order_id: Optional[uuid.UUID] = None
    movement_date: datetime
    user_id: uuid.UUID
    observations: Optional[str] = None

    @model_validator(mode="after")
    def validate_order_id_by_movement_type(self) -> "InventoryUpdateBatch":
        if self.movement_type == MovementType.OUT and self.order_id is None:
            raise ValueError(
                "order_id é obrigatório para movement_type=OUT (saída via pedido)"
            )
        if self.movement_type == MovementType.IN and self.order_id is not None:
            raise ValueError(
                "order_id não deve ser informado para movement_type=IN "
                "(entrada é referenciada por romaneio, via 'code')"
            )
        if self.quantity <= 0:
            raise ValueError("quantity deve ser maior que zero")
        return self


class InventoryRead(InventoryBase):
    id: uuid.UUID
    current_quantity: float
    reserved_quantity: float
    available_quantity: float
    last_updated: datetime

    # Campos resolvidos
    product_code: Optional[str] = None
    product_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InventoryReadWithProduct(InventoryRead):
    """Visão completa do estoque com dados do produto embutidos."""

    product: ProductRead

    model_config = ConfigDict(from_attributes=True)


class InventoryBatchFailure(BaseModel):
    product_id: uuid.UUID
    error: str


class InventoryBatchRead(BaseModel):
    created: list[InventoryReadWithProduct]
    failed: list[InventoryBatchFailure]
