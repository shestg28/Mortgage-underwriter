import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.utils.deps import get_current_user
from app.db import get_db
from app.services.pdf_processor import extract_text_from_pdf
from app.services.ocr_service import ocr_image_bytes
from app.services.cleaning import clean_text
from app.services.extraction import extract_fields_from_text
from app.services.verifier import compare_extracted_with_db
from app.services.fraud import detect_fraud_rules
from app import models
from uuid import uuid4
from app.schemas.document import DocumentProcessResponse

STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "uploads"
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
def upload_document(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF uploads are allowed")

    file_id = uuid.uuid4().hex
    extension = Path(file.filename).suffix or ".pdf"
    destination = STORAGE_ROOT / f"{file_id}{extension}"

    with destination.open("wb") as buffer:
        buffer.write(file.file.read())

    return {
        "file_id": file_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "path": str(destination),
    }



@router.post("/process", response_model=DocumentProcessResponse)
def process_document(file_id: str, customer_id: str | None = None, application_id: str | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # locate file
    candidate = next(STORAGE_ROOT.glob(f"{file_id}*"), None)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # extract text/pages by converting the PDF to PNGs first
    pages = extract_text_from_pdf(str(candidate))

    raw_pages = [text or "" for text in pages]
    cleaned_pages = [clean_text(text) for text in raw_pages if text]

    full_text = "\n".join([p for p in cleaned_pages if p])
    extracted = extract_fields_from_text(full_text)

    # attempt to find DB record
    db_record = None
    if customer_id:
        db_record = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    # fallback: search by PAN or Aadhaar
    if not db_record and extracted.get("pan"):
        db_record = db.query(models.Customer).filter(models.Customer.pan == extracted.get("pan")).first()
    if not db_record and extracted.get("aadhaar"):
        db_record = db.query(models.Customer).filter(models.Customer.aadhaar == extracted.get("aadhaar")).first()

    result = {
        "extracted": extracted,
        "matched": False,
        "match_details": None,
        "fraud_flags": [],
        "raw_pages": raw_pages,
        "cleaned_pages": cleaned_pages,
        "cleaned_text": full_text,
    }

    # always flag missing required fields even without a matching DB record
    missing_flags = detect_fraud_rules({}, extracted)
    result["fraud_flags"] = missing_flags

    if db_record:
        # build lightweight db dict
        db_dict = {"full_name": db_record.full_name, "pan": db_record.pan or "", "aadhaar": db_record.aadhaar or "", "salary": float(db_record.salary) if db_record.salary is not None else None}
        match, details = compare_extracted_with_db(extracted, db_dict)
        result["matched"] = match
        result["match_details"] = details

        # append additional fraud flags from DB comparison
        flags = detect_fraud_rules(details, extracted)
        result["fraud_flags"].extend(flags)

        # persist flags to DB only when application_id is provided (application_id is required by model)
        if application_id:
            for f in flags:
                ff = models.FraudFlag(
                    id=uuid4(),
                    application_id=application_id,
                    flag_type=f["flag_type"],
                    severity=f["severity"],
                    details=f["details"],
                )
                db.add(ff)
            db.commit()

    return result
