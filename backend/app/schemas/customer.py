from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID


class CustomerCreate(BaseModel):
    customer_id: str
    full_name: str
    date_of_birth: Optional[date] = None
    pan: Optional[str] = None
    aadhaar: Optional[str] = None
    salary: Optional[float] = None
    address: Optional[str] = None


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    pan: Optional[str] = None
    aadhaar: Optional[str] = None
    salary: Optional[float] = None
    address: Optional[str] = None


class CustomerRead(CustomerCreate):
    id: UUID

    class Config:
        from_attributes = True
