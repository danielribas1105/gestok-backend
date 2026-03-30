from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.modules.user.schema import LoginRequest
from app.modules.auth.schema import Token
from app.modules.auth.service import (
    create_access_token,
    create_refresh_token,
    authenticate_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def login(data: LoginRequest) -> Token:
    user = await authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token, expire = create_access_token(data={"sub": str(user.id)})
    refresh_token = await create_refresh_token(user_id=str(user.id))

    return Token(
        access_token=access_token,
        token_type="bearer",
        expire_at=expire,
        refresh_token=refresh_token,
    )


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expire = create_access_token(data={"sub": str(user.id)})
    refresh_token = await create_refresh_token(user_id=str(user.id))

    return Token(
        access_token=access_token,
        token_type="bearer",
        expire_at=expire,
        refresh_token=refresh_token,
    )
