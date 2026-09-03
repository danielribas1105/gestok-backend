import uuid
from fastapi import APIRouter, Depends

from app.modules.auth.service import get_current_user
from app.modules.delivery import service
from app.modules.delivery.schema import (
    DeliveryCreate,
    DeliveryRead,
    DeliveryUpdate,
)
from app.modules.user.model import User

router = APIRouter(prefix="/delivery", tags=["Delivery"])


@router.get("", response_model=list[DeliveryRead])
async def list_delivery(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_delivery(offset, limit)


@router.post("", response_model=list[DeliveryRead], status_code=201)
async def create_delivery(
    delivery: list[DeliveryCreate],
    user: User = Depends(get_current_user),
):
    return await service.create_delivery(delivery)


@router.get("/{delivery_id}", response_model=DeliveryRead)
def get_delivery_by_id(delivery_id: uuid.UUID):
    return service.get_delivery_by_id(delivery_id)


@router.put("/{delivery_id}", response_model=DeliveryRead)
async def update_delivery(
    delivery_id: uuid.UUID,
    data: DeliveryUpdate,
    user: User = Depends(get_current_user),
):
    """
    Update delivery
    """
    return await service.update_delivery(delivery_id, data)


""" @router.patch("/{delivery_id}/confirm", response_model=DeliveryRead)
def confirm_delivery(
    delivery_id: uuid.UUID,
    data: DeliveryConfirm,
    session: Session = Depends(get_session),
):
    return service.confirm_delivery(session, delivery_id) """
