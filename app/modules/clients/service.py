import uuid

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy.future import select
from app.modules.clients.model import Client
from app.modules.clients.schema import ClientCreate, ClientUpdate


async def list_clients(offset: int = 0, limit: int = 20) -> list[Client]:
    result = await db.session.execute(select(Client).offset(offset).limit(limit))
    return result.scalars().all()


async def create_client(data: ClientCreate) -> Client:
    client = Client(**data.model_dump())
    db.session.add(client)
    await db.session.commit()
    await db.session.refresh(client)
    return client


async def get_client_by_id(client_id: uuid.UUID) -> Client | None:
    client = await db.session.execute(select(Client).where(Client.id == client_id))
    return client.scalars().first()


async def update(client_id: uuid.UUID, data: ClientUpdate) -> Client:
    client = await get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    await db.session.commit()
    await db.session.refresh(client)
    return client


async def delete(client_id: uuid.UUID) -> None:
    client = await get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    await db.session.delete(client)
    await db.session.commit()


async def get_client_by_name(client) -> Client | None:
    # print(f"🔍 Buscando cliente {client}")
    session = db.session
    # print(f"Sessão ativa: {session}")

    stmt = select(Client).where(Client.client == client.strip())
    # print(f"SQL gerado: {stmt}")

    # TODO - Caso o cliente não exista na base, inserir novo cliente
    result = await session.execute(stmt)
    client = result.scalars().first()

    # print(f"Resultado da query: {client}")
    return client.id
