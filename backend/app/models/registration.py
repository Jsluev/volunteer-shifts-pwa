from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, func, UniqueConstraint, Index
from app.core.database import Base


class ShiftRegistration(Base):
    __tablename__ = "shift_registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Text, nullable=False, default="pending")  # pending, approved, rejected, cancelled, attendance_confirmed
    moderator_comment = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("shift_id", "user_id", name="uq_shift_registrations_shift_user"),
        Index("idx_reg_shift_status", "shift_id", "status", postgresql_where="status IN ('approved', 'attendance_confirmed')"),
        Index("idx_reg_user_active", "user_id", "status", postgresql_where="status IN ('approved', 'attendance_confirmed', 'pending')"),
    )
