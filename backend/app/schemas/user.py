from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    email: str
    phone: str | None = None
    role: str  # volunteer, coordinator, controller, admin
    full_name: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    tenant_id: int
    email: str
    phone: str | None
    role: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str
