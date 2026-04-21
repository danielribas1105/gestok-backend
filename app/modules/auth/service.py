from datetime import datetime, timedelta, timezone
from math import floor
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_async_sqlalchemy import db
from jose import jwt, JWTError

from app.config import settings
from app.modules.auth.schema import TokenData
from app.modules.user.service import get_user_by_email, get_user_by_id
from app.modules.auth.model import UserSession
from app.utils.security import verify_password

SECRET_KEY = settings.JWT_TOKEN_SECRET
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = settings.REFRESH_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> tuple[str, int]:
    """Generates a encoded JWT with the provided data and expiration time."""
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, floor(expire.timestamp())


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_token(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    return decode_token(token)


async def authenticate_user(email: str, password: str):
    """Authenticate user"""
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False

    return user


async def get_current_user(request: Request):
    token = request.headers.get("Authorization")

    if token and token.startswith("Bearer "):
        token = token.replace("Bearer ", "")
    else:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401)

    except JWTError:
        raise HTTPException(status_code=401)

    user = await get_user_by_id(user_id)

    if not user or not user.active:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def create_refresh_token(user_id: str):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=REFRESH_TOKEN_EXPIRE_MINUTES
    )

    new_session = UserSession(user_id=UUID(user_id), expires_at=expire)

    db.session.add(new_session)
    await db.session.commit()
    await db.session.refresh(new_session)

    return str(new_session.id)
