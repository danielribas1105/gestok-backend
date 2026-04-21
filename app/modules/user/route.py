from fastapi import APIRouter, Depends

from app.modules.auth.service import get_current_user
from app.modules.user.schema import UserCreate, UserResponse, UserUpdate
from app.modules.user.model import User
from app.modules.user import service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
async def list_users(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_users(offset, limit)


@router.get("/me", response_model=UserResponse)
async def my_profile(user: User = Depends(get_current_user)):
    return user


@router.post("", response_model=UserResponse, status_code=201)
async def register_user(data: UserCreate):
    return await service.create_user(data)


@router.put("/{user_id}", response_model=UserResponse)
async def update_profile(
    user_id: str,
    data: UserUpdate,
    user: User = Depends(get_current_user),  # corrigido: era authenticate_user
):
    return await service.update_user(user_id, data)


@router.delete("/{user_id}", status_code=204)
async def delete_account(user_id: str, user: User = Depends(get_current_user)):
    await service.delete_user(user_id)
