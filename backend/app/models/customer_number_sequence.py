from sqlalchemy import Column, Integer, String
from app.models.base import Base


class CustomerNumberSequence(Base):
    __tablename__ = "customer_number_sequences"

    prefix = Column(String(2), primary_key=True)
    last_sequence = Column(Integer, nullable=False, server_default="0")
