# app/modules/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from app.modules.auth.service import get_current_user
from app.modules.user.model import User


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.profile != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return user


def require_driver(user: User = Depends(get_current_user)) -> User:
    if user.profile != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a motoristas",
        )
    return user
