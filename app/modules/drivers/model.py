import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column, DateTime, String, func, text

if TYPE_CHECKING:
    from app.modules.car.model import Car
    from app.modules.delivery.model import Delivery


class TypeLicense(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class Driver(SQLModel, table=True):
    __tablename__ = "drivers"  # type: ignore

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    name: str
    code: Optional[str] = Field(default=None, nullable=True)
    cpf: Optional[str] = Field(default=None, nullable=True)
    phone: Optional[str] = Field(default=None, nullable=True)
    license: Optional[str] = Field(default=None, nullable=True)
    type: TypeLicense = Field(
        default=TypeLicense.B,
        sa_column=Column(
            String(50), nullable=False, server_default=TypeLicense.B.value
        ),
    )
    validity: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
    )
    ear: Optional[bool] = Field(default=True)
    active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    image: Optional[str] = Field(default=None, nullable=True)

    # Relationship
    car: Optional["Car"] = Relationship(back_populates="driver")
    deliveries: List["Delivery"] = Relationship(back_populates="driver")
