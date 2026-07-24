from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, func, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(Text, nullable=False)
    meta = Column(JSONB, nullable=False, default=dict)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("idx_audit_coord_created", "tenant_id", "user_id", "created_at"),
    )
