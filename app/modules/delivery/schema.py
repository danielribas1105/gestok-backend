import uuid
from datetime import datetime
from typing import Optional
from pydantic import ConfigDict
from sqlmodel import SQLModel
from app.modules.delivery.model import DeliveryStatus


class DeliveryCreate(SQLModel):
    order_id: uuid.UUID
    car_id: uuid.UUID
    user_id: uuid.UUID
    weight: float
    invoice: Optional[str] = None
    status: DeliveryStatus = DeliveryStatus.PENDING
    observations: Optional[str] = None
    departed_at: Optional[datetime] = None
    delivery_at: Optional[datetime] = None
    delivery_confirmed: Optional[bool] = False


class DeliveryUpdate(SQLModel):
    car_id: Optional[uuid.UUID] = None
    status: Optional[DeliveryStatus] = None


class DeliveryRead(SQLModel):
    id: uuid.UUID
    order_id: uuid.UUID
    car_id: uuid.UUID
    user_id: uuid.UUID
    weight: Optional[float] = None
    invoice: Optional[str] = None
    status: DeliveryStatus
    observations: Optional[str] = None
    created_at: datetime
    departed_at: Optional[datetime] = None
    delivery_at: Optional[datetime] = None
    delivery_confirmed: Optional[bool] = None

    # Campos resolvidos
    order_code: Optional[str] = None
    car: Optional[str] = None
    driver: Optional[str] = None
    user: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
