from fastapi import APIRouter, Depends

from app.modules.auth.service import get_current_user
from app.modules.user.schema import UserCreate, UserResponse, UserUpdate
from app.modules.user.model import User
from app.modules.user import service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def my_profile(user: User = Depends(get_current_user)):
    return user


@router.post("/", response_model=UserResponse, status_code=201)
async def register_user(data: UserCreate):
    return await service.create_user(data)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    user: User = Depends(get_current_user),  # corrigido: era authenticate_user
):
    return await service.update_user(str(user.id), data)


@router.delete("/me", status_code=204)
async def delete_account(user: User = Depends(get_current_user)):
    await service.delete_user(str(user.id))
