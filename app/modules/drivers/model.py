import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column, DateTime, String, func, text


if TYPE_CHECKING:
    from app.modules.car.model import Car


class TypeLicense(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class Driver(SQLModel, table=True):
    __tablename__ = "drivers"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    name: str = Field()
    cpf: Optional[str] = Field(default=None, nullable=True)
    license: str = Field()
    type: TypeLicense = Field(
        default=TypeLicense.B,
        sa_column=Column(
            String(50),
            nullable=False,
            server_default=TypeLicense.B.value,
        ),
    )
    validity: Optional[datetime] = Field(default=None)
    phone: str = Field()
    active: bool = Field(default=True, sa_column_kwargs={"server_default": "true"})
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    image: str | None = Field(default=None)

    # Relationship
    car_driver: List["Car"] = Relationship(back_populates="driver")
