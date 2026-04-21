from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_async_sqlalchemy import db
from app.modules.auth.model import UserSession
from app.modules.user.schema import LoginRequest
from app.modules.auth.schema import RefreshTokenBody, Token
from app.modules.auth.service import (
    create_access_token,
    create_refresh_token,
    authenticate_user,
)
from app.modules.user.service import get_user_by_id

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

    access_token, expire = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.profile,  # ajuste conforme seu model
        }
    )
    refresh_token = await create_refresh_token(str(user.id))

    return Token(
        access_token=access_token,
        token_type="bearer",
        expire_at=expire,
        refresh_token=refresh_token,
    )


@router.post("/refresh")
async def refresh(body: RefreshTokenBody) -> Token:
    try:
        session_id = UUID(body.refresh_token)
    except:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    session = await db.session.get(UserSession, session_id)

    if not session:
        raise HTTPException(status_code=401, detail="Session not found")

    if session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    user = await get_user_by_id(str(session.user_id))

    if not user or not user.active:
        raise HTTPException(status_code=403, detail="User inactive")

    # 🔥 gera novo access token
    access_token, expire = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.profile,
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expire_at=expire,
        refresh_token=body.refresh_token,  # mantém o mesmo
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


@router.post("/logout")
async def logout(body: RefreshTokenBody):
    try:
        session_id = UUID(body.refresh_token)
    except:
        return

    session = await db.session.get(UserSession, session_id)

    if session:
        await db.session.delete(session)
        await db.session.commit()

    return {"detail": "Logged out"}
