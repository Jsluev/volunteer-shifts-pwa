from pydantic import BaseModel


class NotificationSettings(BaseModel):
    email_enabled: bool = True
    push_enabled: bool = True
    inapp_enabled: bool = True
    sms_enabled: bool = False
    reminder_2days: bool = True
    reminder_15hours: bool = True
    reminder_1hour: bool = True
    quiet_hours_start: int = 3
    quiet_hours_end: int = 9
