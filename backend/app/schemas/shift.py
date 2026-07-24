from pydantic import BaseModel
from datetime import datetime


class ShiftCreate(BaseModel):
    department_id: int
    start_time: datetime
    end_time: datetime
    total_slots: int


class ShiftUpdate(BaseModel):
    department_id: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    total_slots: int | None = None
    status: str | None = None


class ShiftResponse(BaseModel):
    id: int
    tenant_id: int
    department_id: int
    start_time: datetime
    end_time: datetime
    total_slots: int
    status: str
    created_by: int | None
    created_at: datetime
    occupied_slots: int = 0

    model_config = {"from_attributes": True}
