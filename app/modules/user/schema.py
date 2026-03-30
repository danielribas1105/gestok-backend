import uuid

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# Data to create a user (input)
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    image: Optional[str] = None
    profile: Optional[str] = "user"
    active: bool


class UserUpdate(BaseModel):
    name: Optional[str] = None
    image: Optional[str] = None
    profile: Optional[str] = None
    active: Optional[bool] = None


# Data returned to the client (output — never exposes the password)
class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    emailVerified: bool
    image: Optional[str]
    createdAt: datetime
    profile: str
    active: bool

    class Config:
        from_attributes = True  # Permite converter model SQLAlchemy → Pydantic


# Login schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
