from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, func, Index
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Text, nullable=False)
    channel = Column(Text, nullable=False)  # email, push, inapp, sms
    subject = Column(Text)
    body = Column(Text, nullable=False)
    scheduled_at = Column(TIMESTAMP, nullable=False)
    sent_at = Column(TIMESTAMP)
    status = Column(Text, nullable=False, default="pending")  # pending, sent, failed
    retry_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("idx_notif_scheduled", "scheduled_at", postgresql_where="status = 'pending'"),
    )
