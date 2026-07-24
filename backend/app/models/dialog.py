from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from app.core.database import Base


class Dialog(Base):
    __tablename__ = "dialogs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    type = Column(Text, nullable=False)  # personal, group
    participant_ids = Column(PG_ARRAY(Integer))
    created_at = Column(TIMESTAMP, server_default=func.now())
