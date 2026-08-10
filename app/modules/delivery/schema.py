import uuid
from datetime import datetime
from typing import Optional
from pydantic import ConfigDict
from sqlmodel import SQLModel
from app.modules.delivery.model import DeliveryStatus


class DeliveryCreate(SQLModel):
    order_id: uuid.UUID
    car_id: uuid.UUID
    # driver_id removido: agora é derivado do carro no service


class DeliveryUpdate(SQLModel):
    car_id: Optional[uuid.UUID] = None
    status: Optional[DeliveryStatus] = None
    # driver_id não é mais editável diretamente aqui;
    # troca de motorista acontece trocando o car_id


class DeliveryConfirm(SQLModel):
    # Preenchido pelo usuário logístico, em nome do motorista
    observations: Optional[str] = None


class DeliveryRead(SQLModel):
    id: uuid.UUID
    order_id: uuid.UUID
    driver_id: uuid.UUID
    car_id: uuid.UUID
    status: DeliveryStatus
    confirmed_by_driver: bool
    confirmed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
