from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.user.model import User, UserProfile
from app.modules.user.schema import UserCreate, UserUpdate
from app.utils.security import get_hash_password


# helper para sempre trazer o driver_profile junto
def _user_with_driver():
    return select(User).options(selectinload(User.driver_profile))


async def list_users(offset: int = 0, limit: int = 20) -> list[User]:
    result = await db.session.execute(
        select(User).offset(offset).limit(limit).order_by(User.name)
    )
    return result.scalars().all()


""" async def list_drivers(offset: int = 0, limit: int = 20) -> list[User]:
    result = await db.session.execute(
        _user_with_driver()
        .where(User.profile == UserProfile.DRIVER)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all() """


async def get_user_by_id(user_id: str) -> User | None:
    result = await db.session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_by_email(email: str) -> User | None:
    result = await db.session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user(data: UserCreate) -> User:
    print(f"User {data}")
    result = await db.session.execute(select(User).where(User.email == data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    dump = data.model_dump(exclude={"password"})
    dump["password_hash"] = get_hash_password(data.password)

    user = User(**dump)
    db.session.add(user)
    await db.session.commit()
    ## await db.session.refresh(user)
    # re-fetch com eager load para retornar driver_profile populado
    return await get_user_by_id(str(user.id))


async def update_user(user_id: str, data: UserUpdate) -> User:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    dump = data.model_dump(exclude_unset=True, exclude={"password", "driver"})

    if data.password:
        dump["password_hash"] = get_hash_password(data.password)

    for field, value in dump.items():
        setattr(user, field, value)

    await db.session.commit()
    ## await db.session.refresh(user)
    return await get_user_by_id(user_id)


async def delete_user(user_id: str) -> None:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    await db.session.delete(user)
    await db.session.commit()
