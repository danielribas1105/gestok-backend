from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, text
from sqlmodel import Field, SQLModel


class UserSession(SQLModel, table=True):
    __tablename__ = "user_session"  # type: ignore

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )

    user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")

    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
