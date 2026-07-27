from datetime import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.modules.user.model import UserProfile


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    cpf: Optional[str] = None
    phone: Optional[str] = None
    profile: UserProfile = UserProfile.OPERATOR
    active: bool = True
    image: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None  # se enviado, re-hashear
    cpf: Optional[str] = None
    phone: Optional[str] = None
    profile: Optional[UserProfile] = None
    active: Optional[bool] = None
    image: Optional[str] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    cpf: Optional[str] = None
    phone: Optional[str] = None
    profile: UserProfile
    active: bool
    email_verified: bool
    image: Optional[str] = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# Login schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
