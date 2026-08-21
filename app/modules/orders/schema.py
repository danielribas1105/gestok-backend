from datetime import datetime
import enum
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.orders.model import OrderStatus, OrderOperationType

# ─────────────────────────────────────────────
# ORDER ITEM
# ─────────────────────────────────────────────


class OrderItemStockStatus(str, enum.Enum):
    IN_STOCK = "in_stock"
    NO_STOCK = "no_stock"
    ON_HOLD = "on_hold"


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
    product_name_code: Optional[str] = None
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    product_unit: Optional[str] = None
    product_weight: Optional[float] = None
    product_volume: Optional[float] = None
    product_boxes_pallet: Optional[int] = None
    stock_item_status: Optional[OrderItemStockStatus] = None

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────────


class OrderStockStatus(str, enum.Enum):
    SUFFICIENT = "sufficient"  # todo o pedido cabe no saldo
    PARTIAL = "partial"  # alguns itens cabem, outros não
    INSUFFICIENT = "insufficient"  # nenhum item coube
    ON_HOLD = "on_hold"  # aguardando


class OrderStockHoldUpdate(BaseModel):
    stock_hold: bool
    reason: Optional[str] = None


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
    operation_type: Optional[OrderOperationType] = None
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
    stock_status: Optional[OrderStockStatus] = None
    stock_hold: bool = False
    stock_hold_reason: Optional[str] = None

    # Campos resolvidos
    client_name: Optional[str] = None
    store_name: Optional[str] = None
    saller_name: Optional[str] = None
    supervisor_name: Optional[str] = None
    manager_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderResponseSummary(BaseModel):
    """Versão resumida para listagens (sem carregar items)."""

    id: uuid.UUID
    branch_code: str
    code: str
    operation_type: OrderOperationType
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
    quantity: int
    unit: str
    weight: float


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


# ─────────────────────────────────────────────
# PRODUCTS INFO
# ─────────────────────────────────────────────


class ProductQuantitySummary(BaseModel):
    """Soma de quantidade de um produto entre os pedidos consultados.
    Usado pelo front pra checar se o estoque cobre a entrega de vários
    pedidos selecionados de uma vez.
    """

    product_id: uuid.UUID
    name: str
    name_code: str
    total_quantity: int


class ProductsQuantitySummaryRequest(BaseModel):
    order_ids: list[uuid.UUID]


class ProductQuantityCheck(BaseModel):
    """Compara quanto foi pedido (soma dos order_ids informados) com o
    estoque disponível do produto. Usado pra validar se dá pra atender
    a entrega de vários pedidos selecionados de uma vez.
    """

    product_id: uuid.UUID
    name: str
    name_code: str
    total_quantity: int  # soma pedida (SUM(order_items.quantity))
    available_quantity: (
        float  # inventory.available_quantity (0 se produto sem registro de estoque)
    )
    current_quantity: float
    reserved_quantity: float
    is_sufficient: bool
    shortage: float  # max(0, total_quantity - available_quantity)


class ProductsQuantityCheckRequest(BaseModel):
    item_ids: list[uuid.UUID]


class ProductsQuantityCheckResponse(BaseModel):
    items: list[ProductQuantityCheck]
    all_sufficient: bool
