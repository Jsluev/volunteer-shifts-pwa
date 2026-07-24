from sqlalchemy import Column, Integer, Text, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    slug = Column(Text, unique=True, nullable=False)
    timezone = Column(Text, default="Europe/Moscow")
    settings = Column(JSONB, nullable=False, default=dict)
    created_at = Column(TIMESTAMP, server_default=func.now())
