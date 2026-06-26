from sqlalchemy import Column, String, TIMESTAMP, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from uuid import uuid4


class Audit(Base):
    __tablename__ = "audit_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True)
    event_type = Column(String(100), nullable=False)
    actor_id = Column(String(100))
    details = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
