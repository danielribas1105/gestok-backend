import uuid

from fastapi import APIRouter, Depends, HTTPException
from app.modules.auth.service import get_current_user
from app.modules.clients.schema import ClientCreate, ClientResponse, ClientUpdate
from app.modules.user.model import User
from app.modules.clients import service

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=list[ClientResponse])
async def list_clients(
    offset: int = 0, limit: int = 20, user: User = Depends(get_current_user)
):
    return await service.list_clients(offset, limit)


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(client: ClientCreate, user: User = Depends(get_current_user)):
    return await service.create_client(client)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: uuid.UUID, user: User = Depends(get_current_user)):
    client = await service.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    user: User = Depends(get_current_user),
):
    return await service.update(client_id, data)


@router.delete("/{client_id}", status_code=204)
async def delete_client(client_id: uuid.UUID, user: User = Depends(get_current_user)):
    await service.delete(client_id)
