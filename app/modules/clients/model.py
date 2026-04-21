from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlalchemy import Column, DateTime, func, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
   from app.modules.orders.model import Order

class Client(SQLModel, table=True):
   __tablename__= "clients"
   id: uuid.UUID = Field(
      default_factory=uuid.uuid4,
      primary_key=True,
      sa_column_kwargs={"server_default": text("gen_random_uuid()")},
   )
   code: str = Field(sa_column_kwargs={"unique": True, "index": True})
   name: str = Field()
   trade_name: str = Field()
   cnpj: str = Field(sa_column_kwargs={"unique": True, "index": True})
   insc_e: str = Field(sa_column_kwargs={"unique": True, "index": True})
   address: Optional[str] = Field(default=None, nullable=True)
   region: Optional[str] = Field(default=None, nullable=True)
   city: Optional[str] = Field(default=None, nullable=True)
   state: Optional[str] = Field(default=None, nullable=True)
   contact: str
   active: bool = Field(default=True)
   created_at: Optional[datetime] = Field(
         default=None,
         sa_column=Column(DateTime(timezone=True), server_default=func.now()),
      )
   image: Optional[str] = Field(default=None, nullable=True)

   # Relationship
   client_orders: List["Order"] = Relationship(back_populates="client")