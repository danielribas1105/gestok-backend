import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    passwordHash: Optional[str] = Field(default=None, nullable=True)
    emailVerified: bool = Field(default=False)
    image: Optional[str] = Field(default=None, nullable=True)
    profile: str = Field(default="user")
    active: bool = Field(default=True)
    createdAt: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updatedAt: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
