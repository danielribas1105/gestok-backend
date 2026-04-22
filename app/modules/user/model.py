import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Column, DateTime, Enum as SAEnum, String, func, text
from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from app.modules.orders.model import Order


class UserProfile(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    DRIVER = "driver"


class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    name: str
    email: str = Field(unique=True, index=True)
    cpf: Optional[str] = Field(default=None, nullable=True)
    phone: Optional[str] = Field(default=None, nullable=True)
    password_hash: Optional[str] = Field(default=None, nullable=True)
    email_verified: bool = Field(default=False)
    profile: UserProfile = Field(
        default=UserProfile.OPERATOR,
        sa_column=Column(
            String(50),
            nullable=False,
            server_default=UserProfile.OPERATOR.value,
        ),
    )
    active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    image: Optional[str] = Field(default=None, nullable=True)

    # Relationship
    created_orders: List["Order"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[Order.created_by]"},
    )
