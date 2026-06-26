from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ExtractedFields(BaseModel):
    name: Optional[str] = None
    pan: Optional[str] = None
    aadhaar: Optional[str] = None
    salary: Optional[float] = None
    address: Optional[str] = None


class FraudFlagSchema(BaseModel):
    id: str
    flag_type: str
    severity: int
    details: Dict[str, Any]


class DocumentProcessResponse(BaseModel):
    extracted: ExtractedFields
    matched: bool
    match_details: Dict[str, Any]
    fraud_flags: List[FraudFlagSchema]
    raw_pages: List[str]
    cleaned_pages: List[str]
    cleaned_text: str

    class Config:
        arbitrary_types_allowed = True


class AnalyzeWorkflowResponse(BaseModel):
    application_id: str
    file_name: str
    extracted_fields: ExtractedFields
    raw_pages: List[str]
    cleaned_pages: List[str]
    cleaned_text: str
    match: bool
    match_details: Dict[str, Any]
    fraud_flags: List[FraudFlagSchema]
    risk_score: int
    decision: str
    breakdown: Dict[str, Any]

    class Config:
        arbitrary_types_allowed = True
