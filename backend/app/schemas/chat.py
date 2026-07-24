from pydantic import BaseModel
from datetime import datetime


class MessageCreate(BaseModel):
    dialog_id: int
    text: str


class MessageResponse(BaseModel):
    id: int
    dialog_id: int
    sender_id: int
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DialogCreate(BaseModel):
    type: str  # personal, group
    participant_ids: list[int]


class DialogResponse(BaseModel):
    id: int
    tenant_id: int
    type: str
    participant_ids: list[int] | None

    model_config = {"from_attributes": True}
