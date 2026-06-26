from sqlalchemy import Column, String, Date, Numeric, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from uuid import uuid4


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(64), nullable=False, unique=True)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date)
    pan = Column(String(20))
    aadhaar = Column(String(20))
    salary = Column(Numeric(14, 2))
    address = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
