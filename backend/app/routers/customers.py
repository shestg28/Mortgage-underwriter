from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services.customer_number_generator import generate_customer_number
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.post("/", response_model=CustomerRead)
def create_customer(customer_in: CustomerCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    customer_number = generate_customer_number(db, customer_in.salary)

    customer = models.Customer(
        customer_id=customer_number,
        full_name=customer_in.full_name,
        date_of_birth=customer_in.date_of_birth,
        pan=customer_in.pan,
        aadhaar=customer_in.aadhaar,
        salary=customer_in.salary,
        address=customer_in.address,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/", response_model=list[CustomerRead])
def list_customers(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    customers = db.query(models.Customer).offset(skip).limit(limit).all()
    return customers


@router.get("/search", response_model=list[CustomerRead])
def search_customers(prefix: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    search_term = f"{prefix}%"
    customers = (
        db.query(models.Customer)
        .filter(func.lower(models.Customer.customer_id).startswith(prefix.lower()))
        .all()
    )
    return customers


@router.get("/lookup/{customer_id}", response_model=CustomerRead)
def lookup_customer(customer_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.put("/lookup/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: str, customer_in: CustomerUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    for field, value in customer_in.dict(exclude_unset=True).items():
        setattr(customer, field, value)

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/lookup/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    db.delete(customer)
    db.commit()
    return None
