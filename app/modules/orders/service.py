from datetime import datetime, timezone
import uuid
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from app.modules.orders.model import Statement
from app.modules.orders.schema import StatementCreate, StatementUpdate


async def list_statements(offset: int = 0, limit: int = 20) -> list[Statement]:
    result = await db.session.execute(select(Statement).offset(offset).limit(limit))
    return result.scalars().all()


async def create_statement(data: StatementCreate) -> Statement:
    statement = Statement(
        **data.model_dump(exclude_none=True),
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(statement)
    await db.session.commit()
    await db.session.refresh(statement)
    return statement


async def get_statement_by_id(statement_id: uuid.UUID) -> Statement:
    result = await db.session.execute(
        select(Statement).where(Statement.id == statement_id)
    )
    statement = result.scalars().first()

    return statement


async def update(statement_id: uuid.UUID, data: StatementUpdate) -> Statement:
    statement = await get_statement_by_id(statement_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(statement, field, value)
    statement.updated_at = datetime.now(timezone.utc)
    await db.session.commit()
    await db.session.refresh(statement)
    return statement


async def delete(statement_id: uuid.UUID) -> None:
    statement = await get_statement_by_id(statement_id)
    await db.session.delete(statement)
    await db.session.commit()
