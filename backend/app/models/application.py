from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    risk_score = Column(Integer)
    decision = Column(String(50))
    decision_reason = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
