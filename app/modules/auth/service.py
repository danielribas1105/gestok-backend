from datetime import datetime, timedelta, timezone
from math import floor
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
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

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, floor(expire.timestamp())


async def authenticate_user(email: str, password: str):
    """Authenticate user"""
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user.passwordHash):
        return False

    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    # corrigido: get_user_by_id agora usa db.session interno, sem passar db
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception

    if user.active is False:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def create_refresh_token(user_id: str, expires_delta: timedelta | None = None):
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=REFRESH_TOKEN_EXPIRE_MINUTES
        )

    new_session = UserSession(user_id=UUID(user_id), expires_at=expire)

    db.session.add(new_session)
    await db.session.commit()
    await db.session.refresh(new_session)

    to_encode = {"sub": user_id, "jti": str(new_session.id)}
    token, _ = create_access_token(  # corrigido: desempacota a tuple, retorna só str
        data=to_encode,
        expires_delta=expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    return token
