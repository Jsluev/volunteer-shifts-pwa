from pydantic import BaseModel, EmailStr
from datetime import datetime


class TenantCreate(BaseModel):
    name: str
    slug: str
    timezone: str = "Europe/Moscow"


class TenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    timezone: str
    settings: dict

    model_config = {"from_attributes": True}
