from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="loan_officer")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
