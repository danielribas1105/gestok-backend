from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.orders.model import OrderStatus

# ─────────────────────────────────────────────
# ORDER ITEM
# ─────────────────────────────────────────────


class OrderItemBase(BaseModel):
    product_id: uuid.UUID
    quantity: int
    total_price: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemUpdate(BaseModel):
    quantity: Optional[int] = None
    total_price: Optional[float] = None


class OrderItemResponse(OrderItemBase):
    id: uuid.UUID
    order_id: uuid.UUID


# ─────────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────────


class OrderBase(BaseModel):
    code: str
    type: str
    observations: Optional[str] = None


class OrderCreate(OrderBase):
    """
    Ao criar uma Order, os itens já devem ser enviados juntos.
    O back-end cria a Order e os OrderItems em uma única transação,
    e em seguida atualiza o Inventory conforme o tipo (entrada/saída).
    """

    items: List[OrderItemCreate]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Uma order deve conter ao menos um item.")
        return v


class OrderUpdate(BaseModel):
    type: Optional[str] = None
    observations: Optional[str] = None
    status: Optional[OrderStatus] = None


class OrderStatusUpdate(BaseModel):
    """Usado para transições de status isoladas (ex: confirmar, cancelar)."""

    status: OrderStatus


class OrderItemResponseNested(OrderItemBase):
    """OrderItem embutido na leitura de uma Order (sem order_id redundante)."""

    id: uuid.UUID
    product_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(OrderBase):
    id: uuid.UUID
    status: OrderStatus
    active: bool
    created_at: Optional[datetime]
    processed_at: Optional[datetime]
    items: List[OrderItemResponseNested] = []

    model_config = ConfigDict(from_attributes=True)


class OrderResponseSummary(BaseModel):
    """Versão resumida para listagens (sem carregar items)."""

    id: uuid.UUID
    code: str
    type: str
    status: OrderStatus
    active: bool
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
