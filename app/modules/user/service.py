from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import select

from app.modules.user.model import User
from app.modules.user.schema import UserCreate, UserUpdate
from app.utils.security import get_hash_password


async def create_user(data: UserCreate) -> User:
    result = await db.session.execute(select(User).where(User.email == data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    user = User(
        name=data.name,
        email=data.email,
        passwordHash=get_hash_password(data.password),
        image=data.image,
        profile=data.profile,
    )
    db.session.add(user)
    await db.session.commit()
    await db.session.refresh(user)
    return user


async def get_user_by_id(user_id: str) -> User | None:
    result = await db.session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_by_email(email: str) -> User | None:
    result = await db.session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def update_user(user_id: str, data: UserUpdate) -> User:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.session.commit()
    await db.session.refresh(user)
    return user


async def delete_user(user_id: str) -> None:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    await db.session.delete(user)
    await db.session.commit()
