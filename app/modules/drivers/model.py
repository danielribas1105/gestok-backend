import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column, DateTime, String, func

if TYPE_CHECKING:
    from app.modules.user.model import User


class TypeLicense(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class DriverProfile(SQLModel, table=True):
    __tablename__ = "driver_profiles"

    # A PK é também a FK para users — isso garante 1:1 no banco
    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        primary_key=True,  # PK + FK = 1:1 garantido
    )
    license: str = Field()
    type: TypeLicense = Field(
        default=TypeLicense.B,
        sa_column=Column(
            String(50), nullable=False, server_default=TypeLicense.B.value
        ),
    )
    validity: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    ear: Optional[bool] = Field(default=True)

    # Relationship
    user: Optional["User"] = Relationship(back_populates="driver_profile")
