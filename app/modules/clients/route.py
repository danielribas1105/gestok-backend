from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.modules.auth.service import get_current_user
from app.modules.clients.model import Client
from app.modules.clients.schema import ClientCreate, ClientResponse, ClientsSchema
from app.modules.clients.service import get_clients_paginated
from app.modules.user.model import User
from app.modules.clients import service

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=ClientsSchema)
async def get_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Recupera todos os clientes cadastrados
    """
    return await get_clients_paginated(
        db=db, page=page, page_size=page_size, search=search
    )


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(client: ClientCreate, user: User = Depends(get_current_user)):
    # TODO - exist client?
    return await service.create_client(client)
