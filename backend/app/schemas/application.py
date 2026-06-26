from pydantic import BaseModel
from typing import Optional


class ApplicationCreate(BaseModel):
    customer_id: str
    created_by: Optional[int]


class ApplicationRead(BaseModel):
    id: str
    customer_id: str
    status: str
    risk_score: Optional[int]
    decision: Optional[str]
    decision_reason: Optional[str]
    created_by: Optional[int]

    class Config:
        orm_mode = True
