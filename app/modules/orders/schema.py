from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.orders.model import OrderStatus, OrderOperationType

# ─────────────────────────────────────────────
# ORDER ITEM
# ─────────────────────────────────────────────


class OrderItemBase(BaseModel):
    quantity: int
    total_price: float
    item_number: Optional[str] = None


class OrderItemCreate(OrderItemBase):
    product_id: uuid.UUID
    # row_hash não é enviado pelo cliente — calculado no backend


class OrderItemUpdate(BaseModel):
    quantity: Optional[int] = None
    total_price: Optional[float] = None


class OrderItemRead(OrderItemBase):
    id: uuid.UUID
    order_id: uuid.UUID
    item_number: Optional[str] = None
    product_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class OrderItemReadNested(OrderItemBase):
    """OrderItem embutido na leitura de uma Order (sem order_id redundante)."""

    id: uuid.UUID
    item_number: Optional[str] = None
    product_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────────


class OrderBase(BaseModel):
    branch_code: str
    code: str
    operation_type: OrderOperationType = OrderOperationType.SALE


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
    observations: Optional[str] = None

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


# ─────────────────────────────────────────────
# ORDER BATCH
# ─────────────────────────────────────────────


class OrderItemCreatePayload(OrderItemBase):
    code: str
    product_id: str


class OrderCreatePayload(OrderBase):
    release_reason: str | None
    released_at: Optional[datetime] | None
    client_id: str
    store_id: str
    saller_id: str
    supervisor_id: str
    manager_id: str
    issued_at: Optional[datetime] | None
    items: List[OrderItemCreatePayload]

    @field_validator("released_at", "issued_at", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class BatchOrderError(BaseModel):
    code: str
    errors: list[str]


class OrderBatchResponse(BaseModel):
    created: list[OrderResponse]
    failed: list[BatchOrderError]
