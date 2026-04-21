from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.modules.clients.model import Client
from app.modules.clients.schema import ClientCreate, ClientRead, ClientsSchema
from app.modules.clients.service import get_clients_paginated

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/", response_model=ClientsSchema)
async def get_clients(
   page: int = Query(1, ge=1),
   page_size: int = Query(20, ge=1, le=100),
   search: str | None = None,
   db: AsyncSession = Depends(get_db)
):
   """
   Recupera todos os clientes cadastrados
   """
   return await get_clients_paginated(db=db, page=page, page_size=page_size, search=search)

@router.post("/", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(client: ClientCreate, db: AsyncSession = Depends(get_db)):
   # Verifica se cliente já existe
   existing = await db.execute(select(Client).where(Client.cod_client == client.cod_client))
   if existing.scalars().first():
      raise HTTPException(status_code=400, detail="Cliente já cadastrado")

   new_client = Client(
      cod_client=client.cod_client,
      client=client.client,
      active=True,
   )
   db.add(new_client)
   await db.commit()
   await db.refresh(new_client)
   return new_client