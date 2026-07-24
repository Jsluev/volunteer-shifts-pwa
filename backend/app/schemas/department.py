from pydantic import BaseModel
from datetime import datetime


class DepartmentCreate(BaseModel):
    name: str


class DepartmentResponse(BaseModel):
    id: int
    tenant_id: int
    name: str

    model_config = {"from_attributes": True}
