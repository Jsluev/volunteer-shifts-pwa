from pydantic import BaseModel
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    channel: str
    subject: str | None
    body: str
    scheduled_at: datetime
    sent_at: datetime | None
    status: str

    model_config = {"from_attributes": True}


class BroadcastCreate(BaseModel):
    message: str
    target: str  # all, department
    department_id: int | None = None
    priority: str = "normal"  # normal, high
