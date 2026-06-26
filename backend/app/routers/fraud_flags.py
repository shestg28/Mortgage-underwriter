from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.utils.deps import get_current_user
from app import models

router = APIRouter(prefix="/api/fraud/flags", tags=["fraud"])


@router.get("/")
def list_fraud_flags(application_id: str | None = None, customer_id: str | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(models.FraudFlag)
    if application_id:
        query = query.filter(models.FraudFlag.application_id == application_id)
    if customer_id:
        query = query.join(models.Application, models.FraudFlag.application_id == models.Application.id).filter(models.Application.customer_id == customer_id)

    flags = query.all()
    return [
        {
            "id": str(flag.id),
            "application_id": str(flag.application_id),
            "flag_type": flag.flag_type,
            "severity": flag.severity,
            "details": flag.details,
            "created_at": flag.created_at.isoformat(),
        }
        for flag in flags
    ]


@router.get("/{flag_id}")
def get_fraud_flag(flag_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    flag = db.query(models.FraudFlag).filter(models.FraudFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fraud flag not found")
    return {
        "id": str(flag.id),
        "application_id": str(flag.application_id),
        "flag_type": flag.flag_type,
        "severity": flag.severity,
        "details": flag.details,
        "created_at": flag.created_at.isoformat(),
    }
