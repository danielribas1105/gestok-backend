import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, String, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
   from app.modules.orders.model import Order
   from app.modules.products.model import Product

class MovementType(str, enum.Enum):
   IN = "in"
   OUT = "out"

class Inventory(SQLModel, table=True):
   __tablename__= "inventory"
   id: uuid.UUID = Field(
      default_factory=uuid.uuid4,
      primary_key=True,
      sa_column_kwargs={"server_default": text("gen_random_uuid()")},
   )
   product_id: uuid.UUID = Field(foreign_key="products.id", unique=True)
   current_quantity: float = Field(default=0.0)
   reserved_quantity: float = Field(default=0.0)
   available_quantity: float = Field(default=0.0)
   last_updated: datetime = Field(default_factory=datetime.utcnow)
   
   # Relationship
   product: Optional["Product"] = Relationship(back_populates="inventory")
   

class StockMovement(SQLModel, table=True):
   __tablename__ = "stock_movements"
   id: uuid.UUID = Field(
      default_factory=uuid.uuid4,
      primary_key=True,
      sa_column_kwargs={"server_default": text("gen_random_uuid()")},
   )
   product_id: uuid.UUID = Field(foreign_key="products.id")
   order_id: uuid.UUID = Field(foreign_key="orders.id")
   movement_type: MovementType = Field(
      default=MovementType.OUT,
      sa_column=Column(
         String(10),
         nullable=False,
         server_default=MovementType.OUT.value,
      )
   )
   quantity: float = Field()
   movement_date: datetime = Field(default_factory=datetime.utcnow)
   observations: Optional[str] = Field(default=None)
   
   # Relationship
   product: Optional["Product"] = Relationship(back_populates="stock_movements")
   order: Optional["Order"] = Relationship(back_populates="stock_movements")