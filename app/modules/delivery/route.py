import uuid
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.modules.auth.service import get_current_user
from app.modules.delivery import service
from app.modules.delivery.schema import (
    DeliveryConfirm,
    DeliveryCreate,
    DeliveryRead,
    DeliveryUpdate,
)
from app.modules.user.model import User

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


@router.get("/", response_model=list[DeliveryRead])
async def list_deliveries(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_deliveries(offset, limit)


""" @router.post("/", response_model=DeliveryRead, status_code=201)
def create_delivery(data: DeliveryCreate, session: Session = Depends(get_session)):
    return service.create_delivery(session, data)


@router.get("/{delivery_id}", response_model=DeliveryRead)
def get_delivery(delivery_id: uuid.UUID, session: Session = Depends(get_session)):
    return service.get_delivery(session, delivery_id)


@router.patch("/{delivery_id}", response_model=DeliveryRead)
def update_delivery(
    delivery_id: uuid.UUID,
    data: DeliveryUpdate,
    session: Session = Depends(get_session),
):
    return service.update_delivery(session, delivery_id, data)


@router.patch("/{delivery_id}/confirm", response_model=DeliveryRead)
def confirm_delivery(
    delivery_id: uuid.UUID,
    data: DeliveryConfirm,
    session: Session = Depends(get_session),
):
    return service.confirm_delivery(session, delivery_id)
 """
