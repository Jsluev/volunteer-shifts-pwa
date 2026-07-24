from pydantic import BaseModel
from datetime import datetime


class RegistrationCreate(BaseModel):
    shift_id: int


class RegistrationUpdate(BaseModel):
    status: str  # approved, rejected, cancelled
    moderator_comment: str | None = None


class RegistrationResponse(BaseModel):
    id: int
    shift_id: int
    user_id: int
    status: str
    moderator_comment: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BulkApprove(BaseModel):
    registration_ids: list[int]
    approve: bool
