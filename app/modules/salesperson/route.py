import uuid

from fastapi import APIRouter, Depends

from app.modules.auth.service import get_current_user
from app.modules.salesperson.schema import SalespersonRead
from app.modules.user.model import User
from app.modules.user import service

router = APIRouter(prefix="/salesperson", tags=["Salesperson"])


@router.get("", response_model=list[SalespersonRead])
async def list_salesperson(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_salesperson(offset, limit)
