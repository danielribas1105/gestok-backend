from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.orders.model import OrderStatus, OrderOperationType

# ─────────────────────────────────────────────
# ORDER ITEM
# ─────────────────────────────────────────────


class OrderItemBase(BaseModel):
    product_id: uuid.UUID
    quantity: int
    total_price: float


class OrderItemCreate(OrderItemBase):
    item_number: Optional[str] = None
    # row_hash não é enviado pelo cliente — calculado no backend


class OrderItemUpdate(BaseModel):
    quantity: Optional[int] = None
    total_price: Optional[float] = None


class OrderItemRead(OrderItemBase):
    id: uuid.UUID
    order_id: uuid.UUID
    item_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderItemReadNested(OrderItemBase):
    """OrderItem embutido na leitura de uma Order (sem order_id redundante)."""

    id: uuid.UUID
    item_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────────


class OrderBase(BaseModel):
    branch_code: str
    code: str
    operationtype: OrderOperationType = OrderOperationType.SALE
    observations: Optional[str] = None


class OrderCreate(OrderBase):
    """
    Ao criar uma Order, os itens já devem ser enviados juntos.
    O back-end cria a Order e os OrderItems em uma única transação.
    """

    client_id: uuid.UUID
    store_id: uuid.UUID
    saller_id: uuid.UUID
    supervisor_id: uuid.UUID
    manager_id: uuid.UUID
    issued_at: Optional[datetime] = None
    items: List[OrderItemCreate]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Uma order deve conter ao menos um item.")
        return v


class OrderUpdate(BaseModel):
    operationtype: Optional[OrderOperationType] = None
    observations: Optional[str] = None
    status: Optional[OrderStatus] = None
    release_reason: Optional[str] = None
    released_at: Optional[datetime] = None


class OrderStatusUpdate(BaseModel):
    """Usado para transições de status isoladas (ex: confirmar, cancelar)."""

    status: OrderStatus
    release_reason: Optional[str] = None  # obrigatório na prática ao sair de BLOCKED


class OrderResponse(OrderBase):
    id: uuid.UUID
    status: OrderStatus
    client_id: uuid.UUID
    store_id: uuid.UUID
    saller_id: uuid.UUID
    supervisor_id: uuid.UUID
    manager_id: uuid.UUID
    issued_at: Optional[datetime] = None
    release_reason: Optional[str] = None
    released_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    items: List[OrderItemReadNested] = []

    model_config = ConfigDict(from_attributes=True)


class OrderResponseSummary(BaseModel):
    """Versão resumida para listagens (sem carregar items)."""

    id: uuid.UUID
    branch_code: str
    code: str
    operationtype: OrderOperationType
    status: OrderStatus
    client_id: uuid.UUID
    store_id: uuid.UUID
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
