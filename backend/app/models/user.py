from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, TIMESTAMP, func, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(Text, nullable=False)
    phone = Column(Text)
    role = Column(Text, nullable=False)  # volunteer, coordinator, controller, admin
    full_name = Column(Text)
    password_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("idx_users_tenant_role", "tenant_id", "role"),
    )
