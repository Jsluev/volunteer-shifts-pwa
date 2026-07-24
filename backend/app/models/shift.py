from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, func, CheckConstraint, Index
from app.core.database import Base


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    total_slots = Column(Integer, nullable=False)
    status = Column(Text, nullable=False, default="draft")  # draft, published, closed, cancelled
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint("total_slots > 0", name="ck_shifts_total_slots_positive"),
        Index("idx_shifts_tenant_date", "tenant_id", "start_time", postgresql_where="status = 'published'"),
    )
