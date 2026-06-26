from sqlalchemy import Column, String, Integer, JSON, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class FraudFlag(Base):
    __tablename__ = "fraud_flags"

    id = Column(UUID(as_uuid=True), primary_key=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    flag_type = Column(String(100), nullable=False)
    severity = Column(Integer, nullable=False)
    details = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
