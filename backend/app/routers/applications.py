from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from uuid import uuid4

from app.db import get_db
from app.utils.deps import get_current_user
from app import models
from app.services.scorer import score_application
from app.services.pdf_processor import extract_text_from_pdf
from app.services.cleaning import clean_text, normalize_fields
from app.services.extraction import extract_fields_from_text
from app.services.verifier import compare_extracted_with_db
from app.services.fraud import detect_fraud_rules
from app.schemas.document import AnalyzeWorkflowResponse

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("/")
def create_application(customer_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    app_rec = models.Application(
        id=uuid4(),
        customer_id=customer.id,
        status="pending",
        created_by=current_user.id,
    )
    db.add(app_rec)
    db.commit()
    db.refresh(app_rec)

    audit = models.Audit(
        id=uuid4(),
        application_id=app_rec.id,
        event_type="application_created",
        actor_id=str(current_user.id),
        details={"customer_id": customer_id},
    )
    db.add(audit)
    db.commit()

    return {"application_id": str(app_rec.id), "status": app_rec.status}


@router.post("/{app_id}/score")
def score_application_endpoint(app_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    app_rec = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    customer = db.query(models.Customer).filter(models.Customer.id == app_rec.customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    flags = db.query(models.FraudFlag).filter(models.FraudFlag.application_id == app_rec.id).all()
    fraud_severity = sum((f.severity or 0) for f in flags)

    match_details = {}
    if flags and flags[0].details:
        match_details = flags[0].details

    customer_dict = {"salary": float(customer.salary) if customer.salary is not None else None, "full_name": customer.full_name}
    scoring = score_application(customer_dict, fraud_severity, match_details)

    risk = scoring["risk_score"]
    if risk < 30:
        decision = "approved"
        status = "approved"
    elif risk < 60:
        decision = "review"
        status = "review"
    else:
        decision = "rejected"
        status = "rejected"

    app_rec.risk_score = risk
    app_rec.decision = decision
    app_rec.decision_reason = str(scoring.get("breakdown"))
    app_rec.status = status
    db.add(app_rec)
    db.commit()

    audit = models.Audit(
        id=uuid4(),
        application_id=app_rec.id,
        event_type="application_scored",
        actor_id=str(current_user.id),
        details={"risk": risk, "decision": decision},
    )
    db.add(audit)
    db.commit()

    return {"application_id": str(app_rec.id), "risk_score": risk, "decision": decision, "breakdown": scoring.get("breakdown")}


@router.post("/{app_id}/analyzeWorkflow", response_model=AnalyzeWorkflowResponse)
async def analyze_workflow(app_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    app_rec = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    customer = db.query(models.Customer).filter(models.Customer.id == app_rec.customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    file_bytes = await file.read()
    pages_text = extract_text_from_pdf(file_bytes)
    raw_pages = [text or "" for text in pages_text]
    cleaned_pages = [clean_text(text) for text in raw_pages if text]
    full_text = "\n".join(cleaned_pages)
    extracted = normalize_fields(extract_fields_from_text(full_text))

    db_record = {"full_name": customer.full_name, "pan": customer.pan or "", "aadhaar": customer.aadhaar or "", "salary": float(customer.salary) if customer.salary is not None else None}
    match, match_details = compare_extracted_with_db(extracted, db_record)

    flags = detect_fraud_rules(match_details, extracted)
    fraud_severity = sum(flag["severity"] for flag in flags)
    customer_dict = {"salary": db_record["salary"], "full_name": db_record["full_name"]}
    scoring = score_application(customer_dict, fraud_severity, match_details)

    risk_score = scoring["risk_score"]
    if risk_score < 30:
        decision = "approved"
        status = "approved"
    elif risk_score < 60:
        decision = "review"
        status = "review"
    else:
        decision = "rejected"
        status = "rejected"

    app_rec.risk_score = risk_score
    app_rec.decision = decision
    app_rec.decision_reason = str(scoring.get("breakdown"))
    app_rec.status = status
    db.add(app_rec)
    db.commit()

    result = {
        "application_id": str(app_rec.id),
        "file_name": file.filename,
        "extracted_fields": extracted,
        "raw_pages": raw_pages,
        "cleaned_pages": cleaned_pages,
        "cleaned_text": full_text,
        "match": match,
        "match_details": match_details,
        "fraud_flags": flags,
        "risk_score": risk_score,
        "decision": decision,
        "breakdown": scoring["breakdown"],
    }

    # persist fraud flags for this application if any
    for f in flags:
        ff = models.FraudFlag(
            id=uuid4(),
            application_id=app_rec.id,
            flag_type=f["flag_type"],
            severity=f["severity"],
            details=f["details"],
        )
        db.add(ff)
    db.commit()

    audit = models.Audit(
        id=uuid4(),
        application_id=app_rec.id,
        event_type="application_analyzed",
        actor_id=str(current_user.id),
        details={"file_name": file.filename, "decision": result["decision"]},
    )
    db.add(audit)
    db.commit()

    return result


@router.get("/{app_id}")
def get_application(app_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    app_rec = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    audits = db.query(models.Audit).filter(models.Audit.application_id == app_rec.id).order_by(models.Audit.created_at).all()
    audit_list = [
        {"event_type": a.event_type, "actor_id": a.actor_id, "details": a.details, "created_at": a.created_at.isoformat()}
        for a in audits
    ]

    return {
        "application_id": str(app_rec.id),
        "status": app_rec.status,
        "risk_score": app_rec.risk_score,
        "decision": app_rec.decision,
        "decision_reason": app_rec.decision_reason,
        "audits": audit_list,
    }
