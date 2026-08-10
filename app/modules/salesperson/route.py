import uuid

from fastapi import APIRouter, Depends, HTTPException
from app.modules.auth.service import get_current_user
from app.modules.salesperson.schema import SalespersonCreate, SalespersonRead
from app.modules.salesperson import service
from app.modules.user.model import User

router = APIRouter(prefix="/salesperson", tags=["Salesperson"])


@router.get("", response_model=list[SalespersonRead])
async def list_salesperson(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_salesperson(offset, limit)


@router.post("", response_model=SalespersonRead, status_code=201)
async def create_salesperson(
    salesperson: SalespersonCreate, user: User = Depends(get_current_user)
):
    return await service.create_salesperson(salesperson)


@router.get("/{salesperson_id}", response_model=SalespersonRead)
async def get_salesperson(
    salesperson_id: uuid.UUID, user: User = Depends(get_current_user)
):
    salesperson = await service.get_salesperson_by_id(salesperson_id)
    if not salesperson:
        raise HTTPException(status_code=404, detail="Vendedor não encontrado")
    return salesperson
